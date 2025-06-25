# ChangeLog

## [2.1.1] [2025/06/25 21:46] - 測試系統全面修復

### 🔧 測試系統修復

#### 核心測試基礎設施修復

- **修復 conftest.py 中的 cleanup_on_failure fixture**
  - 解決 `AttributeError: 'Function' object has no attribute 'rep_call'` 錯誤
  - 正確實作 pytest_runtest_makereport hook 來設定測試結果屬性
  - 確保測試失敗時的清理機制正常運作

#### 快取系統修復

- **修復 cache_utils.py 中的 save_to_cache 函數**
  - 新增 timestamp 欄位到快取資料中
  - 解決測試期望快取資料包含時間戳記的問題
  - 保持快取資料格式的一致性

#### API 測試修復

- **修復 test_main.py 中的 mock 導入問題**
  - 修正 `mock.requests.exceptions` 的錯誤使用
  - 直接導入 requests 模組來使用其異常類別
  - 確保 API 超時和請求錯誤測試正常運作

#### 評審功能測試修復

- **修正評審解析錯誤的預期結果**
  - 將預期分數從 5 修正為 1（因為 max(1, min(10, 0)) = 1）
  - 確保測試符合實際的評分邏輯

#### Markdown 轉 HTML 功能修復

- **修復 markdown2html.py 的錯誤處理**
  - 將 sys.exit() 改為拋出適當的異常
  - FileNotFoundError 用於檔案不存在的情況
  - PermissionError 等其他異常正常向上傳播

- **修復 HTML 輸出格式測試**
  - 修正標題 ID 屬性的預期格式（如 `<h1 id="_1">標題</h1>`）
  - 修正字符編碼聲明的預期格式（`charset=UTF-8`）
  - 確保 HTML 結構測試符合實際輸出

#### 測試 Fixture 完善

- **新增缺少的 temp_files fixture**
  - 為 TestMarkdown2HtmlIntegration 類別新增所需的 fixture
  - 確保整合測試能正常建立和清理臨時檔案

### 🎯 修復成果

#### 解決的問題統計

- **系統性錯誤**: 62個 AttributeError 錯誤全部修復
- **功能測試失敗**: 9個失敗測試全部修復
  - 1個快取功能測試
  - 2個 API Mock 測試
  - 1個評審解析測試
  - 5個 Markdown 轉 HTML 測試

#### 測試穩定性提升

- **測試基礎設施穩定**: conftest.py 修復確保所有測試的清理機制正常
- **Mock 系統完善**: API 測試的 mock 機制正確運作
- **錯誤處理一致**: 異常處理方式統一，避免 sys.exit() 干擾測試

### 🛠️ 技術細節

#### 關鍵修復點

1. **pytest_runtest_makereport Hook**
   ```python
   def pytest_runtest_makereport(item, call):
       if call.when == "call":
           setattr(item, "rep_" + call.when, call)
   ```

2. **快取資料結構**
   ```python
   cache_data = {
       "content": data,
       "timestamp": time.time()
   }
   ```

3. **異常處理改進**
   ```python
   # 從 sys.exit(1) 改為
   raise FileNotFoundError(f"找不到輸入檔案 '{input_path}'")
   ```

## [2025-06-25] - 完整測試程式建立

### 🧪 測試系統建立

#### 全面的測試覆蓋

- **主程式測試 (`test_main.py`)**
  - `ModelEvaluator` 類別的完整測試
  - API 呼叫功能測試（Ollama、OpenAI、Google、OpenRouter、Replicate）
  - 評審功能測試
  - 報表生成測試
  - 圖表生成測試
  - 錯誤處理測試

- **設定檔案測試 (`test_config.py`)**
  - 設定檔案結構驗證
  - 必要參數檢查
  - API 金鑰格式驗證
  - 評審模型設定驗證
  - 溫度參數設定驗證

- **快取系統測試 (`test_cache_utils.py`)**
  - 快取鍵生成測試
  - 快取儲存和載入測試
  - 快取檔案錯誤處理測試
  - 快取效能測試
  - 中文和特殊字符支援測試

- **Markdown 轉 HTML 測試 (`test_markdown2html.py`)**
  - 基本 Markdown 轉換測試
  - 中文內容轉換測試
  - 複雜表格轉換測試
  - 圖片和連結轉換測試
  - HTML 結構完整性測試

#### 測試基礎設施

- **測試配置 (`conftest.py`)**
  - 共用的 fixtures 和測試設定
  - 自動化測試環境設定
  - 測試數據管理
  - 模擬 API 回應設定

- **Pytest 配置 (`pytest.ini`)**
  - 測試發現和執行設定
  - 覆蓋率報告設定
  - 測試標記定義
  - 警告過濾設定

- **測試執行腳本 (`run_tests.py`)**
  - 多種測試執行選項
  - 依賴檢查功能
  - 覆蓋率報告生成
  - 測試結果清理

### 🎯 測試特色

#### 測試分類標記

- **`unit`**: 單元測試
- **`integration`**: 整合測試
- **`slow`**: 執行時間較長的測試
- **`api`**: 需要 API 連接的測試
- **`cache`**: 快取功能測試
- **`config`**: 設定功能測試
- **`report`**: 報表生成功能測試

#### Mock 和模擬

- **API 呼叫模擬**: 避免實際 API 呼叫的成本和依賴
- **檔案系統模擬**: 測試檔案操作而不影響實際檔案
- **快取系統模擬**: 測試快取邏輯而不產生實際快取檔案
- **時間模擬**: 測試時間相關功能

#### 錯誤情境測試

- **網路錯誤**: 模擬 API 超時、連接失敗等情況
- **檔案錯誤**: 模擬檔案不存在、權限錯誤等情況
- **設定錯誤**: 模擬無效設定、缺少必要參數等情況
- **解析錯誤**: 模擬 API 回應格式錯誤等情況

### 🛠️ 測試執行方式

#### 基本執行

```bash
# 執行所有測試
uv run python run_tests.py all

# 執行單元測試
uv run python run_tests.py unit

# 執行整合測試
uv run python run_tests.py integration

# 執行快速測試（排除慢速測試）
uv run python run_tests.py fast
```

#### 特定測試

```bash
# 執行特定測試檔案
uv run python run_tests.py --file test_main.py

# 執行 API 相關測試
uv run python run_tests.py api

# 執行快取相關測試
uv run python run_tests.py cache
```

#### 覆蓋率報告

```bash
# 生成覆蓋率報告
uv run python run_tests.py coverage

# 清理測試產生的檔案
uv run python run_tests.py clean
```

### 📊 測試覆蓋率

#### 目標覆蓋率

- **主程式 (`main.py`)**: 90%+ 覆蓋率
- **快取工具 (`cache_utils.py`)**: 95%+ 覆蓋率
- **Markdown 轉換 (`markdown2html.py`)**: 90%+ 覆蓋率
- **整體專案**: 85%+ 覆蓋率

#### 測試報告

- **終端輸出**: 即時顯示測試結果和覆蓋率
- **HTML 報告**: 詳細的覆蓋率分析報告 (`htmlcov/index.html`)
- **測試摘要**: 顯示通過/失敗的測試數量和執行時間

### 🔧 測試工具和依賴

#### 核心測試套件

- **pytest**: 測試框架
- **pytest-cov**: 覆蓋率測試
- **pytest-mock**: 模擬和 mock 功能
- **unittest.mock**: Python 內建模擬功能

#### 輔助工具

- **tempfile**: 臨時檔案管理
- **pathlib**: 路徑操作
- **subprocess**: 命令執行

### 🎯 測試最佳實踐

#### 測試設計原則

- **獨立性**: 每個測試都是獨立的，不依賴其他測試
- **可重複性**: 測試結果可重複，不受外部環境影響
- **清晰性**: 測試名稱和內容清楚表達測試目的
- **完整性**: 涵蓋正常流程、邊界情況和錯誤情況

#### 測試數據管理

- **Fixtures**: 使用 pytest fixtures 管理測試數據
- **臨時檔案**: 使用臨時檔案避免污染專案目錄
- **清理機制**: 自動清理測試產生的檔案和資源

### 🚀 持續改進

#### 未來計劃

- **效能測試**: 加入大量數據的效能測試
- **並行測試**: 支援並行執行以提升測試速度
- **自動化 CI/CD**: 整合到持續整合流程
- **測試數據多樣化**: 增加更多測試場景和數據

---

## [2025-01-27] - REVIEWER_MODELS 結構重構：支援同 Provider 多模型評審

### 🚀 重大架構改進

#### 評審模型配置結構變更

- **從 dict 結構改為 list 結構**
  - 舊格式：`{"openai": "o4-mini", "gemini": "gemini-2.5-pro"}`
  - 新格式：`[{"provider": "openai", "model": "o4-mini"}, {"provider": "openai", "model": "gpt-4.1"}]`
  - 支援同一個 provider 使用多個不同模型進行評審比較

#### 多模型評審能力

- **同 Provider 多模型支援**
  - 可同時使用 OpenAI 的 o4-mini、gpt-4.1、gpt-4o 等多個模型
  - 可同時使用 Google 的 gemini-1.5-flash、gemini-2.5-pro 等多個模型
  - 每個模型都會獨立進行評審並生成獨立的評分結果

### 🔧 技術實作改進

#### 唯一識別碼系統

- **新增 reviewer_id 生成邏輯**
  ```python
  reviewer_id = f"{provider}_{model.replace('/', '_').replace(':', '_').replace('-', '_')}"
  ```
  - 避免同 provider 多模型的資料衝突
  - 支援複雜模型名稱（如 OpenRouter 的 `mistralai/mistral-7b-instruct`）

#### 程式碼全面適配

- **更新所有相關函數**
  - `run_evaluation()`: 適配新的評審循環邏輯
  - `create_markdown_report()`: 支援多模型報表生成
  - `create_charts()`: 為每個評審模型生成獨立圖表
  - `main()`: 更新設定檢查邏輯

### 📊 報表增強

#### 獨立評審結果展示

- **每個評審模型獨立章節**
  - 報表標題格式：`OPENAI (o4-mini) 評審結果`、`OPENAI (gpt-4.1) 評審結果`
  - 統計分析格式：`OPENAI (o4-mini) 評審統計`
  - 圖表檔案格式：`chart_openai_o4_mini_TIMESTAMP.png`

#### 清晰的模型區分

- 每個評審模型的結果完全獨立顯示
- 便於比較不同模型的評審標準和偏好
- 支援深度分析各模型的評分差異

### 📝 配置範例

#### 新的 REVIEWER_MODELS 配置

```python
REVIEWER_MODELS = [
    {"provider": "openai", "model": "o4-mini"},
    {"provider": "openai", "model": "gpt-4.1"},
    {"provider": "openai", "model": "gpt-4o-mini"},
    {"provider": "gemini", "model": "gemini-1.5-flash-latest"},
    {"provider": "gemini", "model": "gemini-2.5-pro"},
    {"provider": "deepseek", "model": "deepseek-chat"},
    {"provider": "openrouter", "model": "mistralai/mistral-7b-instruct"},
    {"provider": "replicate", "model": "meta/meta-llama-3-70b-instruct:version"},
]
```

#### 停用設定

```python
# 如果要停用所有評審模型
REVIEWER_MODELS = []

# 或註解掉不需要的模型
# {"provider": "openai", "model": "gpt-4o-mini"},
```

### 🎯 使用優勢

#### 評審模型比較分析

- **多角度評審**: 同時使用多個評審模型，獲得更全面的評分視角
- **模型偏好分析**: 比較不同評審模型的評分標準和偏好差異
- **結果可信度**: 多個獨立評審結果提高評分的可信度

#### 靈活配置管理

- **按需啟用**: 可根據需要選擇性啟用特定的評審模型
- **成本控制**: 可根據 API 成本考量選擇適當的評審模型組合
- **實驗友好**: 便於進行不同評審模型組合的實驗

### 🔄 向後相容性

- **配置檔案**: 需要手動更新 `config.py` 為新格式
- **功能保持**: 所有原有的評審功能完全保持
- **報表格式**: 報表結構保持相容，僅增加更多評審結果

### 🛠️ 遷移指南

#### 從舊格式遷移

1. **備份現有配置**
2. **更新 REVIEWER_MODELS 格式**
   ```python
   # 舊格式
   REVIEWER_MODELS = {"openai": "gpt-4o-mini"}
   
   # 新格式
   REVIEWER_MODELS = [{"provider": "openai", "model": "gpt-4o-mini"}]
   ```
3. **測試配置正確性**

---

## [2025-06-25] - Temperature 參數配置與時間戳記檔名功能

### ✨ 新增功能

#### Temperature 參數配置

- **新增 `REVIEWER_TEMPERATURE` 配置選項**
  - 支援為每個評審模型單獨設定 temperature 參數
  - 當 temperature 設為 1 時，系統不會傳入此參數（適用於 O3/O4 等不允許自定義 temperature 的模型）
  - 當 temperature 為其他值時，會正常傳入該參數
  - 支援 OpenAI、Google Gemini、OpenRouter、Replicate 等所有評審模型

#### 時間戳記檔名

- **報表檔名自動加入時間戳記**
  - Markdown 報表格式：`evaluation_report_YYYYMMDDHHMM.md`
  - HTML 報表格式：`evaluation_report_YYYYMMDDHHMM.html`
  - 圖表檔案格式：`chart_{reviewer_type}_YYYYMMDDHHMM.png`
  - 避免不同時間的評比結果互相覆蓋

### 🔧 技術改進

#### API 呼叫優化

- **更新所有評審 API 呼叫函數**
  - `call_openai_api()`: 支援動態 temperature 設定
  - `call_google_api()`: 支援動態 temperature 設定
  - `call_openrouter_api()`: 支援動態 temperature 設定
  - `call_replicate_api()`: 支援動態 temperature 設定

#### 配置檔案擴充

- **更新 `config.py.example`**
  - 新增 `REVIEWER_TEMPERATURE` 範例配置
  - 詳細說明 O3/O4 模型的特殊處理方式

### 📝 配置範例

```python
# config.py 中的新配置
REVIEWER_TEMPERATURE = {
    "openai": 1,        # 對於 O3/O4 模型，不傳入 temperature 參數
    "gemini": 0.3,      # 正常傳入 temperature = 0.3
    "deepseek": 0.1,    # 正常傳入 temperature = 0.1
    "openrouter": 0.3,  # OpenRouter 模型可調整
    "replicate": 0.3,   # Replicate 模型可調整
}
```

### 🎯 使用說明

#### Temperature 設定邏輯

- **設為 1**: 不傳入 temperature 參數，讓模型使用預設值（適用於 O3/O4 系列）
- **設為其他值**: 正常傳入指定的 temperature 值
- **設為 None**: 同樣會正常傳入（向下相容）

#### 報表檔案管理

- 每次執行評比會產生獨特的檔案名稱
- 可以保留多個時間點的評比結果進行比較
- 圖表檔案也會對應包含時間戳記

### 🔄 相容性

- 向下相容現有配置
- 如果未設定 `REVIEWER_TEMPERATURE`，會使用預設值 0.1
- 現有的評比流程不受影響

---

## 版本說明

- 此版本主要針對新一代 AI 模型（如 O3/O4）的 temperature 限制進行適配
- 提升了報表管理的便利性，支援多時間點結果比較

## [1.3.0] [2025/06/25 21:57] [REVIEWER_TEMPERATURE 架構重構：從 Provider 改為 Model 設定]

### 🚀 重大架構改進

#### Temperature 設定架構變更

**變更前（以 Provider 為 Key）：**
```python
REVIEWER_TEMPERATURE = {
    "openai": 0.1,      # 所有 OpenAI 模型使用相同設定
    "gemini": 0.3,      # 所有 Gemini 模型使用相同設定
    "deepseek": 0.3,    # 所有 DeepSeek 模型使用相同設定
}
```

**變更後（以 Model 為 Key）：**
```python
REVIEWER_TEMPERATURE = {
    "o4-mini": 1,               # O4 系列不允許指定 temperature
    "gpt-4.1": 1,               # 某些新版 GPT 模型不允許指定 temperature
    "gpt-4o-mini": 0.3,         # 一般 OpenAI 模型可調整
    "gemini-1.5-flash-latest": 0.3,  # Google Gemini 模型可調整
    "gemini-2.5-pro": 0.3,      # Google Gemini 模型可調整
    "deepseek-chat": 0.3,       # DeepSeek 模型可調整
}
```

### 🎯 改進優勢

#### 精細化控制
- **模型特定設定**：每個模型可以有獨立的 temperature 設定
- **新模型支援**：O3/O4 等不允許自定義 temperature 的模型可以正確處理
- **靈活性提升**：同一 provider 的不同模型可以有不同的 temperature 設定

#### 向前相容性
- **自動降級**：未在 `REVIEWER_TEMPERATURE` 中設定的模型會使用預設值 0.1
- **錯誤預防**：避免因模型不支援 temperature 參數而導致的 API 錯誤

### 🔧 技術實作

#### 程式碼變更
- **API 呼叫函數**：所有評審 API 呼叫函數都已更新
  - `call_openai_api()`: 使用 `model` 作為 key
  - `call_google_api()`: 使用 `model` 作為 key  
  - `call_openrouter_api()`: 使用 `model` 作為 key
  - `call_replicate_api()`: 使用 `model_version` 作為 key

#### 配置檔案更新
- **config.py**: 更新為新的模型導向設定
- **config.py.example**: 提供新格式的範例設定
- **測試檔案**: 更新所有相關測試以符合新架構

### 🛠️ 遷移指南

#### 必要步驟
1. **更新 config.py**：將 `REVIEWER_TEMPERATURE` 從 provider 格式改為 model 格式
2. **檢查模型名稱**：確保所有使用的評審模型都有對應的 temperature 設定
3. **測試運行**：執行測試確保配置正確

#### 範例遷移
```python
# 舊格式
REVIEWER_TEMPERATURE = {
    "openai": 0.1,
    "gemini": 0.3,
}

# 新格式
REVIEWER_TEMPERATURE = {
    "gpt-4o-mini": 0.1,
    "o4-mini": 1,  # 不允許自定義 temperature
    "gemini-1.5-flash-latest": 0.3,
    "gemini-2.5-pro": 0.3,
}
```

### 📋 注意事項

#### 重要提醒
- **配置必須更新**：舊的 provider 格式將不再有效
- **模型名稱精確性**：必須使用與 `REVIEWER_MODELS` 中完全相同的模型名稱
- **預設值機制**：未設定的模型會使用 0.1 作為預設 temperature

#### 特殊模型處理
- **O3/O4 系列**：設為 1 表示不傳入 temperature 參數
- **一般模型**：設為 0.1-2.0 之間的數值
- **實驗模型**：可根據需要調整具體數值

---
