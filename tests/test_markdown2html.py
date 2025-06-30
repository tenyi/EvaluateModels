#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
測試 markdown2html.py 的功能。

這個測試檔案旨在確保 `convert_markdown_to_html` 函式能夠正確地
將 Markdown 格式的字串或檔案轉換為包含樣式的 HTML 檔案。

主要測試內容：
- 基本的 Markdown 元素轉換 (標題、列表、表格、程式碼區塊等)。
- 包含中文內容的轉換。
- 包含圖片和連結的轉換。
- 邊界情況測試 (空檔案、檔案不存在、權限問題)。
- 整合測試，模擬一個完整的報告轉換流程。
"""

# 匯入必要的模組
import pytest  # pytest 測試框架
import tempfile  # 用於建立臨時檔案和目錄
import os  # 處理作業系統相關功能，如路徑、檔案操作
from unittest.mock import patch, mock_open  # 用於模擬 (mock) 物件和函式
import sys  # 存取 Python 直譯器的變數和函式

# 將專案根目錄加入 Python 的模組搜尋路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 從專案中匯入待測試的函式
from markdown2html import convert_markdown_to_html


# --- 測試類別：TestMarkdown2Html ---

class TestMarkdown2Html:
    """測試 Markdown 轉 HTML 的核心功能。"""

    @pytest.fixture
    def sample_markdown(self):
        """提供一個包含多種 Markdown 元素的範例字串，作為測試資料。"""
        return '''# 測試標題

這是一個測試段落。

## 子標題

- 項目 1
- 項目 2
- 項目 3

### 表格測試

| 模型 | 分數 | 評語 |
|------|------|------|
| llama2 | 8 | 良好 |
| mistral | 7 | 不錯 |

```python
def hello():
    print("Hello World")
```

**粗體文字** 和 *斜體文字*
'''

    @pytest.fixture
    def temp_files(self):
        """建立臨時的 Markdown 和 HTML 檔案，並在測試結束後自動清理。"""
        # 建立臨時 Markdown 檔案
        md_fd, md_path = tempfile.mkstemp(suffix='.md')
        # 建立臨時 HTML 檔案
        html_fd, html_path = tempfile.mkstemp(suffix='.html')
        
        # 關閉由 mkstemp 建立的檔案描述符
        os.close(md_fd)
        os.close(html_fd)
        
        # 使用 yield 將檔案路徑提供給測試函式
        yield md_path, html_path
        
        # --- 清理階段 ---
        # 測試結束後，刪除建立的臨時檔案
        for path in [md_path, html_path]:
            if os.path.exists(path):
                os.unlink(path)

    def test_convert_markdown_to_html_basic(self, temp_files, sample_markdown):
        """測試最基本的 Markdown 到 HTML 轉換功能。"""
        md_path, html_path = temp_files
        
        # 將範例 Markdown 內容寫入臨時檔案
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(sample_markdown)
        
        # 執行轉換函式
        convert_markdown_to_html(md_path, html_path)
        
        # 斷言 HTML 輸出檔案已建立
        assert os.path.exists(html_path)
        
        # 讀取轉換後的 HTML 內容
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 檢查 HTML 的基本結構
        assert '<!DOCTYPE html>' in html_content
        assert '<html' in html_content
        assert '<head>' in html_content
        assert '<body>' in html_content
        assert '</html>' in html_content
        
        # 檢查特定元素的轉換結果
        assert '<h1 id="_1">測試標題</h1>' in html_content
        assert '<h2 id="_2">子標題</h2>' in html_content
        assert '<h3 id="_3">表格測試</h3>' in html_content
        assert '<ul>' in html_content
        assert '<li>項目 1</li>' in html_content
        assert '<table>' in html_content
        assert '<th>模型</th>' in html_content
        assert '<td>llama2</td>' in html_content
        assert '<pre><code>' in html_content or '<code>' in html_content
        assert '<strong>粗體文字</strong>' in html_content
        assert '<em>斜體文字</em>' in html_content

    def test_convert_markdown_to_html_with_css(self, temp_files, sample_markdown):
        """測試轉換後的 HTML 是否包含內嵌的 CSS 樣式。"""
        md_path, html_path = temp_files
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(sample_markdown)
        
        convert_markdown_to_html(md_path, html_path)
        
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 斷言 HTML 中包含 <style> 標籤和一些基本的 CSS 規則
        assert '<style>' in html_content
        assert 'font-family' in html_content
        assert 'table' in html_content  # 檢查是否有表格樣式

    def test_convert_markdown_to_html_chinese_content(self, temp_files):
        """測試包含繁體中文內容的 Markdown 是否能正確轉換。"""
        md_path, html_path = temp_files
        
        chinese_markdown = '''# 中文標題測試

這是中文段落內容，包含各種標點符號：，。！？

## 評比結果

| 模型名稱 | 翻譯分數 | 摘要分數 | 平均分數 |
|----------|----------|----------|----------|
| 模型一 | 8.5 | 7.2 | 7.85 |
| 模型二 | 9.0 | 8.1 | 8.55 |

### 結論

**最佳模型**：模型二表現最優秀。
'''
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(chinese_markdown)
        
        convert_markdown_to_html(md_path, html_path)
        
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 斷言中文內容被正確地呈現在 HTML 中
        assert '中文標題測試' in html_content
        assert '評比結果' in html_content
        assert '模型一' in html_content
        assert '最佳模型' in html_content
        
        # 斷言 HTML 頭部包含 UTF-8 編碼聲明
        assert 'charset="UTF-8"' in html_content

    def test_convert_markdown_to_html_empty_file(self, temp_files):
        """測試當輸入的 Markdown 檔案為空時，是否能產生一個有效的空 HTML 檔案。"""
        md_path, html_path = temp_files
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write("")
        
        convert_markdown_to_html(md_path, html_path)
        
        assert os.path.exists(html_path)
        
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 斷言即使內容為空，HTML 的基本骨架依然存在
        assert '<!DOCTYPE html>' in html_content
        assert '<body>' in html_content

    def test_convert_markdown_to_html_file_not_found(self):
        """測試當指定的輸入檔案不存在時，是否會引發 FileNotFoundError。"""
        with pytest.raises(FileNotFoundError):
            convert_markdown_to_html("nonexistent.md", "output.html")

    def test_convert_markdown_to_html_permission_error(self, temp_files, sample_markdown):
        """測試當沒有權限寫入輸出檔案時，是否會引發 PermissionError。"""
        md_path, html_path = temp_files
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(sample_markdown)
        
        # 使用 patch 來模擬 open() 函式在寫入時拋出 PermissionError
        with patch('builtins.open', side_effect=PermissionError("Permission denied")) as mock_file:
            # 讓模擬函式只在寫入模式 ('w') 時拋出異常
            def side_effect(*args, **kwargs):
                if len(args) > 1 and 'w' in args[1]:
                    raise PermissionError("Permission denied")
                # 對於讀取操作，則正常返回一個 mock_open 物件
                return mock_open(read_data=sample_markdown)(*args, **kwargs)
            
            mock_file.side_effect = side_effect
            
            with pytest.raises(PermissionError):
                convert_markdown_to_html(md_path, html_path)

    def test_convert_markdown_to_html_with_images(self, temp_files):
        """測試包含圖片連結的 Markdown 是否能正確轉換成 <img> 標籤。"""
        md_path, html_path = temp_files
        
        markdown_with_images = '''# 報表標題

![評比結果圖表](chart_openai_gpt4.png)
'''
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(markdown_with_images)
        
        convert_markdown_to_html(md_path, html_path)
        
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 斷言 HTML 中包含 <img> 標籤，且 src 和 alt 屬性正確
        assert '<img' in html_content
        assert 'src="chart_openai_gpt4.png"' in html_content
        assert 'alt="評比結果圖表"' in html_content

    def test_convert_markdown_to_html_with_links(self, temp_files):
        """測試包含超連結的 Markdown 是否能正確轉換成 <a> 標籤。"""
        md_path, html_path = temp_files
        
        markdown_with_links = '''# 參考資料

- [OpenAI 官網](https://openai.com)
- [本地文件](./local_doc.md)
'''
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(markdown_with_links)
        
        convert_markdown_to_html(md_path, html_path)
        
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 斷言 HTML 中包含 <a> 標籤，且 href 屬性正確
        assert '<a href="https://openai.com">OpenAI 官網</a>' in html_content
        assert '<a href="./local_doc.md">本地文件</a>' in html_content

    def test_html_output_structure(self, temp_files, sample_markdown):
        """測試輸出的 HTML 檔案是否具有完整且正確的文檔結構。"""
        md_path, html_path = temp_files
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(sample_markdown)
        
        convert_markdown_to_html(md_path, html_path)
        
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 斷言 HTML 的主要標籤都存在且成對
        assert html_content.count('<html') == 1
        assert html_content.count('</html>') == 1
        assert html_content.count('<head>') == 1
        assert html_content.count('</head>') == 1
        assert html_content.count('<body>') == 1
        assert html_content.count('</body>') == 1
        
        # 斷言包含重要的 meta 標籤
        assert '<meta charset="UTF-8">' in html_content
        assert '<meta name="viewport"' in html_content


# --- 測試類別：TestMarkdown2HtmlIntegration ---

class TestMarkdown2HtmlIntegration:
    """整合測試，模擬更真實的使用場景。"""
    
    @pytest.fixture
    def temp_files(self):
        """為整合測試建立臨時檔案。"""
        # 使用 with 陳述式確保即使發生錯誤，檔案也能被正確關閉
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as md_file, \
             tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as html_file:
            md_path = md_file.name
            html_path = html_file.name
        
        yield md_path, html_path
        
        # 清理檔案
        for path in [md_path, html_path]:
            if os.path.exists(path):
                os.unlink(path)
    
    def test_full_report_conversion(self, temp_files):
        """測試一個模擬的、完整的評比報告 Markdown 檔案是否能成功轉換。"""
        md_path, html_path = temp_files
        
        # 模擬一個包含各種元素的完整 Markdown 報告
        full_report = '''# Ollama 模型評比報表

**生成時間**: 2024-01-01 12:00:00

## 評比概要

### 測試模型清單
1. `llama2`
2. `mistral`

### 評審模型
- **OPENAI**: `gpt-4`

## OPENAI (gpt-4) 評審結果

| 模型 | 翻譯分數 | 摘要分數 |
|------|----------|----------|
| `llama2` | 8 | 7 |
| `mistral` | 9 | 8 |

## 視覺化圖表

![評審結果圖表](chart.png)

## 模型輸出結果

### llama2

#### Translate 結果

```
你好，大家好...
```
'''
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(full_report)
        
        convert_markdown_to_html(md_path, html_path)
        
        assert os.path.exists(html_path)
        
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 抽樣檢查幾個關鍵部分是否被正確轉換
        assert 'Ollama 模型評比報表' in html_content
        assert '評比概要' in html_content
        assert '視覺化圖表' in html_content
        assert '<table>' in html_content
        assert '<td>llama2</td>' in html_content
        assert '<img' in html_content
        assert '<pre><code>' in html_content


# --- 主程式進入點 ---

if __name__ == "__main__":
    # 如果此檔案被直接執行，則使用 pytest 執行其中的測試
    pytest.main([__file__, "-v"]) 