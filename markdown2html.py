#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os
import sys
from markdown import markdown

def create_full_html_doc(title, body_content):
    """
    建立一個包含 Mermaid.js 功能的完整 HTML 文件字串。

    Args:
        title (str): HTML 文件的 <title>。
        body_content (str): 要放入 <body> 的 HTML 內容。

    Returns:
        str: 完整的 HTML 文件內容。
    """
    html_template = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        /* 提供一些適合閱讀的基本樣式 */
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1000px;
            margin: 20px auto;
            padding: 0 20px;
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: #222;
            margin-top: 2em;
            margin-bottom: 1em;
        }}
        h1 {{
            border-bottom: 2px solid #eee;
            padding-bottom: 0.3em;
        }}
        h2 {{
            border-bottom: 1px solid #eee;
            padding-bottom: 0.3em;
        }}
        code {{
            background-color: #f4f4f4;
            padding: 2px 4px;
            border-radius: 4px;
            font-family: "Courier New", Courier, monospace;
        }}
        pre:not(.mermaid) {{ /* 讓 mermaid 的 pre 背景透明 */
            background-color: #f4f4f4;
            padding: 1rem;
            border-radius: 4px;
            overflow-x: auto;
        }}
        img {{
            max-width: 100%;
            height: auto;
        }}
        /* 表格樣式 */
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 1em 0;
            font-size: 0.9em;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px 12px;
            text-align: left;
            vertical-align: top;
        }}
        th {{
            background-color: #f2f2f2;
            font-weight: bold;
            text-align: center;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        /* 讓表格在小螢幕上可以橫向滾動 */
        .table-container {{
            overflow-x: auto;
            margin: 1em 0;
        }}
        /* Mermaid 圖形預設置中 */
        .mermaid {{
            text-align: center;
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

<script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script>
        mermaid.initialize({{ 
            startOnLoad: true,
            theme: 'default' // 可選 'default', 'neutral', 'dark', 'forest'
        }});
    </script>
</body>
</html>"""
    return html_template

def convert_markdown_to_html(input_path, output_path=None):
    """
    將指定的 Markdown 檔案轉換為一個完整的 HTML 檔案，並支援 Mermaid 圖形和表格。
    """
    # 檢查輸入檔案是否存在
    if not os.path.exists(input_path):
        print(f"錯誤：找不到輸入檔案 '{input_path}'", file=sys.stderr)
        raise FileNotFoundError(f"找不到輸入檔案 '{input_path}'")

    # 如果未指定輸出檔名，則自動生成
    base_name_without_ext = os.path.splitext(input_path)[0]
    if output_path is None:
        output_path = f"{base_name_without_ext}.html"

    print(f"正在將 '{input_path}' 轉換至 '{output_path}' (包含 Mermaid 和表格支援)...")

    try:
        # 讀取 Markdown 檔案內容
        with open(input_path, 'r', encoding='utf-8') as f_in:
            markdown_text = f_in.read()

        # 設定 SuperFences 擴充，讓它可以辨識 mermaid 程式碼區塊
        extension_configs = {
            'pymdownx.superfences': {
                'custom_fences': [{
                    'name': 'mermaid', # 在 markdown 中使用 ```mermaid
                    'class': 'mermaid', # 轉換後套用的 CSS class
                    # 這個 format 函式會保留原始碼，並用 <pre class="mermaid"> 包起來
                    'format': lambda source, language, css_class, options, md, **kwargs: f'<pre class="{css_class}">{source}</pre>'
                }]
            }
        }

        # 執行轉換，啟用多個擴充套件
        html_fragment = markdown(
            markdown_text,
            extensions=[
                'tables',           # 支援表格
                'fenced_code',      # 支援程式碼區塊
                'codehilite',       # 程式碼語法高亮
                'toc',              # 目錄生成
                'pymdownx.superfences',  # 支援 Mermaid
                'nl2br',            # 換行轉換
                'sane_lists'        # 改善清單處理
            ],
            extension_configs=extension_configs
        )

        # 建立完整的 HTML 文件
        full_html = create_full_html_doc(
            title=base_name_without_ext, 
            body_content=html_fragment
        )

        # 將完整的 HTML 寫入檔案
        with open(output_path, 'w', encoding='utf-8') as f_out:
            f_out.write(full_html)
            
        print("✅ 轉換成功！已生成支援 Mermaid 和表格的 HTML 檔案。")

    except Exception as e:
        print(f"轉換過程中發生錯誤：{e}", file=sys.stderr)
        raise

if __name__ == "__main__":
    # 解析命令列參數
    if(len(sys.argv) == 1):
        print("請提供要轉換的 Markdown 檔案路徑。")
        sys.exit(1)
    
    parser = argparse.ArgumentParser(
        description="一個能轉換 Markdown 和 Mermaid 圖形到 HTML 的轉換器。",
        epilog="範例: python md_converter_mermaid.py my_diagrams.md"
    )
    
    parser.add_argument("input_file", help="要轉換的 Markdown 檔案路徑。")
    parser.add_argument("output_file", nargs='?', default=None, help="輸出的 HTML 檔案路徑 (可選)。")
    
    args = parser.parse_args()
    
    convert_markdown_to_html(args.input_file, args.output_file)
