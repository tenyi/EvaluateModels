#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主程式：Ollama 模型評比工具

本程式會自動化執行一系列針對本機 Ollama 模型的評比任務，
包括翻譯和摘要。它會使用設定好的雲端大型語言模型（如 GPT-4、Gemini）
作為評審，對各個 Ollama 模型的表現進行評分，並最終生成包含
表格、統計分析與視覺化圖表的 Markdown 和 HTML 報表。

主要流程：
1. 讀取設定檔 `config.py` 中的模型清單與 API 金鑰。
2. 讀取 `input.txt` 作為所有任務的輸入文本。
3. 依序呼叫 `OLLAMA_MODELS_TO_COMPARE` 中的每個模型，執行 `SUPPORTED_TASKS` 中定義的任務。
4. 將每個模型的輸出結果，交由 `REVIEWER_MODELS` 中定義的評審模型進行評分。
5. 彙總所有評分與結果，生成 Markdown 格式的報表。
6. 將 Markdown 報表轉換為 HTML 格式，方便瀏覽。
7. 所有 API 呼叫結果都會被快取，避免重複執行浪費時間與資源。
"""

import re
import sys
import time
from openai import OpenAI
import requests
from typing import Tuple
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np

# 從設定檔導入所有必要的參數
from config import (
    OLLAMA_API_BASE_URL,
    OLLAMA_MODELS_TO_COMPARE,
    OPENAI_API_KEY,
    GOOGLE_API_KEY,
    OPENROUTER_API_KEY,
    REPLICATE_API_KEY,
    REVIEWER_MODELS,
    REVIEWER_TEMPERATURE,
    SUPPORTED_TASKS,
)
# 從工具模組導入 HTML 轉換器與快取工具
from markdown2html import convert_markdown_to_html
from cache_utils import get_cache_key, load_from_cache, save_to_cache

# --- 全域設定 ---
# 設定 Matplotlib 使用的字體，以確保圖表中的中文能正常顯示。
# Arial Unicode MS 和 SimHei 是常用的中文字體。
plt.rcParams["font.sans-serif"] = ["Arial Unicode MS", "SimHei", "DejaVu Sans"]
# 解決 Matplotlib 圖表中的負號顯示問題。
plt.rcParams["axes.unicode_minus"] = False


class ModelEvaluator:
    """
    模型評比器類別，封裝了所有評比相關的邏輯。

    這個類別負責管理整個評比流程，從讀取輸入、呼叫模型、
    進行評審，到最終生成報表。
    """

    def __init__(self):
        """
        初始化評比器。

        - `self.results`: 一個字典，用來儲存每個 Ollama 模型在各項任務的原始輸出結果。
                          結構：{ "模型名稱": { "任務名稱": "輸出文字" } }
        - `self.evaluation_scores`: 一個字典，用來儲存每個評審模型對 Ollama 模型輸出結果的評分。
                                     結構：{ "評審者ID": { "模型名稱": { "任務名稱": { "score": 分數, "comment": "評語" } } } }
        """
        self.results = {}
        self.evaluation_scores = {}

    def read_input_text(self, file_path: str = "input.txt") -> str:
        """
        讀取指定的測試樣本文件。

        Args:
            file_path (str): 輸入文件的路徑，預設為 "input.txt"。

        Returns:
            str: 文件的完整內容。

        Raises:
            SystemExit: 如果文件找不到或讀取時發生錯誤，則會印出錯誤訊息並終止程式。
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            print(f"❌ 找不到輸入檔案: {file_path}")
            sys.exit(1)  # 終止程式
        except Exception as e:
            print(f"❌ 讀取檔案時發生錯誤: {e}")
            sys.exit(1)  # 終止程式

    def call_ollama_api(self, model: str, task: str, text: str) -> str:
        """
        呼叫本機的 Ollama API 來執行指定任務。

        在呼叫前會先檢查快取，如果快取中已有相同請求的結果，則直接返回快取結果。
        否則，會向 Ollama 發送請求，並將新結果存入快取。

        Args:
            model (str): 要使用的 Ollama 模型名稱。
            task (str): 要執行的任務名稱（例如 "translate" 或 "summarize"）。
            text (str): 輸入給模型的文字。

        Returns:
            str: 模型生成的文字結果。如果發生錯誤，則返回以 "ERROR:" 開頭的錯誤訊息。
        """
        # 建立快取參數字典與快取鍵
        # 從設定檔中取得該任務對應的系統提示詞
        prompt: str = SUPPORTED_TASKS[task]

        # 建立快取參數字典與快取鍵
        cache_params = {
            "provider": "ollama",
            "model": model,
            "task": task,
            "text": text,
        }
        cache_key = get_cache_key(cache_params, prompt=prompt)
        # 嘗試從快取載入
        cached_response = load_from_cache(cache_key)
        if cached_response:
            print(f"  ✅ {model} ({task}) 從快取載入")
            return cached_response

        # 設定 API 端點與標頭
        url: np.LiteralString = f"{OLLAMA_API_BASE_URL}/api/chat"
        headers: dict[str, str] = {"Content-Type": "application/json"}

        # 從設定檔中取得該任務對應的系統提示詞
        prompt: str = SUPPORTED_TASKS[task]

        # 準備請求的資料結構
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": text},
            ],
            "stream": False,  # 關閉串流輸出，一次性取得完整結果
        }

        try:
            print(f"  🔄 正在呼叫 {model} 執行 {task} 任務...")
            # 發送 POST 請求，設定較長的超時時間（500秒），因為本機模型可能需要較長時間回應
            response: requests.Response = requests.post(
                url, headers=headers, json=data, timeout=500
            )
            response.raise_for_status()  # 如果 HTTP 狀態碼是 4xx 或 5xx，則拋出異常

            # 解析 JSON 回應
            result = response.json()
            output_text: str = result["message"]["content"].strip()
            # 移除模型回應中可能包含的 <think>...</think> 標籤（某些模型會用來表示思考過程）
            output_text: str = re.sub(
                r"<think>.*?</think>", "", output_text, flags=re.DOTALL
            )
            # 將成功取得的結果存入快取
            save_to_cache(cache_key, output_text)
            return output_text

        except requests.exceptions.Timeout:
            print(f"  ⚠️  {model} 回應超時")
            return "ERROR: 回應超時"
        except requests.exceptions.RequestException as e:
            print(f"  ❌ {model} API 呼叫失敗: {e}")
            return f"ERROR: API 呼叫失敗 - {e}"
        except Exception as e:
            print(f"  ❌ {model} 處理回應時發生錯誤: {e}")
            return f"ERROR: 處理回應失敗 - {e}"

    def call_openai_api(
        self,
        model: str,
        system_prompt: str,
        user_content: str,
        is_reviewer: bool = False,
    ) -> str:
        """
        呼叫 OpenAI API。

        同樣支援快取機制。會根據模型名稱從設定檔中取得對應的 `temperature` 參數。

        Args:
            model (str): 要使用的 OpenAI 模型名稱 (e.g., "gpt-4.1-mini")。
            system_prompt (str): 系統提示詞。
            user_content (str): 使用者輸入的內容。
            is_reviewer (bool): 標記此呼叫是否為評審用途，主要用於快取鍵的區分。

        Returns:
            str: 模型生成的文字結果或錯誤訊息。
        """
        # 檢查快取
        full_prompt = f"{system_prompt}\n\n{user_content}"
        cache_params = {
            "provider": "openai",
            "model": model,
            "is_reviewer": is_reviewer,
        }
        cache_key = get_cache_key(cache_params, prompt=full_prompt)
        cached_response = load_from_cache(cache_key)
        if cached_response:
            print(f"  ✅ OpenAI ({model}) 從快取載入")
            return cached_response

        # 檢查 API 金鑰是否已設定
        if not OPENAI_API_KEY or OPENAI_API_KEY == "your_openai_api_key_here":
            return "ERROR: OpenAI API 金鑰未設定"

        try:
            print(f"  🔄 正在呼叫 OpenAI API ({model})...")

            # 從設定檔中取得該評審模型的 temperature
            temperature = REVIEWER_TEMPERATURE.get(model, 0.1)

            # 建立請求參數字典
            request_params = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                "timeout": 60,  # 設定 60 秒超時
            }

            # 某些模型（如 gpt-4o-mini）不支援 temperature=1，所以只有在不為 None 或 1 時才加入此參數
            if temperature is not None and temperature != 1:
                request_params["temperature"] = temperature

            # 使用官方 openai library 來發送請求
            with OpenAI(api_key=OPENAI_API_KEY) as client:
                response = client.chat.completions.create(**request_params)
                output_text = response.choices[0].message.content.strip()
                # 存入快取
                save_to_cache(cache_key, output_text)
                return output_text

        except Exception as e:
            print(f"  ❌ OpenAI API 處理時發生錯誤: {e}")
            return f"ERROR: OpenAI API 處理失敗 - {e}"

    def call_google_api(
        self,
        model: str,
        system_prompt: str,
        user_content: str,
        is_reviewer: bool = False,
    ) -> str:
        """
        呼叫 Google Gemini API。

        Args:
            model (str): 要使用的 Google 模型名稱 (e.g., "gemini-1.5-flash")。
            system_prompt (str): 系統提示詞。
            user_content (str): 使用者輸入的內容。
            is_reviewer (bool): 標記此呼叫是否為評審用途。

        Returns:
            str: 模型生成的文字結果或錯誤訊息。
        """
        # 檢查快取
        full_prompt = f"{system_prompt}\n\n{user_content}"
        cache_params = {
            "provider": "google",
            "model": model,
            "is_reviewer": is_reviewer,
        }
        cache_key = get_cache_key(cache_params, prompt=full_prompt)
        cached_response = load_from_cache(cache_key)
        if cached_response:
            print(f"  ✅ Google ({model}) 從快取載入")
            return cached_response

        # 檢查 API 金鑰
        if not GOOGLE_API_KEY or GOOGLE_API_KEY == "your_google_api_key_here":
            return "ERROR: Google API 金鑰未設定"

        # 組合 API URL
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GOOGLE_API_KEY}"
        headers = {"Content-Type": "application/json"}

        # 取得 temperature 設定
        temperature = REVIEWER_TEMPERATURE.get(model, 0.1)

        # Gemini API 的資料格式與 OpenAI 不同，需要將系統和使用者提示詞合併
        data = {
            "contents": [{"parts": [{"text": f"{system_prompt}\n\n{user_content}"}]}]
        }

        # 同樣，只有在需要時才加入 temperature 參數
        if temperature is not None and temperature != 1:
            data["generationConfig"] = {"temperature": temperature}

        try:
            print(f"  🔄 正在呼叫 Google API ({model})...")
            response = requests.post(url, headers=headers, json=data, timeout=60)
            response.raise_for_status()

            result = response.json()
            # 解析 Gemini 回應的特定結構
            output_text = result["candidates"][0]["content"]["parts"][0]["text"].strip()
            save_to_cache(cache_key, output_text)
            return output_text

        except Exception as e:
            print(f"  ❌ Google API 呼叫失敗: {e}")
            return f"ERROR: Google API 失敗 - {e}"

    def call_openrouter_api(
        self,
        model: str,
        system_prompt: str,
        user_content: str,
        is_reviewer: bool = False,
    ) -> str:
        """
        呼叫 OpenRouter API。

        OpenRouter 是一個模型路由服務，可以用相同的 API 格式呼叫不同供應商的模型。

        Args:
            model (str): 要使用的 OpenRouter 模型識別碼 (e.g., "mistralai/mistral-7b-instruct")。
            system_prompt (str): 系統提示詞。
            user_content (str): 使用者輸入的內容。
            is_reviewer (bool): 標記此呼叫是否為評審用途。

        Returns:
            str: 模型生成的文字結果或錯誤訊息。
        """
        # 檢查快取
        full_prompt = f"{system_prompt}\n\n{user_content}"
        cache_params = {
            "provider": "openrouter",
            "model": model,
            "is_reviewer": is_reviewer,
        }
        cache_key = get_cache_key(cache_params, prompt=full_prompt)
        cached_response = load_from_cache(cache_key)
        if cached_response:
            print(f"  ✅ OpenRouter ({model}) 從快取載入")
            return cached_response

        # 檢查 API 金鑰
        if (
            not OPENROUTER_API_KEY
            or OPENROUTER_API_KEY == "your_openrouter_api_key_here"
        ):
            return "ERROR: OpenRouter API 金鑰未設定"

        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "http://localhost",  # 建議性標頭，用於分析
            "X-Title": "Ollama Model Evaluator",  # 建議性標頭，用於分析
        }

        # 取得 temperature 設定
        temperature = REVIEWER_TEMPERATURE.get(model, 0.1)

        # OpenRouter 的 API 格式與 OpenAI 相容
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        }

        if temperature is not None and temperature != 1:
            data["temperature"] = temperature

        try:
            print(f"  🔄 正在呼叫 OpenRouter API ({model})...")
            response = requests.post(url, headers=headers, json=data, timeout=60)
            response.raise_for_status()

            result = response.json()
            output_text = result["choices"][0]["message"]["content"].strip()
            save_to_cache(cache_key, output_text)
            return output_text
        except Exception as e:
            print(f"  ❌ OpenRouter API 呼叫失敗: {e}")
            return f"ERROR: OpenRouter API 失敗 - {e}"

    def call_replicate_api(
        self,
        model_version: str,
        system_prompt: str,
        user_content: str,
        is_reviewer: bool = False,
    ) -> str:
        """
        呼叫 Replicate API。

        Replicate 的 API 是非同步的。需要先發送一個請求來啟動預測，
        然後輪詢另一個端點來獲取結果。

        Args:
            model_version (str): Replicate 模型的版本識別碼 (格式通常是 "owner/model_name:version_hash")。
            system_prompt (str): 系統提示詞。
            user_content (str): 使用者輸入的內容。
            is_reviewer (bool): 標記此呼叫是否為評審用途。

        Returns:
            str: 模型生成的文字結果或錯誤訊息。
        """
        # 檢查快取
        full_prompt = f"{system_prompt}\n\nUser: {user_content}\nAssistant:"
        cache_params = {
            "provider": "replicate",
            "model_version": model_version,
            "is_reviewer": is_reviewer,
        }
        cache_key = get_cache_key(cache_params, prompt=full_prompt)
        cached_response = load_from_cache(cache_key)
        if cached_response:
            print(f"  ✅ Replicate ({model_version}) 從快取載入")
            return cached_response

        # 檢查 API 金鑰
        if not REPLICATE_API_KEY or REPLICATE_API_KEY == "your_replicate_api_key_here":
            return "ERROR: Replicate API 金鑰未設定"

        url = "https://api.replicate.com/v1/predictions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {REPLICATE_API_KEY}",
        }

        # 根據常見的 Replicate 模型格式建構輸入。
        # 對於類聊天模型，通常需要將系統和使用者提示詞組合起來。
        full_prompt = f"{system_prompt}\n\nUser: {user_content}\nAssistant:"

        # 取得 temperature 設定
        temperature = REVIEWER_TEMPERATURE.get(model_version, 0.1)

        # 準備輸入資料，這部分可能需要根據具體模型進行調整
        input_data = {
            "prompt": full_prompt,
            "system_prompt": system_prompt,
            "max_new_tokens": 1024,  # 範例參數，可調整
        }

        if temperature is not None and temperature != 1:
            input_data["temperature"] = temperature

        # 準備完整的請求資料，需要提供模型的版本 hash
        data = {
            "version": model_version.split(":")[-1]
            if ":" in model_version
            else model_version,
            "input": input_data,
        }

        try:
            print(f"  🔄 正在呼叫 Replicate API ({model_version})...")
            # 步驟 1: 發送請求以啟動預測
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            prediction_start_result = response.json()

            prediction_id = prediction_start_result.get("id")
            if not prediction_id:
                return f"ERROR: Replicate API 未返回有效的 prediction ID - {prediction_start_result.get('detail', '無詳細錯誤')}"

            # 步驟 2: 輪詢 API 以獲取結果
            prediction_url: str = f"https://api.replicate.com/v1/predictions/{prediction_id}"
            max_retries = 20  # 最多重試 20 次 (約 100 秒)
            retry_interval = 5  # 每次重試間隔 5 秒

            for _ in range(max_retries):
                time.sleep(retry_interval)
                poll_response = requests.get(
                    prediction_url, headers=headers, timeout=30
                )
                poll_response.raise_for_status()
                poll_result = poll_response.json()

                status = poll_result.get("status")
                if status == "succeeded":
                    # 處理成功的回應。輸出格式可能是一個字串列表或單一字串。
                    output = poll_result.get("output")
                    if isinstance(output, list):
                        output_text = "".join(output).strip()
                    elif isinstance(output, str):
                        output_text = output.strip()
                    else:
                        return (
                            f"ERROR: Replicate API 返回了未知的輸出格式: {type(output)}"
                        )

                    save_to_cache(cache_key, output_text)
                    return output_text
                elif status == "failed" or status == "canceled":
                    error_detail = poll_result.get("error", "未知錯誤")
                    return f"ERROR: Replicate 預測失敗或取消 - {error_detail}"
                # 如果狀態是 "starting" 或 "processing"，則繼續輪詢

            return f"ERROR: Replicate 預測超時 ({model_version})"

        except requests.exceptions.RequestException as e:
            print(f"  ❌ Replicate API 呼叫失敗: {e}")
            return f"ERROR: Replicate API 請求失敗 - {e}"
        except Exception as e:
            print(f"  ❌ Replicate API 處理時發生錯誤: {e}")
            return f"ERROR: Replicate API 錯誤 - {e}"

    def evaluate_with_reviewer(
        self,
        reviewer_type: str,
        reviewer_model: str,
        task: str,
        original_text: str,
        model_output: str,
    ) -> Tuple[int, str]:
        """
        使用指定的評審模型對 Ollama 模型的輸出進行評分。

        它會根據任務類型（翻譯或摘要）選擇對應的評分標準（系統提示詞），
        然後呼叫相應的雲端 API 進行評審，最後解析評審模型的回應以提取分數和評語。

        Args:
            reviewer_type (str): 評審模型的供應商 (e.g., "openai", "gemini")。
            reviewer_model (str): 評審模型的具體名稱。
            task (str): 被評分的任務名稱。
            original_text (str): 原始輸入文本。
            model_output (str): Ollama 模型的輸出結果。

        Returns:
            Tuple[int, str]: 一個包含 (分數, 評語) 的元組。
                             如果解析失敗，分數會設為 1，評語會是錯誤訊息。
        """

        # 根據任務類型選擇不同的系統提示詞和評分標準
        if task == "translate":
            system_prompt = """你是專業的翻譯評審專家。請根據以下標準對翻譯結果評分（1-10分）：
評分標準：
- 通順性（1-3分）：翻譯是否自然流暢，符合中文表達習慣
- 準確性（1-3分）：是否有翻譯錯誤、遺漏或誤解
- 遵循指令(1-2分)：是否完全遵循指令，以繁體中文回覆
- 專業術語處理（1-2分）：英文專業術語是否適當保留


請以以下格式回覆：
分數: [1-10的整數]
評語: [簡短評語，說明評分理由]"""

            user_content = f"""原文：
{original_text}

翻譯結果：
{model_output}

請評分並給出評語。"""

        elif task == "summarize":
            system_prompt = """你是專業的摘要評審專家。請根據以下標準對摘要結果評分（1-10分）：

評分標準：
- 重點涵蓋（1-3分）：重要議題和關鍵成果是否有提及
- 表達清楚（1-3分）：摘要是否條理分明、易於理解  
- 遵循指令(1-2分)：是否完全遵循指令，以繁體中文回覆
- 簡潔性（1-2分）：是否避免冗餘，切中要點

請以以下格式回覆：
分數: [1-10的整數]
評語: [簡短評語，說明評分理由]"""

            user_content = f"""原文：
{original_text}

摘要結果：
{model_output}

請評分並給出評語。"""

        # 呼叫對應的評審 API
        if reviewer_type == "openai":
            response = self.call_openai_api(
                reviewer_model, system_prompt, user_content, is_reviewer=True
            )
        elif reviewer_type == "gemini":
            response = self.call_google_api(
                reviewer_model, system_prompt, user_content, is_reviewer=True
            )
        elif reviewer_type == "openrouter":
            response = self.call_openrouter_api(
                reviewer_model, system_prompt, user_content, is_reviewer=True
            )
        elif reviewer_type == "replicate":
            response = self.call_replicate_api(
                reviewer_model, system_prompt, user_content, is_reviewer=True
            )
        else:
            return 0, "ERROR: 不支援的評審模型類型"

        # 解析評審模型返回的文字，提取分數和評語
        try:
            lines = response.split("\n")
            score = 0
            comment = "無評語"
            comment_started = False
            comment_lines = []
            found_score = False
            found_comment = False

            for line in lines:
                line = line.strip()
                # 尋找 "分數:" 或簡體的 "分数:" 開頭的行
                if line.startswith("分數:") or line.startswith("分数:"):
                    score_text = line.split(":")[1].strip()
                    # 從文字中提取所有數字部分並轉換為整數
                    score = int("".join(filter(str.isdigit, score_text)))
                    found_score = True
                # 尋找 "評語:" 或簡體的 "评语:" 開頭的行
                elif line.startswith("評語:") or line.startswith("评语:"):
                    # 處理評語可能跨越多行的情況
                    initial_comment = line.split(":", 1)[1].strip()
                    if initial_comment:
                        comment_lines.append(initial_comment)
                    comment_started = True
                    found_comment = True
                elif comment_started and line:
                    comment_lines.append(line)

            if comment_lines:
                comment = " ".join(comment_lines) # 將多行評語合併為一行

            # 如果找不到特定格式的分數和評語，則認為解析失敗
            if not found_score and not found_comment:
                return 1, f"解析失敗: {response[:100]}..."

            # 確保分數在 1 到 10 的有效範圍內
            score = max(1, min(10, score))
            return score, comment

        except Exception as e:
            print(f"  ⚠️  解析評分失敗: {e}")
            return 1, f"解析失敗: {response[:100]}..." # 返回部分回應內容以供除錯

    def run_evaluation(self):
        """
        執行完整的評比流程。

        這是整個評比工作的核心協調函式。
        """
        print("🚀 開始模型評比...")

        # 步驟 1: 讀取輸入文本
        input_text = self.read_input_text()
        print(f"📖 已讀取測試文本 ({len(input_text)} 字元)")

        # 步驟 2: 遍歷所有要測試的 Ollama 模型，執行各項任務
        for model in OLLAMA_MODELS_TO_COMPARE:
            print(f"\n🔍 正在測試模型: {model}")
            self.results[model] = {}

            for task in SUPPORTED_TASKS.keys():
                print(f"  📝 執行任務: {task}")

                # 呼叫 Ollama API 並儲存結果
                result = self.call_ollama_api(model, task, input_text)
                self.results[model][task] = result

                if result.startswith("ERROR:"):
                    print(f"  ❌ 任務失敗: {result}")
                else:
                    print(f"  ✅ 任務完成 ({len(result)} 字元)")

                time.sleep(1)  # 短暫延遲，避免對 API 造成過大壓力

        # 步驟 3: 遍歷所有評審模型，對前一步的結果進行評分
        print("\n⚖️  開始評審階段...")
        self.evaluation_scores = {}

        for reviewer_config in REVIEWER_MODELS:
            reviewer_provider = reviewer_config["provider"]
            reviewer_model = reviewer_config["model"]
            
            # 建立一個對檔案系統友善的唯一評審者 ID
            reviewer_id = f"{reviewer_provider}_{reviewer_model.replace('/', '_').replace(':', '_').replace('-', '_')}"

            print(f"\n🎯 使用評審模型: {reviewer_provider} ({reviewer_model})")
            self.evaluation_scores[reviewer_id] = {}

            for model in OLLAMA_MODELS_TO_COMPARE:
                self.evaluation_scores[reviewer_id][model] = {}

                for task in SUPPORTED_TASKS.keys():
                    # 如果模型執行失敗，則直接給 0 分
                    if self.results[model][task].startswith("ERROR:"):
                        score, comment = 0, "模型執行失敗"
                    else:
                        print(f"  📊 評審 {model} 的 {task} 結果...")
                        # 呼叫評審函式
                        score, comment = self.evaluate_with_reviewer(
                            reviewer_provider,
                            reviewer_model,
                            task,
                            input_text,
                            self.results[model][task],
                        )

                    # 儲存評分結果
                    self.evaluation_scores[reviewer_id][model][task] = {
                        "score": score,
                        "comment": comment,
                    }

                    print(f"    分數: {score}/10")
                    time.sleep(1)  # 避免 API 限制

    def generate_report(self):
        """
        生成最終的評比報表（Markdown 和 HTML）。
        """
        print("\n📊 正在生成報表...")
        
        # 使用當前時間建立獨一無二的時間戳記，用於檔名
        timestamp = datetime.now().strftime("%Y%m%d%H%M")
        
        # 步驟 1: 優先生成圖表檔案，因為 Markdown 報表需要引用它們
        self.create_charts(timestamp)
        
        # 步驟 2: 建立 Markdown 報表的完整內容
        report_content = self.create_markdown_report(timestamp)
        
        # 步驟 3: 將 Markdown 內容寫入檔案
        report_md_path = f"reports/evaluation_report_{timestamp}.md"
        with open(report_md_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        
        print(f"✅ Markdown 報表已生成: {report_md_path}")
        
        # 步驟 4: 將 Markdown 檔案轉換為 HTML
        report_html_path = f"reports/evaluation_report_{timestamp}.html"
        convert_markdown_to_html(report_md_path, report_html_path)
        print(f"✅ HTML 報表已生成: {report_html_path}")
        
        return report_md_path, report_html_path

    def create_markdown_report(self, timestamp: str) -> str:
        """
        組合出 Markdown 格式的報表字串。

        Args:
            timestamp (str): 用於連結圖檔的時間戳記。

        Returns:
            str: 完整的 Markdown 報表內容。
        """
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 報表標頭
        content = f"""# Ollama 模型評比報表

**生成時間**: {current_time}

## 評比概要

本次評比測試了 {len(OLLAMA_MODELS_TO_COMPARE)} 個 Ollama 模型在兩個任務上的表現：
- **翻譯任務** (Translate): 英文翻譯為繁體中文
- **摘要任務** (Summarize): 會議記錄摘要

### 測試模型清單
"""
        # 列出所有被測試的 Ollama 模型
        for i, model in enumerate(OLLAMA_MODELS_TO_COMPARE, 1):
            content += f"{i}. `{model}`\n"

        # 列出所有評審模型
        content += "\n### 評審模型\n"
        for reviewer_config in REVIEWER_MODELS:
            reviewer_provider = reviewer_config["provider"]
            reviewer_model = reviewer_config["model"]
            content += f"- **{reviewer_provider.upper()}**: `{reviewer_model}`\n"

        # 為每個評審模型建立一個評分表格
        for reviewer_config in REVIEWER_MODELS:
            reviewer_provider = reviewer_config["provider"]
            reviewer_model = reviewer_config["model"]
            reviewer_id = f"{reviewer_provider}_{reviewer_model.replace('/', '_').replace(':', '_').replace('-', '_')}"
            
            if reviewer_id not in self.evaluation_scores:
                continue

            content += f"\n## {reviewer_provider.upper()} ({reviewer_model}) 評審結果\n\n"
            content += "| 模型 | 翻譯分數 | 翻譯評語 | 摘要分數 | 摘要評語 | 平均分數 |\n"
            content += "|------|----------|----------|----------|----------|----------|\n"

            # 填入每個模型的分數和評語
            for model in OLLAMA_MODELS_TO_COMPARE:
                if model in self.evaluation_scores[reviewer_id]:
                    translate_score = self.evaluation_scores[reviewer_id][model].get("translate", {}).get("score", 0)
                    translate_comment = self.evaluation_scores[reviewer_id][model].get("translate", {}).get("comment", "N/A")
                    summarize_score = self.evaluation_scores[reviewer_id][model].get("summarize", {}).get("score", 0)
                    summarize_comment = self.evaluation_scores[reviewer_id][model].get("summarize", {}).get("comment", "N/A")
                    avg_score = (translate_score + summarize_score) / 2
                    content += f"| `{model}` | {translate_score} | {translate_comment} | {summarize_score} | {summarize_comment} | {avg_score:.1f} |\n"

        # 統計分析區塊
        content += "\n## 統計分析\n\n"
        for reviewer_config in REVIEWER_MODELS:
            reviewer_provider = reviewer_config["provider"]
            reviewer_model = reviewer_config["model"]
            reviewer_id = f"{reviewer_provider}_{reviewer_model.replace('/', '_').replace(':', '_').replace('-', '_')}"
            
            if reviewer_id not in self.evaluation_scores:
                continue

            content += f"### {reviewer_provider.upper()} ({reviewer_model}) 評審統計\n\n"

            # 計算每個任務的平均分、最高分、最低分
            translate_scores = [self.evaluation_scores[reviewer_id][m].get("translate", {}).get("score", 0) for m in OLLAMA_MODELS_TO_COMPARE if m in self.evaluation_scores[reviewer_id] and self.evaluation_scores[reviewer_id][m].get("translate", {}).get("score", 0) > 0]
            summarize_scores = [self.evaluation_scores[reviewer_id][m].get("summarize", {}).get("score", 0) for m in OLLAMA_MODELS_TO_COMPARE if m in self.evaluation_scores[reviewer_id] and self.evaluation_scores[reviewer_id][m].get("summarize", {}).get("score", 0) > 0]

            if translate_scores:
                content += f"- **翻譯任務平均分數**: {np.mean(translate_scores):.2f}\n"
                content += f"- **翻譯任務最高分**: {max(translate_scores)}\n"
                content += f"- **翻譯任務最低分**: {min(translate_scores)}\n"

            if summarize_scores:
                content += f"- **摘要任務平均分數**: {np.mean(summarize_scores):.2f}\n"
                content += f"- **摘要任務最高分**: {max(summarize_scores)}\n"
                content += f"- **摘要任務最低分**: {min(summarize_scores)}\n"
            content += "\n"

        # 視覺化圖表區塊
        content += "## 視覺化圖表\n\n"
        for reviewer_config in REVIEWER_MODELS:
            reviewer_provider = reviewer_config["provider"]
            reviewer_model = reviewer_config["model"]
            reviewer_id = f"{reviewer_provider}_{reviewer_model.replace('/', '_').replace(':', '_').replace('-', '_')}"
            
            if reviewer_id not in self.evaluation_scores:
                continue
            
            chart_path = f"chart_{reviewer_id}_{timestamp}.png"
            content += f"### {reviewer_provider.upper()} ({reviewer_model}) 評審結果圖表\n\n"
            content += f"![{reviewer_provider.upper()} ({reviewer_model}) 評審結果]({chart_path})\n\n"

        # 附錄：模型原始輸出結果
        content += "## 模型輸出結果\n\n"
        for model in OLLAMA_MODELS_TO_COMPARE:
            content += f"### {model}\n\n"
            for task in SUPPORTED_TASKS.keys():
                content += f"#### {task.capitalize()} 結果\n\n"
                content += "```\n"
                content += self.results[model][task]
                content += "\n```\n\n"

        return content

    def create_charts(self, timestamp: str):
        """
        使用 Matplotlib 生成比較各模型表現的長條圖，並儲存為 PNG 檔案。

        Args:
            timestamp (str): 用於生成唯一檔名的時間戳記。
        """
        print("📈 正在生成圖表...")

        for reviewer_config in REVIEWER_MODELS:
            reviewer_provider = reviewer_config["provider"]
            reviewer_model = reviewer_config["model"]
            reviewer_id = f"{reviewer_provider}_{reviewer_model.replace('/', '_').replace(':', '_').replace('-', '_')}"
            
            if reviewer_id not in self.evaluation_scores:
                continue

            # 準備繪圖所需的數據
            models = []
            translate_scores = []
            summarize_scores = []

            for model in OLLAMA_MODELS_TO_COMPARE:
                if model in self.evaluation_scores[reviewer_id]:
                    # 簡化模型名稱以利顯示
                    models.append(model.replace("hf.co/mradermacher/", "").replace(":Q4_K_M", ""))
                    translate_scores.append(self.evaluation_scores[reviewer_id][model].get("translate", {}).get("score", 0))
                    summarize_scores.append(self.evaluation_scores[reviewer_id][model].get("summarize", {}).get("score", 0))

            if not models:
                continue

            # 開始繪圖
            x = np.arange(len(models))  # X 軸座標
            width = 0.35  # 長條寬度

            fig, ax = plt.subplots(figsize=(12, 8)) # 設定畫布大小
            # 繪製翻譯分數的長條
            bars1 = ax.bar(x - width / 2, translate_scores, width, label="翻譯 (Translate)", alpha=0.8)
            # 繪製摘要分數的長條
            bars2 = ax.bar(x + width / 2, summarize_scores, width, label="摘要 (Summarize)", alpha=0.8)

            # 設定圖表標題、座標軸標籤等
            ax.set_xlabel("模型")
            ax.set_ylabel("分數")
            ax.set_title(f"模型評比結果 - {reviewer_provider.upper()} ({reviewer_model}) 評審")
            ax.set_xticks(x)
            ax.set_xticklabels(models, rotation=45, ha="right") # X 軸標籤旋轉以免重疊
            ax.legend()
            ax.set_ylim(0, 10) # Y 軸範圍設為 0-10

            # 在每個長條上方顯示分數值
            def autolabel(bars):
                for bar in bars:
                    height = bar.get_height()
                    ax.annotate(
                        f"{height}",
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),  # 垂直偏移 3 點
                        textcoords="offset points",
                        ha="center",
                        va="bottom",
                    )

            autolabel(bars1)
            autolabel(bars2)

            plt.tight_layout()  # 自動調整版面
            chart_path = f"reports/chart_{reviewer_id}_{timestamp}.png"
            plt.savefig(chart_path, dpi=300, bbox_inches="tight") # 儲存圖檔
            plt.close() # 關閉畫布，釋放資源

            print(f"✅ 圖表已生成: {chart_path}")


def main():
    """
    主程式入口函式。
    """
    print("🎯 Ollama 模型評比系統")
    print("=" * 50)

    # 執行前的基本檢查
    if not OLLAMA_MODELS_TO_COMPARE:
        print("❌ 未設定要評比的模型，請檢查 config.py")
        sys.exit(1)

    if not REVIEWER_MODELS:
        print("❌ 未設定評審模型，請檢查 config.py")
        sys.exit(1)

    # 建立評比器物件
    evaluator = ModelEvaluator()

    try:
        # 執行評比流程
        evaluator.run_evaluation()

        # 生成報表
        md_path, html_path = evaluator.generate_report()

        # 顯示最終結果
        print("\n" + "=" * 50)
        print("🎉 評比完成！")
        print(f"📄 Markdown 報表: {md_path}")
        print(f"🌐 HTML 報表: {html_path}")
        print("=" * 50)

    except KeyboardInterrupt:
        # 處理使用者手動中斷 (Ctrl+C)
        print("\n❌ 使用者中斷執行")
        sys.exit(1)
    except Exception as e:
        # 捕捉所有其他未預期的錯誤
        print(f"\n❌ 執行過程中發生錯誤: {e}")
        sys.exit(1)


# 當此腳本被直接執行時，才呼叫 main() 函式
if __name__ == "__main__":
    main()
