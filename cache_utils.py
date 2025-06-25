import hashlib
import json
import os

CACHE_DIR = "cache"

def get_cache_key(params: dict) -> str:
    """Generates a unique hash key from a dictionary of parameters."""
    # Ensure parameters are sorted by key for consistent hashing
    sorted_params = sorted(params.items())
    encoded_params = json.dumps(sorted_params).encode('utf-8')
    return hashlib.md5(encoded_params).hexdigest()

def load_from_cache(key: str) -> str | None:
    """Loads data from a cache file if it exists."""
    cache_file_path = os.path.join(CACHE_DIR, f"{key}.json")
    if os.path.exists(cache_file_path):
        try:
            with open(cache_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("content")
        except Exception as e:
            print(f"⚠️  Error loading from cache file {cache_file_path}: {e}")
            return None
    return None

def save_to_cache(key: str, data: str) -> None:
    """Saves data to a cache file."""
    if not os.path.exists(CACHE_DIR):
        try:
            os.makedirs(CACHE_DIR)
        except OSError as e:
            print(f"❌ Error creating cache directory {CACHE_DIR}: {e}")
            return

    cache_file_path = os.path.join(CACHE_DIR, f"{key}.json")
    try:
        with open(cache_file_path, 'w', encoding='utf-8') as f:
            json.dump({"content": data}, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"⚠️  Error saving to cache file {cache_file_path}: {e}")
