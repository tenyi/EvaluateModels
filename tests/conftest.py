#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
import os
import sys
import tempfile
import shutil
from unittest.mock import patch

# 將專案根目錄加入 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session")
def test_data_dir():
    """建立測試數據目錄"""
    test_dir = tempfile.mkdtemp(prefix="test_evaluate_models_")
    yield test_dir
    shutil.rmtree(test_dir, ignore_errors=True)


@pytest.fixture
def sample_config():
    """提供測試用的設定"""
    return {
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


@pytest.fixture
def sample_input_text():
    """提供測試用的輸入文字"""
    return """Hello everyone, thanks for joining today's meeting. 
We discussed the quarterly results and future plans. 
The team performed well this quarter with significant growth in revenue.
Key achievements include:
1. Launched new product features
2. Expanded to new markets
3. Improved customer satisfaction scores
Next quarter, we will focus on:
- Enhancing product quality
- Strengthening customer support
- Exploring partnership opportunities
Thank you for your attention."""


@pytest.fixture
def mock_api_responses():
    """提供模擬的 API 回應"""
    return {
        "ollama_translate": "大家好，感謝參加今天的會議。我們討論了季度結果和未來計劃。",
        "ollama_summarize": "本次會議討論了季度業績和未來規劃，團隊表現良好。",
        "openai_review": "分數: 8\n評語: 翻譯準確且流暢，符合中文表達習慣。",
        "gemini_review": "分數: 7\n評語: 摘要重點明確，但可以更詳細一些。"
    }


@pytest.fixture
def temp_input_file(sample_input_text):
    """建立臨時輸入檔案"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(sample_input_text)
        temp_path = f.name
    
    yield temp_path
    
    # 清理
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def temp_cache_dir():
    """建立臨時快取目錄"""
    temp_dir = tempfile.mkdtemp(prefix="test_cache_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_requests_post():
    """模擬 requests.post 的回應"""
    with patch('requests.post') as mock_post:
        yield mock_post


@pytest.fixture
def mock_openai_client():
    """模擬 OpenAI 客戶端"""
    with patch('openai.OpenAI') as mock_openai:
        yield mock_openai


@pytest.fixture
def disable_cache():
    """停用快取功能用於測試"""
    with patch('cache_utils.load_from_cache', return_value=None), \
         patch('cache_utils.save_to_cache'):
        yield


@pytest.fixture(autouse=True)
def setup_test_environment():
    """自動設定測試環境"""
    # 設定測試環境變數
    os.environ['TESTING'] = '1'
    
    # 確保 reports 目錄存在
    reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    
    yield
    
    # 清理測試環境變數
    if 'TESTING' in os.environ:
        del os.environ['TESTING']


# 測試標記
def pytest_configure(config):
    """設定 pytest 標記"""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "api: marks tests that require API access")


# 測試收集階段的設定
def pytest_collection_modifyitems(config, items):
    """修改測試項目的設定"""
    # 為沒有標記的測試自動加上 unit 標記
    for item in items:
        if not any(mark.name in ['unit', 'integration', 'slow', 'api'] for mark in item.iter_markers()):
            item.add_marker(pytest.mark.unit)


# 為測試報告添加額外資訊
def pytest_runtest_makereport(item, call):
    """為測試報告添加額外資訊"""
    if "incremental" in item.keywords:
        if call.excinfo is not None:
            parent = item.parent
            parent._previousfailed = item
    
    # 為 cleanup_on_failure fixture 添加測試結果
    if call.when == "call":
        setattr(item, "rep_" + call.when, call)


# 測試失敗時的處理
@pytest.fixture(autouse=True)
def cleanup_on_failure(request):
    """測試失敗時的清理工作"""
    yield
    
    # 檢查測試結果是否存在且失敗
    if hasattr(request.node, 'rep_call') and hasattr(request.node.rep_call, 'failed') and request.node.rep_call.failed:
        # 可以在這裡加入失敗時的清理邏輯
        pass


def pytest_runtest_setup(item):
    """測試設定階段"""
    if "incremental" in item.keywords:
        previousfailed = getattr(item.parent, "_previousfailed", None)
        if previousfailed is not None:
            pytest.xfail("previous test failed (%s)" % previousfailed.name)


# 測試會話開始時的設定
def pytest_sessionstart(session):
    """測試會話開始時執行"""
    print("\n🚀 開始執行 EvaluateModels 專案測試...")


# 測試會話結束時的設定
def pytest_sessionfinish(session, exitstatus):
    """測試會話結束時執行"""
    if exitstatus == 0:
        print("\n✅ 所有測試通過！")
    else:
        print(f"\n❌ 測試失敗，退出代碼: {exitstatus}") 