#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
import tempfile
import os
import json
import shutil
from unittest.mock import patch, mock_open
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cache_utils import get_cache_key, load_from_cache, save_to_cache


class TestCacheUtils:
    """測試快取工具函數"""

    @pytest.fixture
    def temp_cache_dir(self):
        """建立臨時快取目錄"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # 清理
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_get_cache_key_basic(self):
        """測試基本快取鍵生成"""
        params = {
            "provider": "ollama",
            "model": "llama2",
            "task": "translate",
            "text": "Hello world"
        }
        
        cache_key = get_cache_key(params)
        
        # 檢查回傳值是字串
        assert isinstance(cache_key, str)
        # 檢查長度合理（MD5 hash 長度為 32）
        assert len(cache_key) == 32
        # 檢查只包含十六進位字符
        assert all(c in '0123456789abcdef' for c in cache_key)

    def test_get_cache_key_consistency(self):
        """測試快取鍵一致性"""
        params = {
            "provider": "ollama",
            "model": "llama2", 
            "task": "translate",
            "text": "Hello world"
        }
        
        key1 = get_cache_key(params)
        key2 = get_cache_key(params)
        
        # 相同參數應該產生相同的快取鍵
        assert key1 == key2

    def test_get_cache_key_different_params(self):
        """測試不同參數產生不同快取鍵"""
        params1 = {
            "provider": "ollama",
            "model": "llama2",
            "task": "translate",
            "text": "Hello world"
        }
        
        params2 = {
            "provider": "ollama",
            "model": "llama2",
            "task": "translate", 
            "text": "Hello world!"  # 不同的文字
        }
        
        key1 = get_cache_key(params1)
        key2 = get_cache_key(params2)
        
        # 不同參數應該產生不同的快取鍵
        assert key1 != key2

    def test_get_cache_key_order_independence(self):
        """測試參數順序不影響快取鍵"""
        params1 = {
            "provider": "ollama",
            "model": "llama2",
            "task": "translate",
            "text": "Hello world"
        }
        
        params2 = {
            "text": "Hello world",
            "task": "translate",
            "model": "llama2",
            "provider": "ollama"
        }
        
        key1 = get_cache_key(params1)
        key2 = get_cache_key(params2)
        
        # 參數順序不同但內容相同，應該產生相同的快取鍵
        assert key1 == key2

    @patch('cache_utils.CACHE_DIR')
    def test_save_to_cache_success(self, mock_cache_dir, temp_cache_dir):
        """測試成功儲存快取"""
        mock_cache_dir.__str__ = lambda: temp_cache_dir
        mock_cache_dir.__fspath__ = lambda: temp_cache_dir
        
        cache_key = "test_cache_key"
        content = "This is test content"
        
        with patch('cache_utils.CACHE_DIR', temp_cache_dir):
            save_to_cache(cache_key, content)
        
        # 檢查檔案是否被建立
        cache_file = os.path.join(temp_cache_dir, f"{cache_key}.json")
        assert os.path.exists(cache_file)
        
        # 檢查檔案內容
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            assert data['content'] == content
            assert 'timestamp' in data

    @patch('cache_utils.CACHE_DIR')
    def test_load_from_cache_success(self, mock_cache_dir, temp_cache_dir):
        """測試成功載入快取"""
        mock_cache_dir.__str__ = lambda: temp_cache_dir
        mock_cache_dir.__fspath__ = lambda: temp_cache_dir
        
        cache_key = "test_cache_key"
        content = "This is cached content"
        
        # 先儲存快取
        with patch('cache_utils.CACHE_DIR', temp_cache_dir):
            save_to_cache(cache_key, content)
            
            # 載入快取
            loaded_content = load_from_cache(cache_key)
        
        assert loaded_content == content

    @patch('cache_utils.CACHE_DIR')
    def test_load_from_cache_not_found(self, mock_cache_dir, temp_cache_dir):
        """測試載入不存在的快取"""
        mock_cache_dir.__str__ = lambda: temp_cache_dir
        mock_cache_dir.__fspath__ = lambda: temp_cache_dir
        
        with patch('cache_utils.CACHE_DIR', temp_cache_dir):
            result = load_from_cache("nonexistent_key")
        
        assert result is None

    @patch('cache_utils.CACHE_DIR')
    def test_load_from_cache_invalid_json(self, mock_cache_dir, temp_cache_dir):
        """測試載入損壞的快取檔案"""
        mock_cache_dir.__str__ = lambda: temp_cache_dir
        mock_cache_dir.__fspath__ = lambda: temp_cache_dir
        
        cache_key = "invalid_cache_key"
        cache_file = os.path.join(temp_cache_dir, f"{cache_key}.json")
        
        # 建立損壞的 JSON 檔案
        with open(cache_file, 'w', encoding='utf-8') as f:
            f.write("invalid json content")
        
        with patch('cache_utils.CACHE_DIR', temp_cache_dir):
            result = load_from_cache(cache_key)
        
        assert result is None

    @patch('builtins.open', side_effect=PermissionError("Permission denied"))
    def test_save_to_cache_permission_error(self, mock_open):
        """測試快取儲存權限錯誤"""
        # 應該不會拋出異常，而是靜默失敗
        save_to_cache("test_key", "test_content")
        # 如果沒有拋出異常就表示測試通過

    def test_cache_key_with_chinese_text(self):
        """測試包含中文的快取鍵生成"""
        params = {
            "provider": "ollama",
            "model": "llama2",
            "task": "translate",
            "text": "你好世界"
        }
        
        cache_key = get_cache_key(params)
        
        # 檢查能正常生成快取鍵
        assert isinstance(cache_key, str)
        assert len(cache_key) == 32

    def test_cache_key_with_special_characters(self):
        """測試包含特殊字符的快取鍵生成"""
        params = {
            "provider": "ollama",
            "model": "llama2",
            "task": "translate",
            "text": "Hello! @#$%^&*()_+-=[]{}|;':\",./<>?"
        }
        
        cache_key = get_cache_key(params)
        
        # 檢查能正常生成快取鍵
        assert isinstance(cache_key, str)
        assert len(cache_key) == 32

    @patch('cache_utils.CACHE_DIR')
    def test_cache_integration(self, mock_cache_dir, temp_cache_dir):
        """整合測試：完整的快取流程"""
        mock_cache_dir.__str__ = lambda: temp_cache_dir
        mock_cache_dir.__fspath__ = lambda: temp_cache_dir
        
        # 測試參數
        params = {
            "provider": "ollama",
            "model": "llama2",
            "task": "translate",
            "text": "Hello world"
        }
        
        content = "你好世界"
        
        with patch('cache_utils.CACHE_DIR', temp_cache_dir):
            # 1. 生成快取鍵
            cache_key = get_cache_key(params)
            
            # 2. 確認快取未存在
            assert load_from_cache(cache_key) is None
            
            # 3. 儲存快取
            save_to_cache(cache_key, content)
            
            # 4. 載入快取
            loaded_content = load_from_cache(cache_key)
            assert loaded_content == content
            
            # 5. 檢查檔案系統
            cache_file = os.path.join(temp_cache_dir, f"{cache_key}.json")
            assert os.path.exists(cache_file)

    def test_cache_key_with_nested_dict(self):
        """測試包含巢狀字典的參數"""
        params = {
            "provider": "openai",
            "model": "gpt-4",
            "config": {
                "temperature": 0.1,
                "max_tokens": 1000
            },
            "text": "Hello world"
        }
        
        cache_key = get_cache_key(params)
        
        # 檢查能正常生成快取鍵
        assert isinstance(cache_key, str)
        assert len(cache_key) == 32

    def test_cache_key_with_list_params(self):
        """測試包含列表的參數"""
        params = {
            "provider": "ollama",
            "models": ["llama2", "mistral"],
            "tasks": ["translate", "summarize"],
            "text": "Hello world"
        }
        
        cache_key = get_cache_key(params)
        
        # 檢查能正常生成快取鍵
        assert isinstance(cache_key, str)
        assert len(cache_key) == 32


class TestCachePerformance:
    """測試快取效能"""
    
    def test_cache_key_generation_performance(self):
        """測試快取鍵生成效能"""
        import time
        
        params = {
            "provider": "ollama",
            "model": "llama2",
            "task": "translate",
            "text": "Hello world" * 1000  # 長文字
        }
        
        start_time = time.time()
        for _ in range(100):
            get_cache_key(params)
        end_time = time.time()
        
        # 100 次快取鍵生成應該在 1 秒內完成
        assert (end_time - start_time) < 1.0

    @patch('cache_utils.CACHE_DIR')
    def test_cache_large_content(self, mock_cache_dir, temp_cache_dir):
        """測試大型內容的快取"""
        mock_cache_dir.__str__ = lambda: temp_cache_dir
        mock_cache_dir.__fspath__ = lambda: temp_cache_dir
        
        cache_key = "large_content_key"
        large_content = "A" * 10000  # 10KB 內容
        
        with patch('cache_utils.CACHE_DIR', temp_cache_dir):
            save_to_cache(cache_key, large_content)
            loaded_content = load_from_cache(cache_key)
        
        assert loaded_content == large_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 