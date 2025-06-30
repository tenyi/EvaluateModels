#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
測試主程式 main.py 中的 ModelEvaluator 類別。

這個測試檔案使用 pytest 和 unittest.mock 來對 `ModelEvaluator` 的各個方法
進行單元測試和整合測試。

主要測試內容：
- **初始化**：檢查 `ModelEvaluator` 實例是否能正確建立。
- **檔案讀取**：測試 `read_input_text` 方法能否成功讀取檔案，以及能否處理檔案不存在等錯誤情況。
- **API 呼叫**：
  - 模擬對 Ollama, OpenAI, Google API 的呼叫，測試成功、失敗、超時和快取等情境。
  - 使用 `@patch` 裝飾器來攔截和模擬外部依賴 (如 `requests.post`, `openai.OpenAI` 等)。
- **評審邏輯**：測試 `evaluate_with_reviewer` 方法能否正確解析評審模型的回應，並處理格式錯誤等問題。
- **報告生成**：測試 `create_charts` 和 `create_markdown_report` 能否根據模擬資料產生預期的圖表和報告內容。
- **完整流程**：測試 `run_evaluation` 和 `generate_report` 能否串連所有步驟，順利執行。
- **整合測試**：測試與真實檔案系統 (臨時檔案) 和快取機制的互動。
"""

# 匯入必要的模組
import pytest
import unittest.mock as mock
import tempfile
import os
import json
from unittest.mock import patch, MagicMock, mock_open
import sys

# 將專案根目錄加入 Python 的模組搜尋路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 從主程式匯入待測試的類別
from main import ModelEvaluator


# --- 測試類別：TestModelEvaluator (單元測試) ---

class TestModelEvaluator:
    """針對 ModelEvaluator 類別的各個方法進行單元測試。"""

    @pytest.fixture
    def evaluator(self):
        """提供一個 ModelEvaluator 的乾淨實例給每個測試函式。"""
        return ModelEvaluator()

    @pytest.fixture
    def sample_input_text(self):
        """提供一段用於測試的範例輸入文字。"""
        return 