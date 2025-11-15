"""
テスト起動条件の管理
ファイル変更に基づいてテストを条件付きスキップする機能を提供
"""

import subprocess
from pathlib import Path

import pytest


def get_changed_files() -> set[str]:
    """
    Gitで変更されたファイルのセットを取得

    Returns:
        変更されたファイルのパスセット（相対パス）
        gitコマンドが使えない場合は全ファイル対象のセットを返す
    """
    try:
        # HEADとの差分で変更されたファイルを取得
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent),
        )
        if result.returncode == 0 and result.stdout.strip():
            return set(result.stdout.strip().split("\n"))
        else:
            # 差分がない場合は空セット（全テストをスキップ）
            return set()
    except (FileNotFoundError, Exception):
        # gitが使えない場合は全テストを実行
        return {"src/letterpack/label.py", "src/letterpack/csv_parser.py"}


# テストモジュールごとの依存関係を定義
TEST_DEPENDENCIES = {
    "test_label.py": {
        "src/letterpack/label.py",
    },
    "test_csv_parser.py": {
        "src/letterpack/csv_parser.py",
        "src/letterpack/label.py",  # csv_parser.pyが label.pyに依存
    },
    "test_multi_interface.py": {
        "src/letterpack/label.py",
        "src/letterpack/csv_parser.py",
        "src/letterpack/cli.py",
        "src/letterpack/web.py",
    },
}


def pytest_collection_modifyitems(config, items):
    """
    テスト実行条件を設定
    依存ファイルが変更されていないテストはスキップマークを追加
    """
    changed_files = get_changed_files()

    for item in items:
        # テストファイル名から対応する依存関係を取得
        test_filename = item.fspath.basename
        dependencies = TEST_DEPENDENCIES.get(test_filename, set())

        # 依存ファイルが変更されていない場合はスキップ
        if dependencies and not any(dep in changed_files for dep in dependencies):
            skip_reason = f"No changes in dependent files: {', '.join(sorted(dependencies))}"
            item.add_marker(pytest.mark.skip(reason=skip_reason))
