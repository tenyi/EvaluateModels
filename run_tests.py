#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
測試執行腳本

提供不同的測試執行選項：
- 全部測試
- 單元測試
- 整合測試
- 特定模組測試
- 覆蓋率報告
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description=""):
    """執行命令並顯示結果"""
    if description:
        print(f"\n🔄 {description}")
        print("-" * 50)
    
    print(f"執行命令: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"✅ {description} 完成")
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} 失敗: {e}")
        return False
    except FileNotFoundError:
        print(f"❌ 找不到命令: {cmd[0]}")
        return False


def check_dependencies():
    """檢查測試依賴"""
    print("🔍 檢查測試依賴...")
    
    required_packages = [
        "pytest",
        "pytest-cov",
        "pytest-mock",
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 缺少以下套件: {', '.join(missing_packages)}")
        print("請執行以下命令安裝:")
        print(f"uv add --dev {' '.join(missing_packages)}")
        return False
    
    print("✅ 所有依賴都已安裝")
    return True


def run_all_tests():
    """執行所有測試"""
    cmd = ["uv", "run", "pytest"]
    return run_command(cmd, "執行所有測試")


def run_unit_tests():
    """執行單元測試"""
    cmd = ["uv", "run", "pytest", "-m", "unit"]
    return run_command(cmd, "執行單元測試")


def run_integration_tests():
    """執行整合測試"""
    cmd = ["uv", "run", "pytest", "-m", "integration"]
    return run_command(cmd, "執行整合測試")


def run_specific_test(test_file):
    """執行特定測試檔案"""
    test_path = Path("tests") / test_file
    if not test_path.exists():
        test_path = Path(test_file)
    
    if not test_path.exists():
        print(f"❌ 找不到測試檔案: {test_file}")
        return False
    
    cmd = ["uv", "run", "pytest", str(test_path), "-v"]
    return run_command(cmd, f"執行測試檔案: {test_path}")


def run_coverage_report():
    """生成覆蓋率報告"""
    cmd = ["uv", "run", "pytest", "--cov=.", "--cov-report=html", "--cov-report=term"]
    success = run_command(cmd, "生成覆蓋率報告")
    
    if success:
        html_report = Path("htmlcov") / "index.html"
        if html_report.exists():
            print(f"📊 HTML 覆蓋率報告已生成: {html_report.absolute()}")
    
    return success


def run_fast_tests():
    """執行快速測試（排除慢速測試）"""
    cmd = ["uv", "run", "pytest", "-m", "not slow"]
    return run_command(cmd, "執行快速測試")


def run_api_tests():
    """執行 API 相關測試"""
    cmd = ["uv", "run", "pytest", "-m", "api"]
    return run_command(cmd, "執行 API 測試")


def run_cache_tests():
    """執行快取相關測試"""
    cmd = ["uv", "run", "pytest", "-m", "cache"]
    return run_command(cmd, "執行快取測試")


def run_config_tests():
    """執行設定相關測試"""
    cmd = ["uv", "run", "pytest", "-m", "config"]
    return run_command(cmd, "執行設定測試")


def run_report_tests():
    """執行報表相關測試"""
    cmd = ["uv", "run", "pytest", "-m", "report"]
    return run_command(cmd, "執行報表測試")


def clean_test_artifacts():
    """清理測試產生的檔案"""
    print("🧹 清理測試產生的檔案...")
    
    paths_to_clean = [
        ".pytest_cache",
        "htmlcov",
        ".coverage",
        "__pycache__",
        "tests/__pycache__",
    ]
    
    for path in paths_to_clean:
        path_obj = Path(path)
        if path_obj.exists():
            if path_obj.is_dir():
                import shutil
                shutil.rmtree(path_obj)
                print(f"  ✅ 已刪除目錄: {path}")
            else:
                path_obj.unlink()
                print(f"  ✅ 已刪除檔案: {path}")
    
    print("✅ 清理完成")


def main():
    """主函數"""
    parser = argparse.ArgumentParser(description="EvaluateModels 專案測試執行器")
    
    parser.add_argument(
        "command",
        choices=[
            "all", "unit", "integration", "fast", "api", "cache", "config", "report",
            "coverage", "clean", "check"
        ],
        nargs="?",
        default="all",
        help="測試命令"
    )
    
    parser.add_argument(
        "--file", "-f",
        help="執行特定測試檔案"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="詳細輸出"
    )
    
    args = parser.parse_args()
    
    print("🎯 EvaluateModels 專案測試執行器")
    print("=" * 50)
    
    # 檢查依賴
    if args.command != "clean" and not check_dependencies():
        sys.exit(1)
    
    success = True
    
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
    elif args.command == "api":
        success = run_api_tests()
    elif args.command == "cache":
        success = run_cache_tests()
    elif args.command == "config":
        success = run_config_tests()
    elif args.command == "report":
        success = run_report_tests()
    elif args.command == "coverage":
        success = run_coverage_report()
    elif args.command == "clean":
        clean_test_artifacts()
    elif args.command == "check":
        success = check_dependencies()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 測試執行完成！")
        sys.exit(0)
    else:
        print("❌ 測試執行失敗！")
        sys.exit(1)


if __name__ == "__main__":
    main() 