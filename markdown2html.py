#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Markdown 到 HTML 轉換工具

這個腳本提供了一個函式 `convert_markdown_to_html`，能夠將指定的 Markdown 檔案
轉換成一個包含完整結構和樣式的 HTML 檔案。

主要功能：
- 使用 `python-markdown` 函式庫進行核心轉換。
- 支援標準 Markdown 語法，並透過擴充套件支援額外功能：
  - `tables`: 轉換 Markdown 表格。
  - `fenced_code` & `codehilite`: 處理程式碼區塊並進行語法高亮。
  - `toc`: 自動生成目錄 (Table of Contents)。
  - `pymdownx.superfences`: 增強的程式碼區塊，特別設定用於支援 Mermaid.js 圖表。
  - `nl2br`: 將換行符轉換為 `<br>` 標籤。
- 內嵌美觀的 CSS 樣式，提升可讀性，包括對表格、程式碼、圖片等的樣式設定。
- 整合 Mermaid.js，可以直接在 Markdown 中使用 ` ```mermaid ` 語法繪製圖表。
- 提供命令列介面，可直接執行此腳本來轉換檔案。

使用範例 (作為函式庫)：
```python
from markdown2html import convert_markdown_to_html

convert_markdown_to_html('input.md', 'output.html')
```

使用範例 (命令列)：
```bash
python markdown2html.py report.md
python markdown2html.py report.md final_report.html
```
"""

# 匯入必要的模組
import argparse  # 用於解析命令列參數
import os  # 處理作業系統相關功能，如路徑
import sys  # 存取 Python 直譯器的變數和函式
from markdown import markdown  # 從 markdown 函式庫匯入核心轉換函式

def create_full_html_doc(title, body_content):
    """
    建立一個包含完整 HTML 結構、CSS 樣式和 Mermaid.js 支援的 HTML 文件字串。

    Args:
        title (str): HTML 文件的 `<title>` 標籤內容。
        body_content (str): 要放入 `<body>` 標籤中的主要 HTML 內容。

    Returns:
        str: 格式化後的完整 HTML 文件內容字串。
    """
    # 使用 f-string 建立 HTML 模板
    html_template = f'''<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        /* 提供一些適合閱讀的通用基本樣式 */
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1000px; /* 設定最大寬度，避免在寬螢幕上內容過寬 */
            margin: 20px auto; /* 上下邊距 20px，左右自動置中 */
            padding: 0 20px; /* 內邊距，避免內容緊貼邊緣 */
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: #222;
            margin-top: 2em;
            margin-bottom: 1em;
        }}
        h1 {{
            border-bottom: 2px solid #eee; /* h1 標題底線 */
            padding-bottom: 0.3em;
        }}
        h2 {{
            border-bottom: 1px solid #eee; /* h2 標題底線 */
            padding-bottom: 0.3em;
        }}
        code {{
            background-color: #f4f4f4; /* 行內程式碼背景色 */
            padding: 2px 4px;
            border-radius: 4px;
            font-family: "Courier New", Courier, monospace;
        }}
        pre:not(.mermaid) {{ /* 針對非 Mermaid 的 pre 區塊設定樣式 */
            background-color: #f4f4f4; /* 程式碼區塊背景色 */
            padding: 1rem;
            border-radius: 4px;
            overflow-x: auto; /* 當程式碼過長時，顯示水平捲軸 */
        }}
        img {{
            max-width: 100%; /* 圖片最大寬度為 100%，確保自適應 */
            height: auto;
        }}
        /* 表格樣式 */
        table {{
            border-collapse: collapse; /* 邊框合併 */
            width: 100%;
            margin: 1em 0;
            font-size: 0.9em;
        }}
        th, td {{
            border: 1px solid #ddd; /* 表格邊框 */
            padding: 8px 12px;
            text-align: left;
            vertical-align: top;
        }}
        th {{
            background-color: #f2f2f2; /* 表頭背景色 */
            font-weight: bold;
            text-align: center;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9; /* 斑馬條紋 */
        }}
        tr:hover {{
            background-color: #f5f5f5; /* 滑鼠懸停效果 */
        }}
        /* 區塊引用樣式 */
        blockquote {{
            border-left: 4px solid #ddd;
            margin: 1em 0;
            padding-left: 1em;
            color: #666;
        }}
        /* 清單樣式 */
        ul, ol {{
            padding-left: 2em;
        }}
        li {{
            margin: 0.5em 0;
        }}
    </style>
</head>
<body>
{body_content}

<!-- 引入 Mermaid.js 的 CDN -->
<script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script>
        // 初始化 Mermaid.js
        mermaid.initialize({{ 
            startOnLoad: true, // 頁面載入時自動渲染 mermaid 圖表
            theme: 'default' // 可選主題: 'default', 'neutral', 'dark', 'forest'
        }});
    </script>
</body>
</html>'''
    return html_template

def convert_markdown_to_html(input_path, output_path=None):
    """
    將指定的 Markdown 檔案轉換為一個功能完整的 HTML 檔案。
    
    此函式會讀取輸入的 Markdown 檔案，使用擴充套件將其轉換為 HTML 片段，
    然後將此片段嵌入一個包含 CSS 樣式和 Mermaid.js 腳本的完整 HTML 結構中。
    """
    # 檢查輸入檔案是否存在，若不存在則拋出錯誤
    if not os.path.exists(input_path):
        print(f"錯誤：找不到輸入檔案 '{input_path}'", file=sys.stderr)
        raise FileNotFoundError(f"找不到輸入檔案 '{input_path}'")

    # 如果未指定輸出路徑，則根據輸入路徑自動生成
    base_name_without_ext = os.path.splitext(input_path)[0]
    if output_path is None:
        output_path = f"{base_name_without_ext}.html"

    print(f"正在將 '{input_path}' 轉換至 '{output_path}'...")

    try:
        # 讀取 Markdown 檔案的完整內容
        with open(input_path, 'r', encoding='utf-8') as f_in:
            markdown_text = f_in.read()

        # 設定 SuperFences 擴充，使其能辨識並正確處理 mermaid 程式碼區塊
        extension_configs = {
            'pymdownx.superfences': {
                'custom_fences': [{
                    'name': 'mermaid',  # 在 markdown 中使用 ```mermaid
                    'class': 'mermaid',  # 轉換後套用的 CSS class
                    # 這個 format 函式會保留原始碼，並用 <pre class="mermaid"> 包起來，交給前端的 Mermaid.js 渲染
                    'format': lambda source, language, css_class, options, md, **kwargs: f'<pre class="{css_class}">{source}</pre>'
                }]
            }
        }

        # 執行 Markdown 到 HTML 的轉換
        html_fragment = markdown(
            markdown_text,
            extensions=[
                'tables',           # 啟用表格擴充
                'fenced_code',      # 啟用圍欄程式碼區塊擴充
                'codehilite',       # 啟用程式碼語法高亮擴充
                'toc',              # 啟用目錄生成擴充
                'pymdownx.superfences',  # 啟用 SuperFences 擴充以支援 Mermaid
                'nl2br',            # 啟用換行符轉 <br> 擴充
                'sane_lists'        # 改善清單的處理邏輯
            ],
            extension_configs=extension_configs
        )

        # 使用輔助函式建立完整的 HTML 文件
        full_html = create_full_html_doc(
            title=os.path.basename(base_name_without_ext), # 使用檔名作為標題
            body_content=html_fragment
        )

        # 將最終的 HTML 內容寫入輸出檔案
        with open(output_path, 'w', encoding='utf-8') as f_out:
            f_out.write(full_html)
            
        print("✅ 轉換成功！")

    except Exception as e:
        # 如果在過程中發生任何錯誤，印出錯誤訊息並重新拋出例外
        print(f"轉換過程中發生錯誤：{e}", file=sys.stderr)
        raise

# --- 主程式進入點 ---

# 當這個腳本被直接從命令列執行時
if __name__ == "__main__":
    # 檢查是否提供了檔案參數
    if len(sys.argv) == 1:
        print("用法: python markdown2html.py <輸入檔案> [輸出檔案]")
        print("請提供要轉換的 Markdown 檔案路徑。")
        sys.exit(1)
    
    # 設定命令列參數解析器
    parser = argparse.ArgumentParser(
        description="一個能將 Markdown (包含 Mermaid 圖表) 轉換為單一 HTML 檔案的工具。",
        epilog="範例: python markdown2html.py my_report.md my_report.html"
    )
    
    # 定義必要參數：輸入檔案
    parser.add_argument("input_file", help="要轉換的 Markdown 檔案路徑。")
    # 定義可選參數：輸出檔案
    parser.add_argument("output_file", nargs='?', default=None, help="輸出的 HTML 檔案路徑 (可選，預設為同檔名.html)。")
    
    # 解析傳入的參數
    args = parser.parse_args()
    
    # 呼叫主轉換函式
    convert_markdown_to_html(args.input_file, args.output_file)
