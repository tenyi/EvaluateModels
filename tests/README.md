# EvaluateModels 測試系統

這個目錄包含了 EvaluateModels 專案的完整測試套件。

## 📁 測試檔案結構

```text
tests/
├── README.md                 # 測試說明文件
├── conftest.py              # pytest 配置和共用 fixtures
├── test_main.py             # 主程式測試
├── test_config.py           # 設定檔案測試
├── test_cache_utils.py      # 快取功能測試
└── test_markdown2html.py    # Markdown 轉 HTML 測試
```

## 🚀 快速開始

### 安裝測試依賴

```bash
# 安裝測試相關套件
uv add --dev pytest pytest-cov pytest-mock
```

### 執行測試

```bash
# 執行所有測試
uv run python run_tests.py all

# 或直接使用 pytest
uv run pytest

# 執行特定測試檔案
uv run pytest tests/test_main.py -v
```

## 🎯 測試分類

### 測試標記 (Markers)

我們使用 pytest 標記來分類測試：

- **`unit`**: 單元測試 - 測試個別函數和類別
- **`integration`**: 整合測試 - 測試多個元件的整合
- **`slow`**: 慢速測試 - 執行時間較長的測試
- **`api`**: API 測試 - 需要外部 API 連接的測試
- **`cache`**: 快取測試 - 測試快取功能
- **`config`**: 設定測試 - 測試設定檔案功能
- **`report`**: 報表測試 - 測試報表生成功能

### 執行特定分類的測試

```bash
# 只執行單元測試
uv run pytest -m unit

# 只執行整合測試
uv run pytest -m integration

# 排除慢速測試
uv run pytest -m "not slow"

# 執行 API 相關測試
uv run pytest -m api
```

## 📊 覆蓋率報告

### 生成覆蓋率報告

```bash
# 生成終端覆蓋率報告
uv run pytest --cov=. --cov-report=term-missing

# 生成 HTML 覆蓋率報告
uv run pytest --cov=. --cov-report=html

# 使用測試腳本生成覆蓋率報告
uv run python run_tests.py coverage
```

### 查看覆蓋率報告

HTML 覆蓋率報告會生成在 `htmlcov/index.html`，可以在瀏覽器中開啟查看詳細的覆蓋率分析。

## 🛠️ 測試工具

### 使用測試執行腳本

專案提供了 `run_tests.py` 腳本來簡化測試執行：

```bash
# 檢查測試依賴
python run_tests.py check

# 執行所有測試
python run_tests.py all

# 執行單元測試
python run_tests.py unit

# 執行整合測試
python run_tests.py integration

# 執行快速測試（排除慢速測試）
python run_tests.py fast

# 執行特定測試檔案
python run_tests.py --file test_main.py

# 生成覆蓋率報告
python run_tests.py coverage

# 清理測試產生的檔案
python run_tests.py clean
```

### 驗證測試檔案

使用驗證腳本檢查所有測試檔案是否可以正常載入：

```bash
python test_verification.py
```

## 🧪 測試內容

### test_main.py

測試主程式 `main.py` 中的 `ModelEvaluator` 類別：

- ✅ 初始化測試
- ✅ 輸入檔案讀取測試
- ✅ Ollama API 呼叫測試
- ✅ OpenAI API 呼叫測試
- ✅ Google API 呼叫測試
- ✅ OpenRouter API 呼叫測試
- ✅ Replicate API 呼叫測試
- ✅ 評審功能測試
- ✅ 報表生成測試
- ✅ 圖表生成測試
- ✅ 錯誤處理測試

### test_config.py

測試設定檔案相關功能：

- ✅ 設定檔案結構驗證
- ✅ 必要參數檢查
- ✅ API 金鑰格式驗證
- ✅ 評審模型設定驗證
- ✅ 溫度參數設定驗證
- ✅ 設定一致性檢查

### test_cache_utils.py

測試快取系統功能：

- ✅ 快取鍵生成測試
- ✅ 快取儲存和載入測試
- ✅ 快取檔案錯誤處理測試
- ✅ 快取效能測試
- ✅ 中文和特殊字符支援測試
- ✅ 快取整合測試

### test_markdown2html.py

測試 Markdown 轉 HTML 功能：

- ✅ 基本 Markdown 轉換測試
- ✅ 中文內容轉換測試
- ✅ 複雜表格轉換測試
- ✅ 圖片和連結轉換測試
- ✅ HTML 結構完整性測試
- ✅ 錯誤處理測試

## 🔧 測試配置

### pytest.ini

專案根目錄的 `pytest.ini` 檔案包含了 pytest 的配置：

- 測試發現設定
- 覆蓋率報告設定
- 測試標記定義
- 警告過濾設定
- 日誌設定

### conftest.py

`tests/conftest.py` 檔案提供了：

- 共用的 fixtures
- 測試環境設定
- 自動化清理機制
- 模擬 API 回應設定

## 🎯 測試最佳實踐

### 編寫測試的原則

1. **獨立性**: 每個測試都應該是獨立的，不依賴其他測試的執行結果
2. **可重複性**: 測試結果應該是可重複的，不受外部環境影響
3. **清晰性**: 測試名稱和內容應該清楚表達測試的目的
4. **完整性**: 應該涵蓋正常流程、邊界情況和錯誤情況

### 使用 Mock 和模擬

為了避免實際 API 呼叫的成本和依賴，測試中大量使用了 Mock：

- **API 呼叫模擬**: 模擬 HTTP 請求和回應
- **檔案系統模擬**: 模擬檔案讀寫操作
- **時間模擬**: 模擬時間相關功能

### 測試數據管理

- 使用 pytest fixtures 管理測試數據
- 使用臨時檔案避免污染專案目錄
- 自動清理測試產生的檔案和資源

## 🚀 持續改進

### 目標覆蓋率

- **主程式 (`main.py`)**: 90%+ 覆蓋率
- **快取工具 (`cache_utils.py`)**: 95%+ 覆蓋率
- **Markdown 轉換 (`markdown2html.py`)**: 90%+ 覆蓋率
- **整體專案**: 85%+ 覆蓋率

### 未來計劃

- **效能測試**: 加入大量數據的效能測試
- **並行測試**: 支援並行執行以提升測試速度
- **自動化 CI/CD**: 整合到持續整合流程
- **測試數據多樣化**: 增加更多測試場景和數據

## 🆘 故障排除

### 常見問題

1. **ImportError**: 確保所有依賴都已安裝
2. **測試失敗**: 檢查是否有外部依賴或網路連接問題
3. **覆蓋率低**: 檢查是否有未測試的程式碼路徑

### 獲取幫助

如果遇到測試相關問題，可以：

1. 檢查測試輸出的錯誤訊息
2. 查看 HTML 覆蓋率報告了解未覆蓋的程式碼
3. 執行單個測試檔案進行除錯
4. 查看專案的 ChangeLog.md 了解最新變更
