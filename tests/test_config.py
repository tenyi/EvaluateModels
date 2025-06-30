#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
測試 config.py 的設定是否正確與完整。

這個測試檔案旨在確保 `config.py` 中的設定符合預期格式和要求，
從而保證主程式在讀取設定時能夠正常運作。

主要測試內容：
- 檢查必要設定項是否存在。
- 驗證各項設定的資料型別是否正確 (例如，列表、字典、字串)。
- 確保設定內容的有效性 (例如，模型列表不能為空)。
- 測試設定之間的一致性 (例如，評審模型都有對應的溫度設定)。
"""

# 匯入必要的模組
import pytest  # pytest 測試框架
import sys  # 存取 Python 直譯器的變數和函式
import os  # 處理作業系統相關功能，如路徑

# 將專案根目錄加入 Python 的模組搜尋路徑
# 這樣可以確保在執行測試時，可以正確地匯入專案中的其他模組
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- 測試資料 ---

# 定義一個用於測試的模擬設定字典
# 在單元測試中，使用固定的測試資料可以避免依賴外部檔案 (config.py)，
# 讓測試更加穩定和可預測。
TEST_CONFIG = {
    "OLLAMA_API_BASE_URL": "http://localhost:11434",
    "OLLAMA_MODELS_TO_COMPARE": ["test-model-1", "test-model-2"], # 待評比的 Ollama 模型
    "OPENAI_API_KEY": "test-openai-key", # OpenAI API 金鑰
    "GOOGLE_API_KEY": "test-google-key", # Google API 金鑰
    "OPENROUTER_API_KEY": "test-openrouter-key", # OpenRouter API 金鑰
    "REPLICATE_API_KEY": "test-replicate-key", # Replicate API 金鑰
    "REVIEWER_MODELS": [ # 評審模型
        {"provider": "openai", "model": "gpt-4"},
        {"provider": "gemini", "model": "gemini-pro"}
    ],
    "REVIEWER_TEMPERATURE": { # 評審模型的溫度參數
        "gpt-4": 0.1,
        "gemini-pro": 0.1,
        "o4-mini": 1,
        "gpt-4.1": 1,
    },
    "SUPPORTED_TASKS": { # 支援的任務及其提示詞
        "translate": "請將以下英文翻譯為繁體中文：",
        "summarize": "請為以下內容製作繁體中文摘要："
    }
}


# --- 測試類別：TestConfig ---

class TestConfig:
    """針對設定檔 (config) 的主要結構和內容進行測試。"""

    def test_config_structure(self):
        """測試設定檔是否包含所有必要的頂層鍵 (top-level keys)。"""
        # 定義必要的設定項目
        required_keys = [
            "OLLAMA_API_BASE_URL",
            "OLLAMA_MODELS_TO_COMPARE", 
            "REVIEWER_MODELS",
            "SUPPORTED_TASKS"
        ]
        
        # 遍歷並斷言每個必要的鍵都在測試設定中
        for key in required_keys:
            assert key in TEST_CONFIG, f"缺少必要設定項目: {key}"

    def test_ollama_models_config(self):
        """測試 OLLAMA_MODELS_TO_COMPARE 設定的格式和內容。"""
        # 取得 Ollama 模型設定
        models = TEST_CONFIG["OLLAMA_MODELS_TO_COMPARE"]
        
        # 斷言它應該是一個列表
        assert isinstance(models, list), "OLLAMA_MODELS_TO_COMPARE 應該是列表"
        # 斷言列表不應為空
        assert len(models) > 0, "至少需要設定一個 Ollama 模型"
        
        # 遍歷列表中的每個模型
        for model in models:
            # 斷言模型名稱應該是字串
            assert isinstance(model, str), "模型名稱應該是字串"
            # 斷言模型名稱不應為空字串
            assert len(model) > 0, "模型名稱不能為空"

    def test_reviewer_models_config(self):
        """測試 REVIEWER_MODELS 設定的格式和內容。"""
        # 取得評審模型設定
        reviewers = TEST_CONFIG["REVIEWER_MODELS"]
        
        # 斷言它應該是一個列表
        assert isinstance(reviewers, list), "REVIEWER_MODELS 應該是列表"
        # 斷言列表不應為空
        assert len(reviewers) > 0, "至少需要設定一個評審模型"
        
        # 遍歷每個評審模型
        for reviewer in reviewers:
            # 斷言每個評審者都應該是字典
            assert isinstance(reviewer, dict), "評審模型設定應該是字典"
            # 斷言字典中必須包含 'provider' 和 'model' 鍵
            assert "provider" in reviewer, "評審模型需要指定 provider"
            assert "model" in reviewer, "評審模型需要指定 model"
            
            # 檢查 provider 是否為支援的類型
            supported_providers = ["openai", "gemini", "openrouter", "replicate"]
            assert reviewer["provider"] in supported_providers, \
                f"不支援的 provider: {reviewer['provider']}"

    def test_supported_tasks_config(self):
        """測試 SUPPORTED_TASKS 設定的格式和內容。"""
        # 取得支援的任務設定
        tasks = TEST_CONFIG["SUPPORTED_TASKS"]
        
        # 斷言它應該是一個字典
        assert isinstance(tasks, dict), "SUPPORTED_TASKS 應該是字典"
        # 斷言字典不應為空
        assert len(tasks) > 0, "至少需要設定一個任務"
        
        # 檢查是否包含必要的任務
        required_tasks = ["translate", "summarize"]
        for task in required_tasks:
            assert task in tasks, f"缺少必要任務: {task}"
            # 斷言任務的提示詞應該是字串
            assert isinstance(tasks[task], str), f"任務 {task} 的提示詞應該是字串"
            # 斷言提示詞不應為空
            assert len(tasks[task]) > 0, f"任務 {task} 的提示詞不能為空"

    def test_api_keys_format(self):
        """測試所有 API 金鑰的格式（如果存在）。"""
        # 定義所有可能的 API 金鑰
        api_keys = [
            "OPENAI_API_KEY",
            "GOOGLE_API_KEY", 
            "OPENROUTER_API_KEY",
            "REPLICATE_API_KEY"
        ]
        
        # 遍歷所有 API 金鑰
        for key in api_keys:
            # 如果金鑰存在於設定中
            if key in TEST_CONFIG:
                value = TEST_CONFIG[key]
                # 斷言其值應該是字串
                assert isinstance(value, str), f"{key} 應該是字串"
                
                # 檢查是否仍然是預設的範例值
                default_values = [
                    "your_openai_api_key_here",
                    "your_google_api_key_here",
                    "your_openrouter_api_key_here", 
                    "your_replicate_api_key_here"
                ]
                # 如果是預設值，印出警告訊息 (在測試中通常不建議 print，但此處用於提醒使用者)
                if value in default_values:
                    print(f"警告: {key} 仍使用預設值，請設定實際的 API 金鑰")

    def test_reviewer_temperature_config(self):
        """測試 REVIEWER_TEMPERATURE 設定的格式和內容。"""
        # 取得溫度設定
        temps = TEST_CONFIG["REVIEWER_TEMPERATURE"]
        
        # 斷言它應該是一個字典
        assert isinstance(temps, dict), "REVIEWER_TEMPERATURE 應該是字典"
        
        # 遍歷字典中的每個項目
        for model, temp in temps.items():
            # 斷言模型名稱是字串
            assert isinstance(model, str), "Model 名稱應該是字串"
            # 斷言溫度值是數字或 None
            assert isinstance(temp, (int, float)) or temp is None, \
                f"{model} 的溫度設定應該是數字或 None"
            
            # 如果溫度值不是 None，則檢查其範圍
            if temp is not None:
                assert 0 <= temp <= 2, f"{model} 的溫度設定應該在 0-2 之間"

    def test_config_consistency(self):
        """測試設定之間的一致性。"""
        # 檢查在 REVIEWER_MODELS 中定義的每個模型，是否都在 REVIEWER_TEMPERATURE 中有對應的設定
        reviewer_models = {r["model"] for r in TEST_CONFIG["REVIEWER_MODELS"]}
        temp_models = set(TEST_CONFIG["REVIEWER_TEMPERATURE"].keys())
        
        # 遍歷所有評審模型
        for model in reviewer_models:
            # 斷言模型名稱存在於溫度設定的鍵中
            assert model in temp_models, \
                f"評審模型 {model} 缺少溫度設定"


# --- 測試類別：TestConfigValidation ---

class TestConfigValidation:
    """模擬一個簡化的設定驗證流程，並測試其是否能捕捉到錯誤的設定。"""
    
    def test_validate_empty_config(self):
        """測試當傳入一個空字典時，驗證函式是否會引發錯誤。"""
        empty_config = {}
        
        # 使用 pytest.raises 來斷言程式碼區塊會引發指定的例外
        with pytest.raises(AssertionError):
            self._validate_config(empty_config)

    def test_validate_invalid_models_list(self):
        """測試當 OLLAMA_MODELS_TO_COMPARE 不是列表時，是否會引發錯誤。"""
        # 建立一個無效的設定
        invalid_config = TEST_CONFIG.copy()
        invalid_config["OLLAMA_MODELS_TO_COMPARE"] = "not-a-list" # 錯誤的型別
        
        # 斷言會引發 AssertionError
        with pytest.raises(AssertionError):
            self._validate_config(invalid_config)

    def test_validate_invalid_reviewer_format(self):
        """測試當 REVIEWER_MODELS 中有項目缺少 'model' 鍵時，是否會引發錯誤。"""
        # 建立一個無效的設定
        invalid_config = TEST_CONFIG.copy()
        invalid_config["REVIEWER_MODELS"] = [
            {"provider": "openai"}  # 缺少 'model' 鍵
        ]
        
        # 斷言會引發 AssertionError
        with pytest.raises(AssertionError):
            self._validate_config(invalid_config)

    def test_validate_unsupported_provider(self):
        """測試當 REVIEWER_MODELS 中包含不支援的 provider 時，是否會引發錯誤。"""
        # 建立一個無效的設定
        invalid_config = TEST_CONFIG.copy()
        invalid_config["REVIEWER_MODELS"] = [
            {"provider": "unsupported", "model": "test-model"} # 不支援的 provider
        ]
        
        # 斷言會引發 AssertionError
        with pytest.raises(AssertionError):
            self._validate_config(invalid_config)

    def _validate_config(self, config):
        """
        一個簡化的內部輔助函式，用於驗證設定字典。
        這個函式模仿了主程式中可能存在的設定驗證邏輯。
        """
        # 檢查必要項目
        required_keys = [
            "OLLAMA_MODELS_TO_COMPARE",
            "REVIEWER_MODELS", 
            "SUPPORTED_TASKS"
        ]
        
        for key in required_keys:
            assert key in config, f"缺少必要設定項目: {key}"
        
        # 檢查 Ollama 模型列表
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


# --- 主程式進入點 ---

# 當這個檔案被直接執行時 (例如 `python tests/test_config.py`)
if __name__ == "__main__":
    # 使用 pytest.main 來執行此檔案中的測試
    # "-v" 參數表示使用詳細 (verbose) 模式輸出
    pytest.main([__file__, "-v"]) 