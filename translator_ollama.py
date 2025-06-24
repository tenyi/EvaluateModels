import argparse
import sys
import requests
import re
from opencc import OpenCC


def translate_subtitle_file(input_file, output_file) -> None:
    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read()
    isWebVtt = False
    if content.startswith("WEBVTT"):
        isWebVtt = True
    # Split the content into subtitle blocks
    blocks = re.split(r"\n\s*\n", content.strip())

    merged_blocks = []
    for block in blocks:
        lines = block.split("\n")
        length = len(lines)
        if length >= 2:
            minus_one = length - 1
            # Keep the subtitle number and timestamp
            merged_block = lines[:minus_one]
            # Merge the text lines
            merged_text = " ".join(lines[minus_one:])
            # 翻譯
            translated_text = translate_text_ollama(merged_text, "zh-TW")
            merged_text = f"{merged_text}\n{translated_text}"
            merged_block.append(merged_text)
            merged_blocks.append("\n".join(merged_block))

    # Join the merged blocks with double newlines
    output_content = "\n\n".join(merged_blocks)

    if isWebVtt:
        output = f"WEBVTT\n\n{output_content}"
    else:
        output = output_content
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(output)


def summary_text_ollama(text, url="http://localhost:11434/api/chat", model="gemma3:27b") -> str:
    """
    總結會議摘要
    """

    headers = {"Content-Type": "application/json"}
    data = {
        "model": model,  # 您可能需要指定適合的模型名稱
        "messages": [
            {
                "role": "system",
                "content": """
1.  **摘要內容要求**：
    *   **主要議題**：識別並概述討論的核心主題。
    *   **關鍵成果**：重點描述重要的決定、達成的共識或結論。
    *   **行動項目**：列出具體的行動計劃及後續步驟；若有提及，須指明負責人或團隊。

2.  **語言與格式**：
    *   **僅限繁體中文**：所有輸出內容必須使用繁體中文。
    *   **保留英文術語**：若原文中包含英文專業術語，請在摘要中保留其英文原文。
    *   **專業簡潔**：使用精確、直接的語言，避免不必要的細節，確保摘要易於理解。

3.  **嚴格排除的內容**：
    *   **禁止任何引言、客套話、結論性陳述** (例如：「本次會議摘要如下」、「會議圓滿結束」、「以上是重點整理」等)。
    *   **禁止提及「摘要」、「紀錄」等詞語本身**。
    *   **禁止任何形式的自我評論、解釋或補充說明**。你的回應**只能是摘要本身**，不應包含摘要以外的任何文字。

4.  **特殊情況處理**：
    *   如果提供的文本資訊量過少，或內容零散難以歸納出有意義的摘要，請直接回答：「無法得出摘要」。請僅在確實無法摘要時使用此回覆。

5.  **最終輸出指示**：
    *   產生的摘要必須**條理分明、切中要點**，不含任何冗餘詞彙。
    *   請務必以 `zh-TW` (繁體中文) 回覆。
"""
            },
            {
                "role": "user",
                "content": text,
            },
        ],
        "stream": False
    }
    # 發送 POST 請求以獲取總結
    response = requests.post(url, headers=headers, json=data)
    # 輸出生成的結果
    json_data = response.json()
    # 輸出生成的結果
    summary = json_data["message"]["content"].strip()
    summary = re.sub(r'<think>.*?</think>', '', summary, flags=re.DOTALL)
    cc = OpenCC("s2twp")  # 翻成台灣繁體中文，避免大語言模型誤寫簡體中文
    summary = cc.convert(summary)
    return summary


def correct_words_ollama(text, url="http://localhost:11434/api/chat", model="gemma3:27b") -> str:
    """
    修正錯字
    """
    headers = {"Content-Type": "application/json"}
    data = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": 
 """
# 角色
你是一位細心的文字校正專家。

# 任務
你的任務是校正由 Whisper 產生的逐字稿中的錯字與同音異字。你必須只回傳校正後的文字。

# 規則
嚴格遵守原始格式（包含換行、空格、標點符號）。只將錯誤的字元替換為正確的字元，絕對不要新增、刪除或改寫任何內容。
 """,
            },
            {
                "role": "user",
                "content": text,
            }
        ],
        "stream": False
    }
    response = requests.post(url, headers=headers, json=data)
    json_data = response.json()
    correct_text = json_data["message"]["content"].strip()
    return correct_text


def correct_words_ollama_fail(text, url="http://localhost:11434/api/chat", model="gemma3:27b") -> str:
    """
    修正錯字
    """
    headers = {"Content-Type": "application/json"}
    data = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": 
 """
You are an AI proofreading engine specialized in correcting Whisper ASR transcripts.

Your single function is to identify and correct typos and homophone errors.

Follow these rules STRICTLY:
1.  **INPUT**: The user will provide a raw text transcript.
2.  **PROCESSING**:
    - Identify and correct all spelling mistakes and homophone errors (e.g., "的" vs. "得", "在" vs. "再").
    - PRESERVE the original document structure: All line breaks, spacing, and punctuation must remain identical.
    - DO NOT add any new words or sentences.
    - DO NOT remove any existing words or sentences.
    - DO NOT rephrase or paraphrase the content. Your only allowed action is character replacement for corrections.
3.  **OUTPUT**:
    - Return ONLY the corrected text.
    - DO NOT include any explanations, apologies, or introductory phrases like "這是校正後的文字：".

 """,
            },
            {
                "role": "user",
                "content": text,
            }
        ],
        "stream": False
    }
    response = requests.post(url, headers=headers, json=data)
    json_data = response.json()
    correct_text = json_data["message"]["content"].strip()
    return correct_text


def translate_text_ollama(text, target_language="zh-TW", model="gemma3:12b") -> str:
    url = "http://localhost:11434/api/chat"
    # url = "http://10.10.10.201:11434/api/chat"
    headers = {"Content-Type": "application/json"}
    data = {
        "model": model,  # 您可能需要指定適合的模型名稱
        "messages": [
            {
                "role": "system",
                "content": f"You are a highly disciplined translation model that strictly follows instructions. You are a highly skilled AI translator specializing in translating meeting records into {target_language}. Translate **only** the user's provided meeting notes according to the following strict guidelines:\n\n1. **Do NOT add any explanation, commentary, or extra content**.  \n   - Your task is strictly translation. Do not include summaries, comments, greetings, or interpretations.  \n   - If you add anything beyond the translation, it will be considered a mistake.\n\n2. **Preserve Professional Terminology in English**:  \n   - If the meeting notes contain technical terms, brand names, product names, or specialized industry jargon, retain them in their original English form.  \n   - Common English words that are part of professional terminology (e.g., 'AI model', 'Deep Learning', 'OpenAI API') should **not be translated** into Chinese.  \n\n3. **Ensure Natural and Fluent Translation**:  \n   - Use clear, professional, and natural formal Traditional Chinese.  \n   - Avoid overly literal translations that sound unnatural.  \n\n4. **Maintain Logical Flow and Readability**:  \n   - Adjust sentence structure to fit Chinese language conventions while preserving the original meaning.  \n\n5. **Keep Formatting and Structure Consistent**:  \n   - Retain original formatting: bullet points, lists, section headings, etc.  \n   - Smoothly integrate terms into the {target_language} context.  \n\n6. **Language Requirement**:  \n   - Entire output must be in {target_language}, except for English professional terminology.  \n\n7. 若文字太過簡短，直接 Translate into {target_language}.\n\nNo preambles. No commentary. If you include anything other than the direct translation, it will be considered an error.",
            },
            {
                "role": "user",
                "content": text,
            },
        ],
        "stream": False
    }
    # 發送 POST 請求以獲取翻譯
    response = requests.post(url, headers=headers, json=data)
    # 輸出生成的結果
    json_data = response.json()
    # 輸出生成的結果
    translate_text = json_data["message"]["content"].strip()
    # for punct in ["。", "！", "？"]:
    #     translate_text = translate_text.replace(f"{punct}", f"{punct}\n")

    if target_language == "zh-TW":
        cc = OpenCC("s2twp")  # 翻成台灣繁體中文，避免大語言模型誤寫簡體中文
        translate_text = cc.convert(translate_text)
        # 常用語彙轉換，目前先不使用，大部分在 OpenCC 已經有包含
        # output_content = (
        #     output_content.replace("黑客", "駭客")
        #     .replace("數據庫", "資料庫")
        #     .replace("計算機", "電腦")
        #     .replace("在線", "線上")
        #     .replace("社會工程", "社交工程")
        #     .replace("網絡", "網路")
        #     .replace("軟件", "軟體")
        #     .replace("資料包", "封包")
        #     .replace("證券分析師", "安全分析師")
        # )

    return translate_text


# 定義顯示使用說明的函式
def usage(script_name: str) -> None:
    print(f"Usage: python {script_name} <input_file> <output_file>")  # 印出使用語法
    print(f"Example: python {script_name} input.srt output.srt")  # 印出使用範例


def main():
    parser = argparse.ArgumentParser(
        description="將指定字幕檔翻譯成繁體中文，並將結果寫入新的檔案。"
    )
    parser.add_argument(
        "input_file",
        help="input file",
    )
    parser.add_argument(
        "output_file",
        nargs="?",
        default="output.srt",
        help="output file (default: output.srt)",
    )
    if len(sys.argv) > 1:
        args = parser.parse_args()
        translate_subtitle_file(args.input_file, args.output_file)
    else:
        usage(sys.argv[0])


if __name__ == "__main__":
    main()
