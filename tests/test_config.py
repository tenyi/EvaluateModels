#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 測試設定檔案
TEST_CONFIG = {
    "OLLAMA_API_BASE_URL": "http://localhost:11434",
    "OLLAMA_MODELS_TO_COMPARE": ["test-model-1", "test-model-2"],
    "OPENAI_API_KEY": "test-openai-key",
    "GOOGLE_API_KEY": "test-google-key",
    "OPENROUTER_API_KEY": "test-openrouter-key",
    "REPLICATE_API_KEY": "test-replicate-key",
    "REVIEWER_MODELS": [
        {"provider": "openai", "model": "gpt-4"},
        {"provider": "gemini", "model": "gemini-pro"}
    ],
    "REVIEWER_TEMPERATURE": {
        "gpt-4": 0.1,
        "gemini-pro": 0.1,
        "o4-mini": 1,
        "gpt-4.1": 1,
    },
    "SUPPORTED_TASKS": {
        "translate": "請將以下英文翻譯為繁體中文：",
        "summarize": "請為以下內容製作繁體中文摘要："
    }
}


class TestConfig:
    """測試設定檔案相關功能"""

    def test_config_structure(self):
        """測試設定檔案結構"""
        # 檢查必要的設定項目
        required_keys = [
            "OLLAMA_API_BASE_URL",
            "OLLAMA_MODELS_TO_COMPARE", 
            "REVIEWER_MODELS",
            "SUPPORTED_TASKS"
        ]
        
        for key in required_keys:
            assert key in TEST_CONFIG, f"缺少必要設定項目: {key}"

    def test_ollama_models_config(self):
        """測試 Ollama 模型設定"""
        models = TEST_CONFIG["OLLAMA_MODELS_TO_COMPARE"]
        
        assert isinstance(models, list), "OLLAMA_MODELS_TO_COMPARE 應該是列表"
        assert len(models) > 0, "至少需要設定一個 Ollama 模型"
        
        for model in models:
            assert isinstance(model, str), "模型名稱應該是字串"
            assert len(model) > 0, "模型名稱不能為空"

    def test_reviewer_models_config(self):
        """測試評審模型設定"""
        reviewers = TEST_CONFIG["REVIEWER_MODELS"]
        
        assert isinstance(reviewers, list), "REVIEWER_MODELS 應該是列表"
        assert len(reviewers) > 0, "至少需要設定一個評審模型"
        
        for reviewer in reviewers:
            assert isinstance(reviewer, dict), "評審模型設定應該是字典"
            assert "provider" in reviewer, "評審模型需要指定 provider"
            assert "model" in reviewer, "評審模型需要指定 model"
            
            # 檢查支援的 provider
            supported_providers = ["openai", "gemini", "openrouter", "replicate"]
            assert reviewer["provider"] in supported_providers, \
                f"不支援的 provider: {reviewer['provider']}"

    def test_supported_tasks_config(self):
        """測試支援任務設定"""
        tasks = TEST_CONFIG["SUPPORTED_TASKS"]
        
        assert isinstance(tasks, dict), "SUPPORTED_TASKS 應該是字典"
        assert len(tasks) > 0, "至少需要設定一個任務"
        
        # 檢查必要的任務
        required_tasks = ["translate", "summarize"]
        for task in required_tasks:
            assert task in tasks, f"缺少必要任務: {task}"
            assert isinstance(tasks[task], str), f"任務 {task} 的提示詞應該是字串"
            assert len(tasks[task]) > 0, f"任務 {task} 的提示詞不能為空"

    def test_api_keys_format(self):
        """測試 API 金鑰格式"""
        api_keys = [
            "OPENAI_API_KEY",
            "GOOGLE_API_KEY", 
            "OPENROUTER_API_KEY",
            "REPLICATE_API_KEY"
        ]
        
        for key in api_keys:
            if key in TEST_CONFIG:
                value = TEST_CONFIG[key]
                assert isinstance(value, str), f"{key} 應該是字串"
                # 檢查是否為預設值（應該要替換）
                default_values = [
                    "your_openai_api_key_here",
                    "your_google_api_key_here",
                    "your_openrouter_api_key_here", 
                    "your_replicate_api_key_here"
                ]
                if value in default_values:
                    print(f"警告: {key} 仍使用預設值，請設定實際的 API 金鑰")

    def test_reviewer_temperature_config(self):
        """測試評審模型溫度設定"""
        temps = TEST_CONFIG["REVIEWER_TEMPERATURE"]
        
        assert isinstance(temps, dict), "REVIEWER_TEMPERATURE 應該是字典"
        
        for model, temp in temps.items():
            assert isinstance(model, str), "Model 名稱應該是字串"
            assert isinstance(temp, (int, float)) or temp is None, \
                f"{model} 的溫度設定應該是數字或 None"
            
            if temp is not None:
                assert 0 <= temp <= 2, f"{model} 的溫度設定應該在 0-2 之間"

    def test_config_consistency(self):
        """測試設定一致性"""
        # 檢查評審模型的 model 是否都有對應的溫度設定
        reviewer_models = {r["model"] for r in TEST_CONFIG["REVIEWER_MODELS"]}
        temp_models = set(TEST_CONFIG["REVIEWER_TEMPERATURE"].keys())
        
        for model in reviewer_models:
            assert model in temp_models, \
                f"評審模型 {model} 缺少溫度設定"


class TestConfigValidation:
    """測試設定檔案驗證功能"""
    
    def test_validate_empty_config(self):
        """測試空設定檔案驗證"""
        empty_config = {}
        
        with pytest.raises(AssertionError):
            self._validate_config(empty_config)

    def test_validate_invalid_models_list(self):
        """測試無效的模型列表"""
        invalid_config = TEST_CONFIG.copy()
        invalid_config["OLLAMA_MODELS_TO_COMPARE"] = "not-a-list"
        
        with pytest.raises(AssertionError):
            self._validate_config(invalid_config)

    def test_validate_invalid_reviewer_format(self):
        """測試無效的評審模型格式"""
        invalid_config = TEST_CONFIG.copy()
        invalid_config["REVIEWER_MODELS"] = [
            {"provider": "openai"}  # 缺少 model
        ]
        
        with pytest.raises(AssertionError):
            self._validate_config(invalid_config)

    def test_validate_unsupported_provider(self):
        """測試不支援的 provider"""
        invalid_config = TEST_CONFIG.copy()
        invalid_config["REVIEWER_MODELS"] = [
            {"provider": "unsupported", "model": "test-model"}
        ]
        
        with pytest.raises(AssertionError):
            self._validate_config(invalid_config)

    def _validate_config(self, config):
        """驗證設定檔案（簡化版本）"""
        # 檢查必要項目
        required_keys = [
            "OLLAMA_MODELS_TO_COMPARE",
            "REVIEWER_MODELS", 
            "SUPPORTED_TASKS"
        ]
        
        for key in required_keys:
            assert key in config, f"缺少必要設定項目: {key}"
        
        # 檢查模型列表
        models = config["OLLAMA_MODELS_TO_COMPARE"]
        assert isinstance(models, list), "OLLAMA_MODELS_TO_COMPARE 應該是列表"
        assert len(models) > 0, "至少需要設定一個 Ollama 模型"
        
        # 檢查評審模型
        reviewers = config["REVIEWER_MODELS"]
        assert isinstance(reviewers, list), "REVIEWER_MODELS 應該是列表"
        assert len(reviewers) > 0, "至少需要設定一個評審模型"
        
        supported_providers = ["openai", "gemini", "openrouter", "replicate"]
        for reviewer in reviewers:
            assert isinstance(reviewer, dict), "評審模型設定應該是字典"
            assert "provider" in reviewer, "評審模型需要指定 provider"
            assert "model" in reviewer, "評審模型需要指定 model"
            assert reviewer["provider"] in supported_providers, \
                f"不支援的 provider: {reviewer['provider']}"
        
        # 檢查任務設定
        tasks = config["SUPPORTED_TASKS"]
        assert isinstance(tasks, dict), "SUPPORTED_TASKS 應該是字典"
        assert len(tasks) > 0, "至少需要設定一個任務"


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 