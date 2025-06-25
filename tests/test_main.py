#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
import unittest.mock as mock
import tempfile
import os
import json
from unittest.mock import patch, MagicMock, mock_open
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import ModelEvaluator


class TestModelEvaluator:
    """測試 ModelEvaluator 類別"""

    @pytest.fixture
    def evaluator(self):
        """建立 ModelEvaluator 實例"""
        return ModelEvaluator()

    @pytest.fixture
    def sample_input_text(self):
        """範例輸入文字"""
        return "Hello world. This is a test document for translation and summarization."

    def test_init(self, evaluator):
        """測試初始化"""
        assert evaluator.results == {}
        assert evaluator.evaluation_scores == {}

    def test_read_input_text_success(self, evaluator):
        """測試成功讀取輸入檔案"""
        test_content = "Test content for evaluation"
        
        with patch("builtins.open", mock_open(read_data=test_content)):
            result = evaluator.read_input_text("test_input.txt")
            assert result == test_content

    def test_read_input_text_file_not_found(self, evaluator):
        """測試檔案不存在的情況"""
        with patch("builtins.open", side_effect=FileNotFoundError):
            with pytest.raises(SystemExit):
                evaluator.read_input_text("nonexistent.txt")

    def test_read_input_text_other_error(self, evaluator):
        """測試其他讀取錯誤"""
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            with pytest.raises(SystemExit):
                evaluator.read_input_text("test.txt")

    @patch('main.requests.post')
    @patch('main.load_from_cache')
    @patch('main.save_to_cache')
    def test_call_ollama_api_success(self, mock_save_cache, mock_load_cache, mock_post, evaluator):
        """測試成功呼叫 Ollama API"""
        # 設定快取未命中
        mock_load_cache.return_value = None
        
        # 模擬 API 回應
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "message": {"content": "This is the translated text."}
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = evaluator.call_ollama_api("llama2", "translate", "Hello world")
        
        assert result == "This is the translated text."
        mock_save_cache.assert_called_once()

    @patch('main.requests.post')
    @patch('main.load_from_cache')
    def test_call_ollama_api_cached(self, mock_load_cache, mock_post, evaluator):
        """測試從快取載入 Ollama API 結果"""
        cached_result = "Cached translation result"
        mock_load_cache.return_value = cached_result
        
        result = evaluator.call_ollama_api("llama2", "translate", "Hello world")
        
        assert result == cached_result
        # 確保沒有呼叫 API
        mock_post.assert_not_called()

    @patch('main.requests.post')
    @patch('main.load_from_cache')
    def test_call_ollama_api_timeout(self, mock_load_cache, mock_post, evaluator):
        """測試 Ollama API 超時"""
        import requests
        mock_load_cache.return_value = None
        mock_post.side_effect = requests.exceptions.Timeout()

        result = evaluator.call_ollama_api("llama2", "translate", "Hello world")
        
        assert result == "ERROR: 回應超時"

    @patch('main.requests.post')
    @patch('main.load_from_cache')
    def test_call_ollama_api_request_error(self, mock_load_cache, mock_post, evaluator):
        """測試 Ollama API 請求錯誤"""
        import requests
        mock_load_cache.return_value = None
        mock_post.side_effect = requests.exceptions.RequestException("Connection error")

        result = evaluator.call_ollama_api("llama2", "translate", "Hello world")
        
        assert result.startswith("ERROR: API 呼叫失敗")

    @patch('main.OpenAI')
    @patch('main.load_from_cache')
    @patch('main.save_to_cache')
    @patch('main.OPENAI_API_KEY', 'test-api-key')
    def test_call_openai_api_success(self, mock_save_cache, mock_load_cache, mock_openai_class, evaluator):
        """測試成功呼叫 OpenAI API"""
        mock_load_cache.return_value = None
        
        # 模擬 OpenAI 客戶端和回應
        mock_client = MagicMock()
        mock_openai_class.return_value.__enter__.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "This is the OpenAI response."
        mock_client.chat.completions.create.return_value = mock_response

        result = evaluator.call_openai_api(
            "gpt-4", "You are a translator", "Translate this text", is_reviewer=False
        )
        
        assert result == "This is the OpenAI response."
        mock_save_cache.assert_called_once()

    @patch('main.OPENAI_API_KEY', 'your_openai_api_key_here')
    def test_call_openai_api_no_key(self, evaluator):
        """測試未設定 OpenAI API 金鑰"""
        result = evaluator.call_openai_api(
            "gpt-4", "System prompt", "User content"
        )
        
        assert result == "ERROR: OpenAI API 金鑰未設定"

    @patch('main.requests.post')
    @patch('main.load_from_cache')
    @patch('main.save_to_cache')
    @patch('main.GOOGLE_API_KEY', 'test-google-key')
    def test_call_google_api_success(self, mock_save_cache, mock_load_cache, mock_post, evaluator):
        """測試成功呼叫 Google API"""
        mock_load_cache.return_value = None
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "Google API response"}]}}]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = evaluator.call_google_api(
            "gemini-pro", "System prompt", "User content"
        )
        
        assert result == "Google API response"
        mock_save_cache.assert_called_once()

    @patch('main.GOOGLE_API_KEY', 'your_google_api_key_here')
    def test_call_google_api_no_key(self, evaluator):
        """測試未設定 Google API 金鑰"""
        result = evaluator.call_google_api(
            "gemini-pro", "System prompt", "User content"
        )
        
        assert result == "ERROR: Google API 金鑰未設定"

    def test_evaluate_with_reviewer_translate_task(self, evaluator):
        """測試翻譯任務評審"""
        # 模擬評審回應
        mock_response = "分數: 8\n評語: 翻譯準確且流暢"
        
        with patch.object(evaluator, 'call_openai_api', return_value=mock_response):
            score, comment = evaluator.evaluate_with_reviewer(
                "openai", "gpt-4", "translate", "Hello world", "你好世界"
            )
            
            assert score == 8
            assert comment == "翻譯準確且流暢"

    def test_evaluate_with_reviewer_summarize_task(self, evaluator):
        """測試摘要任務評審"""
        mock_response = "分數: 7\n評語: 摘要重點明確但稍嫌簡略"
        
        with patch.object(evaluator, 'call_openai_api', return_value=mock_response):
            score, comment = evaluator.evaluate_with_reviewer(
                "openai", "gpt-4", "summarize", "Long text...", "Short summary"
            )
            
            assert score == 7
            assert comment == "摘要重點明確但稍嫌簡略"

    def test_evaluate_with_reviewer_parse_error(self, evaluator):
        """測試評審回應解析錯誤"""
        mock_response = "Invalid response format"
        
        with patch.object(evaluator, 'call_openai_api', return_value=mock_response):
            score, comment = evaluator.evaluate_with_reviewer(
                "openai", "gpt-4", "translate", "Hello", "你好"
            )
            
            assert score == 1  # 預設分數（因為 max(1, min(10, 0)) = 1）
            assert comment.startswith("解析失敗:")

    def test_evaluate_with_reviewer_unsupported_type(self, evaluator):
        """測試不支援的評審模型類型"""
        score, comment = evaluator.evaluate_with_reviewer(
            "unsupported", "model", "translate", "Hello", "你好"
        )
        
        assert score == 0
        assert comment == "ERROR: 不支援的評審模型類型"

    @patch('main.OLLAMA_MODELS_TO_COMPARE', ['llama2'])
    @patch('main.SUPPORTED_TASKS', {'translate': 'Translate to Chinese'})
    @patch('main.REVIEWER_MODELS', [{'provider': 'openai', 'model': 'gpt-4'}])
    def test_run_evaluation_basic(self, evaluator, sample_input_text):
        """測試基本評比流程"""
        with patch.object(evaluator, 'read_input_text', return_value=sample_input_text), \
             patch.object(evaluator, 'call_ollama_api', return_value="翻譯結果"), \
             patch.object(evaluator, 'evaluate_with_reviewer', return_value=(8, "良好")), \
             patch('time.sleep'):  # 跳過延遲
            
            evaluator.run_evaluation()
            
            # 檢查結果結構
            assert 'llama2' in evaluator.results
            assert 'translate' in evaluator.results['llama2']
            assert evaluator.results['llama2']['translate'] == "翻譯結果"
            
            # 檢查評分結構
            assert 'openai_gpt_4' in evaluator.evaluation_scores
            assert 'llama2' in evaluator.evaluation_scores['openai_gpt_4']
            assert 'translate' in evaluator.evaluation_scores['openai_gpt_4']['llama2']

    @patch('main.datetime')
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_create_charts(self, mock_close, mock_savefig, mock_datetime, evaluator):
        """測試圖表生成"""
        # 設定測試數據
        evaluator.evaluation_scores = {
            'openai_gpt_4': {
                'llama2': {
                    'translate': {'score': 8},
                    'summarize': {'score': 7}
                }
            }
        }
        
        mock_datetime.now.return_value.strftime.return_value = "202401011200"
        
        with patch('main.OLLAMA_MODELS_TO_COMPARE', ['llama2']), \
             patch('main.REVIEWER_MODELS', [{'provider': 'openai', 'model': 'gpt-4'}]):
            
            evaluator.create_charts("202401011200")
            
            mock_savefig.assert_called()
            mock_close.assert_called()

    def test_create_markdown_report(self, evaluator):
        """測試 Markdown 報表生成"""
        # 設定測試數據
        evaluator.results = {
            'llama2': {
                'translate': '你好世界',
                'summarize': '這是摘要'
            }
        }
        
        evaluator.evaluation_scores = {
            'openai_gpt_4': {
                'llama2': {
                    'translate': {'score': 8, 'comment': '翻譯良好'},
                    'summarize': {'score': 7, 'comment': '摘要清楚'}
                }
            }
        }
        
        with patch('main.OLLAMA_MODELS_TO_COMPARE', ['llama2']), \
             patch('main.REVIEWER_MODELS', [{'provider': 'openai', 'model': 'gpt-4'}]), \
             patch('main.SUPPORTED_TASKS', {'translate': 'Translate', 'summarize': 'Summarize'}):
            
            report = evaluator.create_markdown_report("202401011200")
            
            assert "# Ollama 模型評比報表" in report
            assert "llama2" in report
            assert "翻譯良好" in report
            assert "摘要清楚" in report

    @patch('main.convert_markdown_to_html')
    @patch('builtins.open', new_callable=mock_open)
    def test_generate_report(self, mock_file, mock_convert, evaluator):
        """測試報表生成"""
        evaluator.results = {'llama2': {'translate': '測試結果'}}
        evaluator.evaluation_scores = {
            'openai_gpt_4': {
                'llama2': {'translate': {'score': 8, 'comment': '良好'}}
            }
        }
        
        with patch.object(evaluator, 'create_charts'), \
             patch.object(evaluator, 'create_markdown_report', return_value="# 測試報表"), \
             patch('main.datetime') as mock_dt:
            
            mock_dt.now.return_value.strftime.return_value = "202401011200"
            
            md_path, html_path = evaluator.generate_report()
            
            assert "evaluation_report_202401011200.md" in md_path
            assert "evaluation_report_202401011200.html" in html_path
            mock_convert.assert_called_once()


class TestModelEvaluatorIntegration:
    """整合測試"""
    
    @pytest.fixture
    def temp_input_file(self):
        """建立臨時輸入檔案"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("This is a test document for evaluation.")
            temp_path = f.name
        
        yield temp_path
        
        # 清理
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    def test_read_input_text_integration(self, temp_input_file):
        """整合測試：讀取實際檔案"""
        evaluator = ModelEvaluator()
        result = evaluator.read_input_text(temp_input_file)
        
        assert result == "This is a test document for evaluation."

    @patch('main.requests.post')
    @patch('main.get_cache_key')
    @patch('main.load_from_cache')
    @patch('main.save_to_cache')
    def test_api_call_with_caching_integration(self, mock_save, mock_load, mock_get_key, mock_post):
        """整合測試：API 呼叫與快取機制"""
        evaluator = ModelEvaluator()
        
        # 第一次呼叫 - 未命中快取
        mock_load.return_value = None
        mock_get_key.return_value = "test_cache_key"
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "API response"}}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        result1 = evaluator.call_ollama_api("llama2", "translate", "Hello")
        
        assert result1 == "API response"
        mock_save.assert_called_with("test_cache_key", "API response")
        
        # 第二次呼叫 - 命中快取
        mock_load.return_value = "Cached response"
        
        result2 = evaluator.call_ollama_api("llama2", "translate", "Hello")
        
        assert result2 == "Cached response"


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 