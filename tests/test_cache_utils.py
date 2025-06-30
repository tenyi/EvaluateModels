#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
測試快取工具模組 cache_utils.py。

這個測試檔案旨在確保 `cache_utils` 中的函式能夠正確、穩定地運作。

主要測試內容：
- **快取鍵生成 (`get_cache_key`)**:
  - **一致性**: 同樣的參數是否總是產生相同的鍵。
  - **唯一性**: 不同的參數是否會產生不同的鍵。
  - **順序無關性**: 參數的順序不應影響最終的鍵值。
  - **特殊字元處理**: 包含中文或特殊符號的參數是否能正常處理。
- **快取存取 (`save_to_cache`, `load_from_cache`)**:
  - **存取流程**: 測試能否成功儲存資料，然後再成功地讀取出來。
  - **邊界情況**: 
    - 讀取一個不存在的快取鍵時，應回傳 `None`。
    - 當快取檔案損毀 (非有效 JSON) 時，應能妥善處理並回傳 `None`。
    - 當沒有權限寫入檔案時，程式不應崩潰。
- **整合測試**: 模擬一個完整的「生成鍵 -> 儲存 -> 讀取」流程。
"""

# 匯入必要的模組
import pytest
import tempfile
import os
import json
import shutil
from unittest.mock import patch
import sys

# 將專案根目錄加入 Python 的模組搜尋路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 從專案中匯入待測試的函式
from cache_utils import get_cache_key, load_from_cache, save_to_cache


# --- 測試類別：TestCacheUtils ---

class TestCacheUtils:
    """測試快取工具函式的核心功能。"""

    @pytest.fixture
    def temp_cache_dir(self):
        """建立一個臨時目錄作為測試期間的快取目錄，並在測試後自動清理。"""
        temp_dir = tempfile.mkdtemp(prefix="test_cache_")
        # 使用 yield 將目錄路徑提供給測試函式
        yield temp_dir
        # --- 清理階段 ---
        # 測試結束後，遞迴地刪除整個臨時目錄
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_get_cache_key_basic_properties(self):
        """測試 `get_cache_key` 生成的鍵是否具備基本屬性 (字串, 長度, 字元集)。"""
        params = {"model": "llama2", "text": "Hello"}
        cache_key = get_cache_key(params, prompt="")
        
        assert isinstance(cache_key, str), "快取鍵應為字串"
        assert len(cache_key) == 32, "快取鍵應為 32 個字元的 MD5 雜湊值"
        assert all(c in '0123456789abcdef' for c in cache_key), "快取鍵應只包含十六進位字元"

    def test_get_cache_key_consistency(self):
        """測試對於完全相同的參數，`get_cache_key` 是否總是生成相同的鍵。"""
        params = {"model": "llama2", "text": "Hello"}
        key1 = get_cache_key(params, prompt="")
        key2 = get_cache_key(params, prompt="")
        assert key1 == key2, "相同的參數應產生相同的快取鍵"

    def test_get_cache_key_is_sensitive_to_changes(self):
        """測試參數的任何微小變動是否都會導致生成不同的快取鍵。"""
        params1 = {"model": "llama2", "text": "Hello"}
        params2 = {"model": "llama2", "text": "hello"} # 大小寫不同
        key1 = get_cache_key(params1, prompt="")
        key2 = get_cache_key(params2, prompt="")
        assert key1 != key2, "不同的參數應產生不同的快取鍵"

    def test_get_cache_key_order_independence(self):
        """測試 `get_cache_key` 是否不受參數字典中鍵順序的影響。"""
        params1 = {"model": "llama2", "text": "Hello"}
        params2 = {"text": "Hello", "model": "llama2"}
        key1 = get_cache_key(params1, prompt="")
        key2 = get_cache_key(params2, prompt="")
        assert key1 == key2, "參數順序不應影響快取鍵的生成"

    def test_get_cache_key_with_complex_data(self):
        """測試 `get_cache_key` 處理包含中文、特殊字元、巢狀結構的參數。"""
        params = {
            "task": "翻譯",
            "config": {"temperature": 0.5, "tags": ["test", "api"]},
            "text": "你好, world!@#$%"
        }
        try:
            cache_key = get_cache_key(params, prompt="")
            assert isinstance(cache_key, str)
            assert len(cache_key) == 32
        except Exception as e:
            pytest.fail(f"處理複雜資料時 `get_cache_key` 不應拋出錯誤: {e}")

    @patch('cache_utils.CACHE_DIR')
    def test_save_and_load_integration(self, mock_cache_dir_path, temp_cache_dir):
        """整合測試：模擬一次完整的儲存和讀取流程。"""
        # 將 cache_utils 中的 CACHE_DIR 常數指向我們的臨時目錄
        mock_cache_dir_path.return_value = temp_cache_dir
        
        cache_key = "my_integration_test_key"
        content = "這是要快取的內容。"
        
        # 在 patch 的上下文中執行，確保 CACHE_DIR 被正確替換
        with patch('cache_utils.CACHE_DIR', temp_cache_dir):
            # 1. 測試儲存
            save_to_cache(cache_key, content)
            
            # 檢查實體檔案是否已建立
            expected_file = os.path.join(temp_cache_dir, f"{cache_key}.json")
            assert os.path.exists(expected_file), "`save_to_cache` 應建立一個 .json 檔案"
            
            # 檢查檔案內容是否正確
            with open(expected_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                assert data.get('content') == content
                assert 'timestamp' in data

            # 2. 測試讀取
            loaded_content = load_from_cache(cache_key)
            assert loaded_content == content, "`load_from_cache` 應能讀取已儲存的內容"

    @patch('cache_utils.CACHE_DIR')
    def test_load_from_cache_not_found(self, mock_cache_dir_path, temp_cache_dir):
        """測試當快取鍵不存在時，`load_from_cache` 是否回傳 None。"""
        with patch('cache_utils.CACHE_DIR', temp_cache_dir):
            result = load_from_cache("a_non_existent_key")
        assert result is None, "對於不存在的鍵，應回傳 None"

    @patch('cache_utils.CACHE_DIR')
    def test_load_from_cache_invalid_json(self, mock_cache_dir_path, temp_cache_dir):
        """測試當快取檔案內容不是有效的 JSON 時，`load_from_cache` 的處理。"""
        cache_key = "invalid_json_key"
        with patch('cache_utils.CACHE_DIR', temp_cache_dir):
            # 建立一個損壞的快取檔案
            cache_file = os.path.join(temp_cache_dir, f"{cache_key}.json")
            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write("this is not valid json")
            
            # 嘗試讀取這個損壞的檔案
            result = load_from_cache(cache_key)
        
        assert result is None, "當快取檔案損毀時，應回傳 None"

    def test_get_cache_key_sensitive_to_prompt_changes(self):
        """測試 `get_cache_key` 是否對提示詞的變動敏感。"""
        params = {"model": "llama2", "text": "Hello"}
        prompt1 = "Summarize the following text."
        prompt2 = "Translate the following text to Chinese."
        
        key1 = get_cache_key(params, prompt=prompt1)
        key2 = get_cache_key(params, prompt=prompt2)
        
        assert key1 != key2, "不同的提示詞應產生不同的快取鍵"

    @patch('os.makedirs')
    @patch('builtins.open')
    def test_save_to_cache_handles_os_error(self, mock_open, mock_makedirs):
        """測試 `save_to_cache` 在建立目錄或檔案失敗時，不會讓程式崩潰。"""
        # 模擬建立目錄時發生 PermissionError
        mock_makedirs.side_effect = OSError("Cannot create directory")
        
        try:
            # 即使發生作業系統錯誤，函式也應該靜默處理，不應拋出例外
            save_to_cache("any_key", "any_data")
        except Exception as e:
            pytest.fail(f"當建立目錄失敗時，`save_to_cache` 不應拋出錯誤: {e}")


# --- 主程式進入點 ---

if __name__ == "__main__":
    # 如果此檔案被直接執行，則使用 pytest 執行其中的測試
    pytest.main([__file__, "-v"]) 