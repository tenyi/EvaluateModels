#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
conftest.py：pytest 的設定檔

這個檔案包含了整個測試套件共享的 fixtures 和設定。
pytest 會自動發現並使用這個檔案中的設定，無需手動匯入。

主要功能：
- 設定共享的測試資源 (fixtures)，例如臨時目錄、設定檔、模擬資料等。
- 修改 pytest 的行為，例如新增自訂標記、調整測試收集流程。
- 在測試會話（session）的不同階段執行特定程式碼，例如開始和結束時。
"""

# 匯入必要的模組
import pytest  # pytest 測試框架
import os  # 處理作業系統相關功能，如路徑
import sys  # 存取 Python 直譯器的變數和函式
import tempfile  # 建立臨時檔案和目錄
import shutil  # 提供高階的檔案操作功能
from unittest.mock import patch  # 用於模擬 (mock) 物件和函式

# --- 路徑設定 ---

# 將專案根目錄加入 Python 的模組搜尋路徑
# 這樣可以確保在執行測試時，可以正確地匯入專案中的其他模組
# os.path.abspath(__file__) 取得目前檔案的絕對路徑
# os.path.dirname() 取得目錄名稱
# sys.path.insert(0, ...) 將路徑插入到搜尋路徑的最前面，優先被搜尋
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# --- Fixtures: 測試資源設定 ---

@pytest.fixture(scope="session")
def test_data_dir():
    """
    建立一個 session 等級的臨時目錄，用於存放測試數據。
    'scope="session"' 表示這個 fixture 在整個測試會話中只會執行一次。
    
    使用 `yield` 將目錄路徑提供給測試函式，並在測試會話結束後自動清理目錄。
    """
    # 建立一個唯一的臨時目錄
    test_dir = tempfile.mkdtemp(prefix="test_evaluate_models_")
    
    # 使用 yield 將控制權交還給測試函式，並提供 test_dir 的值
    yield test_dir
    
    # 測試會話結束後，執行清理工作
    # shutil.rmtree() 會遞迴地刪除整個目錄
    shutil.rmtree(test_dir, ignore_errors=True)


@pytest.fixture
def sample_config():
    """
    提供一個固定的、用於測試的設定字典。
    這個 fixture 的預設 scope 是 "function"，表示每個使用它的測試函式都會得到一個新的副本。
    """
    # 傳回一個包含模擬設定的字典
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
    """
    提供一段固定的、用於測試的輸入文字。
    """
    # 傳回一段多行字串作為測試輸入
    return '''Hello everyone, thanks for joining today's meeting. 
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
Thank you for your attention.'''


@pytest.fixture
def mock_api_responses():
    """
    提供一個包含模擬 API 回應的字典。
    用於在測試中取代實際的 API 呼叫，避免網路延遲和外部依賴。
    """
    # 傳回一個包含各種模擬 API 回應的字典
    return {
        "ollama_translate": "大家好，感謝參加今天的會議。我們討論了季度結果和未來計劃。",
        "ollama_summarize": "本次會議討論了季度業績和未來規劃，團隊表現良好。",
        "openai_review": "分數: 8\n評語: 翻譯準確且流暢，符合中文表達習慣。",
        "gemini_review": "分數: 7\n評語: 摘要重點明確，但可以更詳細一些。"
    }


@pytest.fixture
def temp_input_file(sample_input_text):
    """
    建立一個包含範例文字的臨時檔案。
    這個 fixture 依賴 `sample_input_text` fixture。
    
    使用 `with tempfile.NamedTemporaryFile` 可以確保檔案在使用後被妥善處理。
    `delete=False` 是為了在 `with` 區塊結束後檔案仍然存在，直到 `yield` 之後手動刪除。
    """
    # 建立一個具名的臨時檔案
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        # 將範例文字寫入檔案
        f.write(sample_input_text)
        # 取得檔案路徑
        temp_path = f.name
    
    # 將檔案路徑提供給測試函式
    yield temp_path
    
    # 測試函式執行完畢後，進行清理
    if os.path.exists(temp_path):
        os.unlink(temp_path)  # 刪除檔案


@pytest.fixture
def temp_cache_dir():
    """
    建立一個臨時目錄，用於測試快取功能。
    """
    # 建立一個前綴為 "test_cache_" 的臨時目錄
    temp_dir = tempfile.mkdtemp(prefix="test_cache_")
    
    # 將目錄路徑提供給測試函式
    yield temp_dir
    
    # 測試結束後，遞迴刪除目錄
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_requests_post():
    """
    模擬 `requests.post` 函式。
    使用 `unittest.mock.patch` 來取代目標函式，並傳回一個 mock 物件。
    """
    # 使用 patch 來模擬 'requests.post'
    with patch('requests.post') as mock_post:
        # 將 mock 物件提供給測試函式
        yield mock_post


@pytest.fixture
def mock_openai_client():
    """
    模擬 `openai.OpenAI` 客戶端。
    """
    # 使用 patch 來模擬 'openai.OpenAI'
    with patch('openai.OpenAI') as mock_openai:
        # 將 mock 物件提供給測試函式
        yield mock_openai


@pytest.fixture
def disable_cache():
    """
    在測試期間停用快取功能。
    透過 patch `load_from_cache` 和 `save_to_cache` 函式來達成。
    `load_from_cache` 永遠傳回 None，模擬快取未命中。
    `save_to_cache` 不執行任何操作。
    """
    with patch('cache_utils.load_from_cache', return_value=None), \
         patch('cache_utils.save_to_cache'):
        yield


@pytest.fixture(autouse=True)
def setup_test_environment():
    """
    為每個測試自動設定環境。
    `autouse=True` 表示這個 fixture 會自動被所有測試使用，無需手動指定。
    """
    # --- 設定階段 ---
    
    # 設定一個環境變數，用來識別目前是否在測試環境中
    os.environ['TESTING'] = '1'
    
    # 確保 reports 目錄存在，以便測試可以寫入報告檔案
    reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    
    # 將控制權交給測試函式
    yield
    
    # --- 清理階段 ---
    
    # 測試結束後，刪除設定的環境變數
    if 'TESTING' in os.environ:
        del os.environ['TESTING']


# --- Pytest Hooks: 自訂 pytest 行為 ---

def pytest_configure(config):
    """
    在 pytest 啟動時設定自訂標記 (markers)。
    這允許我們用 `@pytest.mark.slow` 等方式標記測試。
    """
    # 新增 'slow' 標記，用於標示執行時間較長的測試
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    # 新增 'integration' 標記，用於標示整合測試
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    # 新增 'unit' 標記，用於標示單元測試
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    # 新增 'api' 標記，用於標示需要存取外部 API 的測試
    config.addinivalue_line("markers", "api: marks tests that require API access")


def pytest_collection_modifyitems(config, items):
    """
    在測試收集完成後，修改測試項目列表。
    這個 hook 用於為沒有任何自訂標記的測試自動加上 'unit' 標記。
    """
    # 遍歷所有收集到的測試項目
    for item in items:
        # 檢查該項目是否已經有 'unit', 'integration', 'slow', 'api' 中的任何一個標記
        if not any(mark.name in ['unit', 'integration', 'slow', 'api'] for mark in item.iter_markers()):
            # 如果沒有，就為它加上 'unit' 標記
            item.add_marker(pytest.mark.unit)


def pytest_runtest_makereport(item, call):
    """
    為測試報告添加額外資訊。
    這個 hook 在測試的 setup, call, teardown 三個階段都會被呼叫。
    """
    # 處理 'incremental' 標記，如果一個測試失敗，則跳過後續依賴它的測試
    if "incremental" in item.keywords:
        if call.excinfo is not None:
            parent = item.parent
            parent._previousfailed = item
    
    # 將測試呼叫 (call) 的結果報告附加到測試項目 (item) 上
    # 這對於在 fixture 中判斷測試是否失敗很有用
    if call.when == "call":
        setattr(item, "rep_" + call.when, call)


@pytest.fixture(autouse=True)
def cleanup_on_failure(request):
    """
    一個 autouse fixture，用於在測試失敗時執行清理工作。
    """
    # 先執行測試
    yield
    
    # 測試結束後，檢查測試結果
    # `request.node` 代表目前的測試項目
    if hasattr(request.node, 'rep_call') and hasattr(request.node.rep_call, 'failed') and request.node.rep_call.failed:
        # 如果測試失敗，可以在這裡加入特定的清理邏輯
        # 例如：儲存螢幕截圖、記錄額外日誌等
        pass


def pytest_runtest_setup(item):
    """
    在每個測試的 setup 階段執行。
    用於實現 'incremental' 標記的功能。
    """
    # 如果測試被標記為 'incremental'
    if "incremental" in item.keywords:
        # 檢查是否有前一個測試失敗的記錄
        previousfailed = getattr(item.parent, "_previousfailed", None)
        if previousfailed is not None:
            # 如果有，則使用 pytest.xfail 來標記目前測試為預期失敗，並提供原因
            pytest.xfail("previous test failed (%s)" % previousfailed.name)


def pytest_sessionstart(session):
    """
    在整個測試會話 (session) 開始時執行一次。
    """
    # 印出開始訊息
    print("\n🚀 開始執行 EvaluateModels 專案測試...")


def pytest_sessionfinish(session, exitstatus):
    """
    在整個測試會話 (session) 結束時執行一次。
    """
    # 根據結束狀態碼印出不同的訊息
    if exitstatus == 0:
        print("\n✅ 所有測試通過！")
    else:
        print(f"\n❌ 測試失敗，退出代碼: {exitstatus}") 