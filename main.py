#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import sys
import time
import requests
from typing import Dict, List, Tuple, Any
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
from config import (
    OLLAMA_API_BASE_URL, 
    OLLAMA_MODELS_TO_COMPARE, 
    OPENAI_API_KEY, 
    GOOGLE_API_KEY,
    REVIEWER_MODELS, 
    SUPPORTED_TASKS
)
from markdown2html import convert_markdown_to_html

# 設定中文字體
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class ModelEvaluator:
    def __init__(self):
        self.results = {}
        self.evaluation_scores = {}
        
    def read_input_text(self, file_path: str = "input.txt") -> str:
        """讀取測試樣本文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"❌ 找不到輸入檔案: {file_path}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ 讀取檔案時發生錯誤: {e}")
            sys.exit(1)

    def call_ollama_api(self, model: str, task: str, text: str) -> str:
        """呼叫 Ollama API"""
        url = f"{OLLAMA_API_BASE_URL}/api/chat"
        headers = {"Content-Type": "application/json"}
        
        prompt = SUPPORTED_TASKS[task]
        
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": text}
            ],
            "stream": False
        }
        
        try:
            print(f"  🔄 正在呼叫 {model} 執行 {task} 任務...")
            response = requests.post(url, headers=headers, json=data, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            text = result["message"]["content"].strip()
            text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
            return text
            
        except requests.exceptions.Timeout:
            print(f"  ⚠️  {model} 回應超時")
            return "ERROR: 回應超時"
        except requests.exceptions.RequestException as e:
            print(f"  ❌ {model} API 呼叫失敗: {e}")
            return f"ERROR: API 呼叫失敗 - {e}"
        except Exception as e:
            print(f"  ❌ {model} 處理回應時發生錯誤: {e}")
            return f"ERROR: 處理回應失敗 - {e}"

    def call_openai_api(self, model: str, system_prompt: str, user_content: str) -> str:
        """呼叫 OpenAI API"""
        if not OPENAI_API_KEY or OPENAI_API_KEY == "your_openai_api_key_here":
            return "ERROR: OpenAI API 金鑰未設定"
            
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            "temperature": 0.1
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            text = result["choices"][0]["message"]["content"].strip()
            return text        
        except Exception as e:
            print(f"  ❌ OpenAI API 呼叫失敗: {e}")
            return f"ERROR: OpenAI API 失敗 - {e}"

    def call_google_api(self, model: str, system_prompt: str, user_content: str) -> str:
        """呼叫 Google Gemini API"""
        if not GOOGLE_API_KEY or GOOGLE_API_KEY == "your_google_api_key_here":
            return "ERROR: Google API 金鑰未設定"
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GOOGLE_API_KEY}"
        headers = {"Content-Type": "application/json"}
        
        data = {
            "contents": [{
                "parts": [{
                    "text": f"{system_prompt}\n\n{user_content}"
                }]
            }],
            "generationConfig": {
                "temperature": 0.1
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            return result["candidates"][0]["content"]["parts"][0]["text"].strip()
            
        except Exception as e:
            print(f"  ❌ Google API 呼叫失敗: {e}")
            return f"ERROR: Google API 失敗 - {e}"

    def evaluate_with_reviewer(self, reviewer_type: str, reviewer_model: str, task: str, 
                             original_text: str, model_output: str) -> Tuple[int, str]:
        """使用評審模型評分"""
        
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
            response = self.call_openai_api(reviewer_model, system_prompt, user_content)
        elif reviewer_type == "gemini":
            response = self.call_google_api(reviewer_model, system_prompt, user_content)
        else:
            return 0, "ERROR: 不支援的評審模型類型"
        
        # 解析評分結果
        try:
            lines = response.split('\n')
            score = 0
            comment = "無評語"
            
            for line in lines:
                if line.startswith('分數:') or line.startswith('分数:'):
                    score_text = line.split(':')[1].strip()
                    score = int(''.join(filter(str.isdigit, score_text)))
                elif line.startswith('評語:') or line.startswith('评语:'):
                    comment = line.split(':', 1)[1].strip()
            
            # 確保分數在有效範圍內
            score = max(1, min(10, score))
            return score, comment
            
        except Exception as e:
            print(f"  ⚠️  解析評分失敗: {e}")
            return 5, f"解析失敗: {response[:100]}..."

    def run_evaluation(self):
        """執行完整的評比流程"""
        print("🚀 開始模型評比...")
        
        # 讀取測試文本
        input_text = self.read_input_text()
        print(f"📖 已讀取測試文本 ({len(input_text)} 字元)")
        
        # 對每個模型執行任務
        for model in OLLAMA_MODELS_TO_COMPARE:
            print(f"\n🔍 正在測試模型: {model}")
            self.results[model] = {}
            
            for task in SUPPORTED_TASKS.keys():
                print(f"  📝 執行任務: {task}")
                
                # 呼叫 Ollama 模型
                result = self.call_ollama_api(model, task, input_text)
                self.results[model][task] = result
                
                if result.startswith("ERROR:"):
                    print(f"  ❌ 任務失敗: {result}")
                else:
                    print(f"  ✅ 任務完成 ({len(result)} 字元)")
                
                # 短暫延遲避免 API 限制
                time.sleep(1)
        
        # 使用評審模型評分
        print(f"\n⚖️  開始評審階段...")
        self.evaluation_scores = {}
        
        for reviewer_type, reviewer_model in REVIEWER_MODELS.items():
            if reviewer_model is None:
                continue
                
            print(f"\n🎯 使用評審模型: {reviewer_type} ({reviewer_model})")
            self.evaluation_scores[reviewer_type] = {}
            
            for model in OLLAMA_MODELS_TO_COMPARE:
                self.evaluation_scores[reviewer_type][model] = {}
                
                for task in SUPPORTED_TASKS.keys():
                    if self.results[model][task].startswith("ERROR:"):
                        score, comment = 0, "模型執行失敗"
                    else:
                        print(f"  📊 評審 {model} 的 {task} 結果...")
                        score, comment = self.evaluate_with_reviewer(
                            reviewer_type, reviewer_model, task, 
                            input_text, self.results[model][task]
                        )
                    
                    self.evaluation_scores[reviewer_type][model][task] = {
                        "score": score,
                        "comment": comment
                    }
                    
                    print(f"    分數: {score}/10")
                    time.sleep(1)  # 避免 API 限制

    def generate_report(self):
        """生成評比報表"""
        print(f"\n📊 正在生成報表...")
        
        # 先生成圖表
        self.create_charts()
        
        # 建立報表內容
        report_content = self.create_markdown_report()
        
        # 寫入 Markdown 檔案
        report_md_path = "reports/evaluation_report.md"
        with open(report_md_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"✅ Markdown 報表已生成: {report_md_path}")
        
        # 轉換為 HTML
        report_html_path = "reports/evaluation_report.html"
        convert_markdown_to_html(report_md_path, report_html_path)
        print(f"✅ HTML 報表已生成: {report_html_path}")
        
        return report_md_path, report_html_path

    def create_markdown_report(self) -> str:
        """建立 Markdown 格式的報表"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        content = f"""# Ollama 模型評比報表

**生成時間**: {current_time}

## 評比概要

本次評比測試了 {len(OLLAMA_MODELS_TO_COMPARE)} 個 Ollama 模型在兩個任務上的表現：
- **翻譯任務** (Translate): 英文翻譯為繁體中文
- **摘要任務** (Summarize): 會議記錄摘要

### 測試模型清單
"""
        
        for i, model in enumerate(OLLAMA_MODELS_TO_COMPARE, 1):
            content += f"{i}. `{model}`\n"
        
        content += f"\n### 評審模型\n"
        for reviewer_type, reviewer_model in REVIEWER_MODELS.items():
            if reviewer_model:
                content += f"- **{reviewer_type.upper()}**: `{reviewer_model}`\n"
        
        # 評分表格
        for reviewer_type, reviewer_model in REVIEWER_MODELS.items():
            if reviewer_model is None or reviewer_type not in self.evaluation_scores:
                continue
                
            content += f"\n## {reviewer_type.upper()} 評審結果\n\n"
            content += "| 模型 | 翻譯分數 | 翻譯評語 | 摘要分數 | 摘要評語 | 平均分數 |\n"
            content += "|------|----------|----------|----------|----------|----------|\n"
            
            for model in OLLAMA_MODELS_TO_COMPARE:
                if model in self.evaluation_scores[reviewer_type]:
                    translate_score = self.evaluation_scores[reviewer_type][model].get('translate', {}).get('score', 0)
                    translate_comment = self.evaluation_scores[reviewer_type][model].get('translate', {}).get('comment', 'N/A')
                    summarize_score = self.evaluation_scores[reviewer_type][model].get('summarize', {}).get('score', 0)
                    summarize_comment = self.evaluation_scores[reviewer_type][model].get('summarize', {}).get('comment', 'N/A')
                    avg_score = (translate_score + summarize_score) / 2
                    
                    content += f"| `{model}` | {translate_score} | {translate_comment} | {summarize_score} | {summarize_comment} | {avg_score:.1f} |\n"
        
        # 統計分析
        content += "\n## 統計分析\n\n"
        
        for reviewer_type in REVIEWER_MODELS.keys():
            if reviewer_type not in self.evaluation_scores:
                continue
                
            content += f"### {reviewer_type.upper()} 評審統計\n\n"
            
            # 計算各任務平均分數
            translate_scores = []
            summarize_scores = []
            
            for model in OLLAMA_MODELS_TO_COMPARE:
                if model in self.evaluation_scores[reviewer_type]:
                    t_score = self.evaluation_scores[reviewer_type][model].get('translate', {}).get('score', 0)
                    s_score = self.evaluation_scores[reviewer_type][model].get('summarize', {}).get('score', 0)
                    if t_score > 0:
                        translate_scores.append(t_score)
                    if s_score > 0:
                        summarize_scores.append(s_score)
            
            if translate_scores:
                content += f"- **翻譯任務平均分數**: {np.mean(translate_scores):.2f}\n"
                content += f"- **翻譯任務最高分**: {max(translate_scores)}\n"
                content += f"- **翻譯任務最低分**: {min(translate_scores)}\n"
            
            if summarize_scores:
                content += f"- **摘要任務平均分數**: {np.mean(summarize_scores):.2f}\n"
                content += f"- **摘要任務最高分**: {max(summarize_scores)}\n"
                content += f"- **摘要任務最低分**: {min(summarize_scores)}\n"
            
            content += "\n"
        
        # 視覺化圖表
        content += "## 視覺化圖表\n\n"
        
        for reviewer_type in REVIEWER_MODELS.keys():
            if reviewer_type not in self.evaluation_scores:
                continue
                
            chart_path = f"chart_{reviewer_type}.png"
            content += f"### {reviewer_type.upper()} 評審結果圖表\n\n"
            content += f"![{reviewer_type.upper()} 評審結果]({chart_path})\n\n"
        
        # 模型輸出結果
        content += "## 模型輸出結果\n\n"
        
        for model in OLLAMA_MODELS_TO_COMPARE:
            content += f"### {model}\n\n"
            
            for task in SUPPORTED_TASKS.keys():
                content += f"#### {task.capitalize()} 結果\n\n"
                content += "```\n"
                content += self.results[model][task]
                content += "\n```\n\n"
        
        return content

    def create_charts(self):
        """生成比較圖表"""
        print("📈 正在生成圖表...")
        
        for reviewer_type in REVIEWER_MODELS.keys():
            if reviewer_type not in self.evaluation_scores:
                continue
                
            # 準備數據
            models = []
            translate_scores = []
            summarize_scores = []
            
            for model in OLLAMA_MODELS_TO_COMPARE:
                if model in self.evaluation_scores[reviewer_type]:
                    models.append(model.replace('hf.co/mradermacher/', '').replace(':Q4_K_M', ''))
                    translate_scores.append(self.evaluation_scores[reviewer_type][model].get('translate', {}).get('score', 0))
                    summarize_scores.append(self.evaluation_scores[reviewer_type][model].get('summarize', {}).get('score', 0))
            
            if not models:
                continue
                
            # 建立長條圖
            x = np.arange(len(models))
            width = 0.35
            
            fig, ax = plt.subplots(figsize=(12, 8))
            bars1 = ax.bar(x - width/2, translate_scores, width, label='翻譯 (Translate)', alpha=0.8)
            bars2 = ax.bar(x + width/2, summarize_scores, width, label='摘要 (Summarize)', alpha=0.8)
            
            ax.set_xlabel('模型')
            ax.set_ylabel('分數')
            ax.set_title(f'模型評比結果 - {reviewer_type.upper()} 評審')
            ax.set_xticks(x)
            ax.set_xticklabels(models, rotation=45, ha='right')
            ax.legend()
            ax.set_ylim(0, 10)
            
            # 在長條上顯示數值
            def autolabel(bars):
                for bar in bars:
                    height = bar.get_height()
                    ax.annotate(f'{height}',
                               xy=(bar.get_x() + bar.get_width() / 2, height),
                               xytext=(0, 3),
                               textcoords="offset points",
                               ha='center', va='bottom')
            
            autolabel(bars1)
            autolabel(bars2)
            
            plt.tight_layout()
            chart_path = f"reports/chart_{reviewer_type}.png"
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"✅ 圖表已生成: {chart_path}")

def main():
    """主程式入口"""
    print("🎯 Ollama 模型評比系統")
    print("=" * 50)
    
    # 檢查設定
    if not OLLAMA_MODELS_TO_COMPARE:
        print("❌ 未設定要評比的模型，請檢查 config.py")
        sys.exit(1)
    
    if not any(REVIEWER_MODELS.values()):
        print("❌ 未設定評審模型，請檢查 config.py")
        sys.exit(1)
    
    # 建立評比器並執行
    evaluator = ModelEvaluator()
    
    try:
        # 執行評比
        evaluator.run_evaluation()
        
        # 生成報表
        md_path, html_path = evaluator.generate_report()
        
        print("\n" + "=" * 50)
        print("🎉 評比完成！")
        print(f"📄 Markdown 報表: {md_path}")
        print(f"🌐 HTML 報表: {html_path}")
        print("=" * 50)
        
    except KeyboardInterrupt:
        print("\n❌ 使用者中斷執行")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 執行過程中發生錯誤: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 