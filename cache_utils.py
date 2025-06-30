#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
快取工具模組 (cache_utils.py)

這個模組提供了一組函式，用於處理 API 呼叫的快取，以避免重複請求和加快執行速度。
快取的基本原理是將每次 API 請求的參數組合生成一個唯一的鍵 (key)，然後將 API 的回應
儲存到一個以該鍵命名的檔案中。下次用同樣的參數發起請求時，程式會先檢查是否存在
對應的快取檔案，如果存在，就直接讀取檔案內容，而不是真的發送 API 請求。

主要功能：
- `get_cache_key()`: 根據一組參數生成一個穩定、唯一的 MD5 雜湊值作為快取鍵。
- `load_from_cache()`: 根據快取鍵，嘗試從快取目錄讀取並傳回儲存的資料。
- `save_to_cache()`: 將資料以 JSON 格式儲存到以快取鍵命名的檔案中。

快取檔案儲存在專案根目錄下的 `cache/` 目錄中。
"""

# 匯入必要的模組
import hashlib  # 用於計算 MD5 雜湊值
import json     # 用於處理 JSON 格式的資料序列化與反序列化
import os       # 用於處理檔案路徑和目錄操作

# --- 常數定義 ---

# 定義快取檔案存放的目錄名稱
CACHE_DIR = "cache"

# --- 函式定義 ---

def get_cache_key(params: dict, prompt: str = "") -> str:
    """
    根據傳入的參數字典，生成一個唯一的 MD5 雜湊值作為快取鍵。

    為了確保對於同樣的參數組合（即使順序不同）都能產生相同的鍵，
    在進行雜湊計算之前，會先對參數字典的鍵進行排序。

    Args:
        params (dict): 包含所有影響 API 呼叫結果的參數的字典。
                       例如：{'model': 'llama2', 'task': 'translate', 'text': 'hello'}

    Returns:
        str: 一個 32 個字元的十六進位 MD5 雜湊字串，例如：'e597b123...'
    """
    # 1. 將提示詞加入到參數字典中，確保提示詞的變動會影響快取鍵
    #    這裡使用一個新的字典來避免修改原始的 params 字典
    all_params = params.copy()
    all_params['prompt'] = prompt

    # 2. 將字典的鍵值對 (items) 進行排序，確保輸入順序不影響最終的雜湊結果
    sorted_params = sorted(all_params.items())
    
    # 3. 使用 json.dumps 將排序後的列表轉換為 JSON 格式的字串。
    #    ensure_ascii=False 確保中文字元不會被轉換成 \uXXXX 格式。
    #    separators=(',', ':') 去除多餘的空白，讓字串更緊湊。
    encoded_params = json.dumps(sorted_params, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    
    # 3. 使用 MD5 演算法計算雜湊值，並以十六進位格式傳回
    return hashlib.md5(encoded_params).hexdigest()

def load_from_cache(key: str) -> str | None:
    """
    如果快取檔案存在，則從中載入資料。

    Args:
        key (str): 由 get_cache_key() 生成的快取鍵。

    Returns:
        str | None: 如果快取命中，則傳回儲存的內容 (字串)；
                    如果檔案不存在或讀取失敗，則傳回 None。
    """
    # 組合出完整的快取檔案路徑
    cache_file_path = os.path.join(CACHE_DIR, f"{key}.json")
    
    # 檢查檔案是否存在
    if os.path.exists(cache_file_path):
        try:
            # 開啟並讀取 JSON 檔案
            with open(cache_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 從 JSON 物件中取得 "content" 鍵的值
                return data.get("content")
        except Exception as e:
            # 如果在讀取或解析過程中發生錯誤，印出警告訊息
            print(f"⚠️  讀取快取檔案 {cache_file_path} 時發生錯誤: {e}")
            return None
    # 如果檔案不存在，直接傳回 None
    return None

def save_to_cache(key: str, data: str) -> None:
    """
    將資料儲存到快取檔案中。

    Args:
        key (str): 由 get_cache_key() 生成的快取鍵。
        data (str): 要儲存的 API 回應內容。
    """
    import time  # 匯入 time 模組以記錄時間戳
    
    # 檢查快取目錄是否存在，如果不存在，則嘗試建立它
    if not os.path.exists(CACHE_DIR):
        try:
            os.makedirs(CACHE_DIR)
        except OSError as e:
            # 如果建立目錄失敗 (例如，權限問題)，印出錯誤訊息並返回
            print(f"❌ 建立快取目錄 {CACHE_DIR} 時發生錯誤: {e}")
            return

    # 組合出完整的快取檔案路徑
    cache_file_path = os.path.join(CACHE_DIR, f"{key}.json")
    try:
        # 準備要寫入的資料結構，包含內容和時間戳
        cache_data = {
            "content": data,
            "timestamp": time.time()
        }
        # 開啟檔案並寫入 JSON 資料
        with open(cache_file_path, 'w', encoding='utf-8') as f:
            # ensure_ascii=False 確保中文能正確寫入
            # indent=4 讓 JSON 檔案內容更容易閱讀
            json.dump(cache_data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        # 如果寫入檔案時發生錯誤，印出警告訊息
        print(f"⚠️  儲存快取檔案 {cache_file_path} 時發生錯誤: {e}")
