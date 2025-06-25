#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
import tempfile
import os
from unittest.mock import patch, mock_open
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from markdown2html import convert_markdown_to_html


class TestMarkdown2Html:
    """測試 Markdown 轉 HTML 功能"""

    @pytest.fixture
    def sample_markdown(self):
        """範例 Markdown 內容"""
        return """# 測試標題

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
"""

    @pytest.fixture
    def temp_files(self):
        """建立臨時檔案"""
        # 建立臨時 Markdown 檔案
        md_fd, md_path = tempfile.mkstemp(suffix='.md')
        html_fd, html_path = tempfile.mkstemp(suffix='.html')
        
        # 關閉檔案描述符
        os.close(md_fd)
        os.close(html_fd)
        
        yield md_path, html_path
        
        # 清理
        for path in [md_path, html_path]:
            if os.path.exists(path):
                os.unlink(path)

    def test_convert_markdown_to_html_basic(self, temp_files, sample_markdown):
        """測試基本 Markdown 轉 HTML 功能"""
        md_path, html_path = temp_files
        
        # 寫入 Markdown 內容
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(sample_markdown)
        
        # 執行轉換
        convert_markdown_to_html(md_path, html_path)
        
        # 檢查 HTML 檔案是否存在
        assert os.path.exists(html_path)
        
        # 讀取並檢查 HTML 內容
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 檢查基本 HTML 結構
        assert '<!DOCTYPE html>' in html_content
        assert '<html' in html_content
        assert '<head>' in html_content
        assert '<body>' in html_content
        assert '</html>' in html_content
        
        # 檢查標題轉換（標題會有 id 屬性）
        assert '<h1 id="_1">測試標題</h1>' in html_content
        assert '<h2 id="_2">子標題</h2>' in html_content
        assert '<h3 id="_3">表格測試</h3>' in html_content
        
        # 檢查列表轉換
        assert '<ul>' in html_content
        assert '<li>項目 1</li>' in html_content
        
        # 檢查表格轉換
        assert '<table>' in html_content
        assert '<th>模型</th>' in html_content
        assert '<td>llama2</td>' in html_content
        
        # 檢查程式碼區塊
        assert '<pre><code>' in html_content or '<code>' in html_content
        
        # 檢查格式化文字
        assert '<strong>粗體文字</strong>' in html_content
        assert '<em>斜體文字</em>' in html_content

    def test_convert_markdown_to_html_with_css(self, temp_files, sample_markdown):
        """測試包含 CSS 樣式的 HTML 轉換"""
        md_path, html_path = temp_files
        
        # 寫入 Markdown 內容
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(sample_markdown)
        
        # 執行轉換
        convert_markdown_to_html(md_path, html_path)
        
        # 讀取 HTML 內容
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 檢查是否包含 CSS 樣式
        assert '<style>' in html_content
        assert 'font-family' in html_content
        assert 'table' in html_content  # 表格樣式

    def test_convert_markdown_to_html_chinese_content(self, temp_files):
        """測試中文內容的轉換"""
        md_path, html_path = temp_files
        
        chinese_markdown = """# 中文標題測試

這是中文段落內容，包含各種標點符號：，。！？

## 評比結果

| 模型名稱 | 翻譯分數 | 摘要分數 | 平均分數 |
|----------|----------|----------|----------|
| 模型一 | 8.5 | 7.2 | 7.85 |
| 模型二 | 9.0 | 8.1 | 8.55 |

### 結論

**最佳模型**：模型二表現最優秀。
"""
        
        # 寫入中文 Markdown 內容
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(chinese_markdown)
        
        # 執行轉換
        convert_markdown_to_html(md_path, html_path)
        
        # 讀取並檢查 HTML 內容
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 檢查中文內容是否正確轉換
        assert '中文標題測試' in html_content
        assert '評比結果' in html_content
        assert '模型一' in html_content
        assert '最佳模型' in html_content
        
        # 檢查 UTF-8 編碼聲明
        assert 'charset="UTF-8"' in html_content

    def test_convert_markdown_to_html_empty_file(self, temp_files):
        """測試空檔案的轉換"""
        md_path, html_path = temp_files
        
        # 建立空的 Markdown 檔案
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write("")
        
        # 執行轉換
        convert_markdown_to_html(md_path, html_path)
        
        # 檢查 HTML 檔案是否存在且包含基本結構
        assert os.path.exists(html_path)
        
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        assert '<!DOCTYPE html>' in html_content
        assert '<html' in html_content
        assert '<body>' in html_content

    def test_convert_markdown_to_html_file_not_found(self):
        """測試輸入檔案不存在的情況"""
        with pytest.raises(FileNotFoundError):
            convert_markdown_to_html("nonexistent.md", "output.html")

    def test_convert_markdown_to_html_permission_error(self, temp_files, sample_markdown):
        """測試輸出檔案權限錯誤"""
        md_path, html_path = temp_files
        
        # 寫入 Markdown 內容
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(sample_markdown)
        
        # 模擬權限錯誤
        with patch('builtins.open', side_effect=PermissionError("Permission denied")) as mock_file:
            # 只對寫入操作拋出異常，讀取操作正常
            def side_effect(*args, **kwargs):
                if len(args) > 1 and 'w' in args[1]:
                    raise PermissionError("Permission denied")
                return mock_open(read_data=sample_markdown)(*args, **kwargs)
            
            mock_file.side_effect = side_effect
            
            with pytest.raises(PermissionError):
                convert_markdown_to_html(md_path, html_path)

    def test_convert_markdown_to_html_with_images(self, temp_files):
        """測試包含圖片的 Markdown 轉換"""
        md_path, html_path = temp_files
        
        markdown_with_images = """# 報表標題

## 圖表展示

![評比結果圖表](chart_openai_gpt4.png)

以上是評比結果的視覺化圖表。

![另一個圖表](chart_gemini_pro.png)
"""
        
        # 寫入包含圖片的 Markdown 內容
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(markdown_with_images)
        
        # 執行轉換
        convert_markdown_to_html(md_path, html_path)
        
        # 讀取並檢查 HTML 內容
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 檢查圖片是否正確轉換
        assert '<img' in html_content
        assert 'chart_openai_gpt4.png' in html_content
        assert 'chart_gemini_pro.png' in html_content
        assert 'alt="評比結果圖表"' in html_content

    def test_convert_markdown_to_html_with_links(self, temp_files):
        """測試包含連結的 Markdown 轉換"""
        md_path, html_path = temp_files
        
        markdown_with_links = """# 參考資料

請參考以下連結：

- [OpenAI 官網](https://openai.com)
- [Google AI](https://ai.google.com)
- [本地文件](./local_doc.md)
"""
        
        # 寫入包含連結的 Markdown 內容
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(markdown_with_links)
        
        # 執行轉換
        convert_markdown_to_html(md_path, html_path)
        
        # 讀取並檢查 HTML 內容
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 檢查連結是否正確轉換
        assert '<a href="https://openai.com">OpenAI 官網</a>' in html_content
        assert '<a href="https://ai.google.com">Google AI</a>' in html_content
        assert '<a href="./local_doc.md">本地文件</a>' in html_content

    def test_convert_markdown_to_html_complex_table(self, temp_files):
        """測試複雜表格的轉換"""
        md_path, html_path = temp_files
        
        complex_table_markdown = """# 複雜表格測試

| 模型 | 翻譯分數 | 翻譯評語 | 摘要分數 | 摘要評語 | 平均分數 |
|------|----------|----------|----------|----------|----------|
| llama2 | 8.5 | 翻譯準確，語法流暢 | 7.2 | 重點明確但稍簡略 | 7.85 |
| mistral | 9.0 | 翻譯優秀，用詞恰當 | 8.1 | 摘要完整且條理清楚 | 8.55 |
| gemma | 7.8 | 翻譯基本準確 | 8.5 | 摘要詳細且重點突出 | 8.15 |
"""
        
        # 寫入複雜表格 Markdown 內容
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(complex_table_markdown)
        
        # 執行轉換
        convert_markdown_to_html(md_path, html_path)
        
        # 讀取並檢查 HTML 內容
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 檢查表格結構
        assert '<table>' in html_content
        assert '<thead>' in html_content
        assert '<tbody>' in html_content
        assert '<th>模型</th>' in html_content
        assert '<th>翻譯分數</th>' in html_content
        assert '<td>llama2</td>' in html_content
        assert '<td>8.5</td>' in html_content
        assert '翻譯準確，語法流暢' in html_content

    def test_html_output_structure(self, temp_files, sample_markdown):
        """測試 HTML 輸出結構的完整性"""
        md_path, html_path = temp_files
        
        # 寫入 Markdown 內容
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(sample_markdown)
        
        # 執行轉換
        convert_markdown_to_html(md_path, html_path)
        
        # 讀取 HTML 內容
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 檢查 HTML 文檔結構完整性
        assert html_content.count('<html') == 1
        assert html_content.count('</html>') == 1
        assert html_content.count('<head>') == 1
        assert html_content.count('</head>') == 1
        assert html_content.count('<body>') == 1
        assert html_content.count('</body>') == 1
        
        # 檢查 meta 標籤
        assert '<meta charset="UTF-8">' in html_content
        assert '<meta name="viewport"' in html_content


class TestMarkdown2HtmlIntegration:
    """整合測試"""
    
    @pytest.fixture
    def temp_files(self):
        """建立臨時檔案用於測試"""
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
        """測試完整報表的轉換"""
        md_path, html_path = temp_files
        
        # 模擬完整的評比報表
        full_report = """# Ollama 模型評比報表

**生成時間**: 2024-01-01 12:00:00

## 評比概要

本次評比測試了 3 個 Ollama 模型在兩個任務上的表現：
- **翻譯任務** (Translate): 英文翻譯為繁體中文
- **摘要任務** (Summarize): 會議記錄摘要

### 測試模型清單
1. `llama2`
2. `mistral`
3. `gemma`

### 評審模型
- **OPENAI**: `gpt-4`
- **GEMINI**: `gemini-pro`

## OPENAI (gpt-4) 評審結果

| 模型 | 翻譯分數 | 翻譯評語 | 摘要分數 | 摘要評語 | 平均分數 |
|------|----------|----------|----------|----------|----------|
| `llama2` | 8 | 翻譯準確且流暢 | 7 | 摘要重點明確 | 7.5 |
| `mistral` | 9 | 翻譯優秀 | 8 | 摘要完整 | 8.5 |
| `gemma` | 7 | 翻譯基本準確 | 8 | 摘要詳細 | 7.5 |

## 統計分析

### OPENAI (gpt-4) 評審統計

- **翻譯任務平均分數**: 8.00
- **翻譯任務最高分**: 9
- **翻譯任務最低分**: 7
- **摘要任務平均分數**: 7.67
- **摘要任務最高分**: 8
- **摘要任務最低分**: 7

## 視覺化圖表

### OPENAI (gpt-4) 評審結果圖表

![OPENAI (gpt-4) 評審結果](chart_openai_gpt_4_202401011200.png)

## 模型輸出結果

### llama2

#### Translate 結果

```
你好，大家好，感謝您的參與...
```

#### Summarize 結果

```
本次會議討論了從 VMware 遷移到 Charmed OpenStack 的相關議題...
```
"""
        
        # 寫入完整報表內容
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(full_report)
        
        # 執行轉換
        convert_markdown_to_html(md_path, html_path)
        
        # 檢查轉換結果
        assert os.path.exists(html_path)
        
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 檢查各個部分是否正確轉換
        assert 'Ollama 模型評比報表' in html_content
        assert '評比概要' in html_content
        assert '統計分析' in html_content
        assert '視覺化圖表' in html_content
        assert '模型輸出結果' in html_content
        
        # 檢查表格
        assert '<table>' in html_content
        assert 'llama2' in html_content
        assert '翻譯準確且流暢' in html_content
        
        # 檢查程式碼區塊
        assert '<pre><code>' in html_content or '<code>' in html_content
        assert '你好，大家好' in html_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 