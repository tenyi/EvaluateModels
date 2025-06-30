#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
測試執行腳本 (run_tests.py)

這個腳本提供了一個統一的命令列介面，用於執行專案中的各種類型測試。
它封裝了 `pytest` 命令，並提供了方便的選項來執行不同的測試套件，
例如單元測試、整合測試、特定檔案測試，以及產生測試覆蓋率報告。

主要功能：
- **依賴檢查**: 執行測試前，自動檢查必要的測試套件 (如 pytest, pytest-cov) 是否已安裝。
- **多樣的測試命令**: 
  - `all`: 執行所有測試。
  - `unit`: 僅執行標記為 `unit` 的單元測試。
  - `integration`: 僅執行標記為 `integration` 的整合測試。
  - `fast`: 執行排除了 `slow` 標記的快速測試。
  - `coverage`: 執行所有測試並產生覆蓋率報告 (HTML 和終端機輸出)。
  - `clean`: 清理測試過程中產生的暫存檔案 (如 .pytest_cache, .coverage, htmlcov)。
- **執行特定檔案**: 使用 `--file` 或 `-f` 參數可以指定只執行某個測試檔案。
- **命令封裝**: 將 `subprocess` 呼叫封裝在 `run_command` 函式中，統一處理命令的執行、輸出和錯誤。

使用範例:
```bash
# 執行所有測試
python run_tests.py all

# 僅執行單元測試
python run_tests.py unit

# 產生覆蓋率報告
python run_tests.py coverage

# 執行特定的測試檔案
python run_tests.py --file test_main.py

# 清理測試產物
python run_tests.py clean
```
"""

# 匯入必要的模組
import os
import sys
import subprocess  # 用於執行外部命令
import argparse    # 用於解析命令列參數
from pathlib import Path # 用於處理檔案路徑

def run_command(cmd, description=""):
    """
    執行一個指定的命令，並提供清晰的輸出和錯誤處理。

    Args:
        cmd (list): 要執行的命令及其參數，格式為一個列表，例如 ["pytest", "-v"]。
        description (str, optional): 對於正在執行的命令的簡短描述。

    Returns:
        bool: 如果命令成功執行 (返回碼為 0)，則為 True，否則為 False。
    """
    if description:
        print(f"\n🔄 {description}")
        print("-" * 50)
    
    print(f"執行命令: {' '.join(cmd)}")
    
    try:
        # 使用 subprocess.run 執行命令
        # check=True: 如果命令返回非零結束碼，則會引發 CalledProcessError
        # capture_output=False: 將子程序的輸出直接顯示在終端機上
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"✅ {description} 完成")
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} 失敗: {e}")
        return False
    except FileNotFoundError:
        print(f"❌ 找不到命令: {cmd[0]}，請確認是否已安裝並在系統路徑中。")
        return False

def check_dependencies():
    """檢查執行測試所需的核心 Python 套件是否已安裝。"""
    print("🔍 正在檢查測試依賴套件...")
    
    required_packages = [
        "pytest",
        "pytest_cov", # pytest 的覆蓋率外掛
        "pytest_mock", # pytest 的 mock 外掛
    ]
    
    missing_packages = []
    
    # 逐一檢查套件是否可以被匯入
    for package in required_packages:
        try:
            # 將套件名稱中的 "-" 替換為 "_" 以符合 Python 匯入語法
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    # 如果有缺少的套件，顯示提示訊息
    if missing_packages:
        print(f"❌ 缺少以下必要的測試套件: {', '.join(missing_packages)}")
        print("請執行以下命令來安裝開發依賴:")
        print(f"uv add --dev {' '.join(missing_packages)}")
        return False
    
    print("✅ 所有測試依賴都已安裝。")
    return True

def run_all_tests():
    """執行所有 pytest 能夠發現的測試。"""
    cmd = ["uv", "run", "pytest"]
    return run_command(cmd, "執行所有測試")

def run_unit_tests():
    """僅執行被 `@pytest.mark.unit` 標記的單元測試。"""
    cmd = ["uv", "run", "pytest", "-m", "unit"]
    return run_command(cmd, "執行單元測試")

def run_integration_tests():
    """僅執行被 `@pytest.mark.integration` 標記的整合測試。"""
    cmd = ["uv", "run", "pytest", "-m", "integration"]
    return run_command(cmd, "執行整合測試")

def run_specific_test(test_file):
    """執行一個特定的測試檔案。"""
    # 組合路徑，優先在 tests/ 目錄下尋找
    test_path = Path("tests") / test_file
    if not test_path.exists():
        # 如果在 tests/ 下找不到，則嘗試直接使用使用者提供的路徑
        test_path = Path(test_file)
    
    if not test_path.exists():
        print(f"❌ 找不到指定的測試檔案: {test_file}")
        return False
    
    cmd = ["uv", "run", "pytest", str(test_path), "-v"] # -v 增加詳細輸出
    return run_command(cmd, f"執行特定測試檔案: {test_path}")

def run_coverage_report():
    """執行測試並產生覆蓋率報告。"""
    # --cov=. : 指定計算覆蓋率的範圍為當前目錄下的所有程式碼
    # --cov-report=html : 產生 HTML 格式的報告，存放在 htmlcov/ 目錄
    # --cov-report=term : 在終端機中直接顯示覆蓋率摘要
    cmd = ["uv", "run", "pytest", "--cov=".", "--cov-report=html", "--cov-report=term"]
    success = run_command(cmd, "產生測試覆蓋率報告")
    
    if success:
        html_report = Path("htmlcov") / "index.html"
        if html_report.exists():
            print(f"📊 HTML 覆蓋率報告已生成，請用瀏覽器開啟: {html_report.resolve()}")
    
    return success

def run_fast_tests():
    """執行所有未被 `@pytest.mark.slow` 標記的測試。"""
    cmd = ["uv", "run", "pytest", "-m", "not slow"]
    return run_command(cmd, "執行快速測試 (排除慢速測試)")

def clean_test_artifacts():
    """清理由 pytest 和 coverage 產生的暫存檔案和目錄。"""
    print("🧹 正在清理測試產生的檔案...")
    
    # 定義要清理的路徑列表
    paths_to_clean = [
        ".pytest_cache",
        "htmlcov",
        ".coverage",
        "__pycache__",
        "tests/__pycache__",
    ]
    
    import shutil # 僅在此函式中需要，所以在此處匯入
    for path_str in paths_to_clean:
        path_obj = Path(path_str)
        if path_obj.exists():
            try:
                if path_obj.is_dir():
                    shutil.rmtree(path_obj)
                    print(f"  ✅ 已刪除目錄: {path_str}")
                else:
                    path_obj.unlink()
                    print(f"  ✅ 已刪除檔案: {path_str}")
            except OSError as e:
                print(f"  ❌ 刪除 {path_str} 失敗: {e}")
    
    print("✅ 清理完成。")

def main():
    """腳本的主進入點，負責解析命令列參數並呼叫對應的函式。"""
    # 設定命令列參數解析器
    parser = argparse.ArgumentParser(description="EvaluateModels 專案測試執行器")
    
    # 定義可接受的命令
    parser.add_argument(
        "command",
        choices=[
            "all", "unit", "integration", "fast", "coverage", "clean", "check"
        ],
        nargs="?", # 參數是可選的
        default="all", # 如果不提供，預設為 "all"
        help="要執行的測試命令 (預設: all)"
    )
    
    # 定義 --file 參數
    parser.add_argument(
        "--file", "-f",
        help="執行指定的測試檔案 (例如: test_main.py)"
    )
    
    # 解析傳入的參數
    args = parser.parse_args()
    
    print("🎯 EvaluateModels 專案測試執行器")
    print("=" * 50)
    
    # 在執行大部分命令前，先檢查依賴
    if args.command not in ["clean", "check"] and not check_dependencies():
        sys.exit(1)
    
    success = True
    
    # 根據參數決定要執行的動作
    if args.file:
        success = run_specific_test(args.file)
    elif args.command == "all":
        success = run_all_tests()
    elif args.command == "unit":
        success = run_unit_tests()
    elif args.command == "integration":
        success = run_integration_tests()
    elif args.command == "fast":
        success = run_fast_tests()
    elif args.command == "coverage":
        success = run_coverage_report()
    elif args.command == "clean":
        clean_test_artifacts()
    elif args.command == "check":
        success = check_dependencies()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 測試執行成功完成！")
        sys.exit(0)
    else:
        print("❌ 測試執行失敗！")
        sys.exit(1)


if __name__ == "__main__":
    main()
 