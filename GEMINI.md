# 專案目的：評比 Ollama 上的幾個模型

## 評比方式：以雲端的 GPT-4.1 或 Gemini-2.5-flash 等較強大的模型檢視結果

## 程式語言： Python

## 設定參數

- 寫在 config.py 裡，提供使用者 config.py.example 用來自行設定
- 提示詞都寫在 config.py 的 SUPPORTED_TASKS 中

## 評比項目： Summarize 與 Translate

- 目前提供 input.txt 做為輸入樣本
- 翻譯方向：**僅英文翻中文**
- 輸出語言為 zh-TW（繁體中文）

## 模型設定

### 待評比的 Ollama 模型

在 `config.py` 的 `OLLAMA_MODELS_TO_COMPARE` 中設定：

- llama3.1:latest
- gemma3:27b
- gemma3-8b
- gemma3:12b
- hf.co/mradermacher/Llama-Breeze2-8B-Instruct-Text-GGUF:Q4_K_M

### 評審模型

在 `config.py` 的 `REVIEWER_MODELS` 中設定：

- OpenAI: gpt-4.1
- Google: gemini-2.5-flash

## 評分標準

### 翻譯評分標準（1~10分）

- **通順性**：翻譯是否自然流暢，符合中文表達習慣
- **準確性**：是否有翻譯錯誤、遺漏或誤解
- **專業術語處理**：英文專業術語是否適當保留

### 摘要評分標準（1~10分）

- **重點涵蓋**：重要議題和關鍵成果是否有提及
- **表達清楚**：摘要是否條理分明、易於理解
- **簡潔性**：是否避免冗餘，切中要點

## 報表要求

### 必要內容

1. **評分表格**：各模型在不同任務的詳細分數
2. **長條圖**：視覺化比較各模型表現
3. **統計分析**：平均分數、最佳/最差表現等

### 輸出格式

- 主要格式：Markdown
- 最終呼叫 `markdown2html.convert_markdown_to_html()` 產生 HTML 版本

## 程式實作要求

### 主程式功能

寫出一個完整的 Python 程式，具備以下功能：

1. **自動化評比流程**：
   - 讀取 input.txt 作為測試樣本
   - 對每個 Ollama 模型執行 Summarize 和 Translate 任務
   - 使用評審模型對結果進行評分

2. **可配置性**：
   - 透過修改 config.py 即可調整模型清單、評審設定
   - 支援新增其他評比任務

3. **報表產生**：
   - 自動產生包含表格和圖表的 Markdown 報表
   - 轉換為 HTML 格式以便查看

4. **錯誤處理**：
   - API 連接失敗處理
   - 模型回應異常處理

### 技術架構

- 使用現有的 `translator_ollama.py` 作為基礎
- 整合雲端 API（OpenAI、Google）進行評審
- 使用 `markdown2html.convert_markdown_to_html()` 產生最終報表

## 專案結構

```
EvaluateModels/
├── config.py.example       # 設定檔範例
├── config.py               # 實際設定檔（使用者自建）
├── input.txt               # 測試樣本
├── main.py                 # 主程式（待開發）
├── translator_ollama.py    # 現有工具函數
├── markdown2html.py        # HTML 轉換工具（待開發）
└── reports/                # 報表輸出目錄
    ├── evaluation_report.md
    └── evaluation_report.html
```
