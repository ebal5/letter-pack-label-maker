#!/usr/bin/env python3
"""
日本語コード品質チェッカー

このスクリプトは、日本語コード（コメント、ドキュメント、文字列リテラル）の品質をチェックします。
以下の項目をチェック：
1. 文字コーディング（UTF-8かどうか）
2. 全角・半角の統一
3. docstringの充実度
"""

import re
import sys
from pathlib import Path


def check_encoding(file_path: Path) -> tuple[str, bool]:
    """ファイルのエンコーディングをチェック"""
    try:
        with open(file_path, encoding="utf-8") as f:
            f.read()
        return "UTF-8", True
    except UnicodeDecodeError:
        # その他のエンコーディングを試す
        for encoding in ["shift_jis", "euc_jp", "iso2022_jp"]:
            try:
                with open(file_path, encoding=encoding) as f:
                    f.read()
                return encoding, False
            except UnicodeDecodeError:
                continue
        return "Unknown", False


def check_fullwidth_numbers(text: str, file_path: str, line_num: int) -> list[dict]:
    """全角数字をチェック"""
    issues = []
    # 全角数字パターン（０-９）
    fullwidth_pattern = re.compile(r"[０-９]+")

    for match in fullwidth_pattern.finditer(text):
        # コメント内かコード内かは区別しない（すべて検出）
        halfwidth = match.group().translate(str.maketrans("０１２３４５６７８９", "0123456789"))
        issues.append(
            {
                "file": file_path,
                "line": line_num,
                "type": "全角数字",
                "current": match.group(),
                "suggested": halfwidth,
            }
        )

    return issues


def check_fullwidth_alpha(text: str, file_path: str, line_num: int) -> list[dict]:
    """全角英字をチェック"""
    issues = []
    # 全角英字パターン
    fullwidth_pattern = re.compile(r"[Ａ-Ｚａ-ｚ]+")

    for match in fullwidth_pattern.finditer(text):
        halfwidth = match.group().translate(
            str.maketrans(
                "ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ",
                "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
            )
        )
        issues.append(
            {
                "file": file_path,
                "line": line_num,
                "type": "全角英字",
                "current": match.group(),
                "suggested": halfwidth,
            }
        )

    return issues


def check_docstrings(file_path: Path) -> list[dict]:
    """docstringの有無をチェック"""
    issues = []

    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
    except (OSError, UnicodeDecodeError):
        return issues

    # 関数定義を検索
    function_pattern = re.compile(r"^def\s+(\w+)\s*\(", re.MULTILINE)
    class_pattern = re.compile(r"^class\s+(\w+)", re.MULTILINE)

    # 関数をチェック
    for match in function_pattern.finditer(content):
        func_name = match.group(1)
        # プライベート関数とマジックメソッドは除外
        if not func_name.startswith("_"):
            # docstringがあるか確認（簡易チェック）
            search_start = match.end()
            next_200 = content[search_start : search_start + 300]

            if '"""' not in next_200 and "'''" not in next_200:
                # 行番号を計算
                line_num = content[: match.start()].count("\n") + 1
                issues.append(
                    {
                        "file": str(file_path),
                        "line": line_num,
                        "type": "docstring不足",
                        "target": f"関数 {func_name}",
                    }
                )

    # クラスをチェック
    for match in class_pattern.finditer(content):
        class_name = match.group(1)
        # プライベートクラスは除外
        if not class_name.startswith("_"):
            search_start = match.end()
            next_300 = content[search_start : search_start + 500]

            if '"""' not in next_300 and "'''" not in next_300:
                line_num = content[: match.start()].count("\n") + 1
                issues.append(
                    {
                        "file": str(file_path),
                        "line": line_num,
                        "type": "docstring不足",
                        "target": f"クラス {class_name}",
                    }
                )

    return issues


def generate_report(
    encoding_issues: list[tuple],
    fullwidth_issues: list[dict],
    docstring_issues: list[dict],
) -> None:
    """チェック結果をレポート形式で出力"""
    print("\n" + "=" * 60)
    print("🔍 日本語コードチェックレポート")
    print("=" * 60 + "\n")

    # 1. エンコーディングチェック
    print("【文字コーディング】")
    if not encoding_issues:
        print("✅ すべてのファイルがUTF-8です\n")
    else:
        print(f"❌ {len(encoding_issues)}件の問題を検出\n")
        for file_path, encoding in encoding_issues:
            print(f"  ❌ {file_path}: {encoding}")
        print()

    # 2. 全角・半角チェック
    print("【全角・半角の使い分け】")
    if not fullwidth_issues:
        print("✅ 問題は検出されませんでした\n")
    else:
        print(f"⚠️ {len(fullwidth_issues)}件の問題を検出\n")
        # 最初の10件のみ表示
        for issue in fullwidth_issues[:10]:
            print(f"  {issue['file']}:{issue['line']}")
            print(f"    - 問題: {issue['type']}")
            print(f"    - 現在: {issue['current']}")
            print(f"    - 推奨: {issue['suggested']}")
        if len(fullwidth_issues) > 10:
            print(f"\n  ... その他 {len(fullwidth_issues) - 10}件")
        print()

    # 3. docstringチェック
    print("【コメント・ドキュメント】")
    if not docstring_issues:
        print("✅ すべての公開関数・クラスに適切なdocstringがあります\n")
    else:
        print(f"⚠️ {len(docstring_issues)}件のdocstring不足を検出\n")
        # 最初の10件のみ表示
        for issue in docstring_issues[:10]:
            print(f"  {issue['file']}:{issue['line']}")
            print(f"    - {issue['target']}: docstringがありません")
        if len(docstring_issues) > 10:
            print(f"\n  ... その他 {len(docstring_issues) - 10}件")
        print()

    # 総合評価
    total_issues = len(encoding_issues) + len(fullwidth_issues) + len(docstring_issues)
    print("【総合評価】")
    if total_issues == 0:
        print("✅ すべてのチェックに合格しました！")
    else:
        print(f"⚠️ {total_issues}件の改善点があります")
        if encoding_issues:
            print(f"  - 文字コーディング: {len(encoding_issues)}件（エンコーディング変更が必要）")
        if fullwidth_issues:
            print(f"  - 全角・半角: {len(fullwidth_issues)}件（修正可能）")
        if docstring_issues:
            print(f"  - docstring: {len(docstring_issues)}件（追加が必要）")

    print("\n" + "=" * 60 + "\n")


def main():
    """メイン処理"""
    # チェック対象のファイルパターン
    patterns = [
        ("*.py", "Pythonファイル"),
        ("*.md", "Markdownファイル"),
        ("*.html", "HTMLファイル"),
    ]

    encoding_issues = []
    fullwidth_issues = []
    docstring_issues = []

    # 1. エンコーディングチェック
    print("\n🔍 チェック中...\n")
    print("  - 文字コーディングをチェック中...")

    project_root = Path(".")
    for pattern, _ in patterns:
        for file_path in project_root.rglob(pattern):
            # 除外ファイル
            if any(
                x in str(file_path)
                for x in [".git", "node_modules", ".venv", "__pycache__", "uv.lock"]
            ):
                continue

            encoding, is_utf8 = check_encoding(file_path)
            if not is_utf8:
                encoding_issues.append((file_path, encoding))

    # 2. Pythonファイルの全角・半角チェック
    print("  - 全角・半角をチェック中...")
    for file_path in project_root.rglob("*.py"):
        if any(x in str(file_path) for x in [".git", "node_modules", ".venv", "__pycache__"]):
            continue

        try:
            with open(file_path, encoding="utf-8") as f:
                for i, line in enumerate(f, 1):
                    # コメントと文字列リテラルから日本語テキストを抽出
                    if "#" in line or '"' in line or "'" in line:
                        fullwidth_issues.extend(check_fullwidth_numbers(line, str(file_path), i))
                        fullwidth_issues.extend(check_fullwidth_alpha(line, str(file_path), i))
        except (OSError, UnicodeDecodeError):
            pass

    # 3. Pythonファイルのdocstringチェック
    print("  - docstringをチェック中...")
    for file_path in project_root.rglob("*.py"):
        if any(
            x in str(file_path) for x in [".git", "node_modules", ".venv", "__pycache__", "tests"]
        ):
            continue

        docstring_issues.extend(check_docstrings(file_path))

    # レポート生成
    generate_report(encoding_issues, fullwidth_issues, docstring_issues)

    # 終了ステータス
    return 0 if not encoding_issues else 1


if __name__ == "__main__":
    sys.exit(main())
