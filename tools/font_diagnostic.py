#!/usr/bin/env python3
"""
フォント診断スクリプト

このスクリプトは、システムのフォント環境を診断し、
レターパックラベル生成に必要なフォントの状態を確認します。

使用方法:
    python tools/font_diagnostic.py
"""

import os
import sys
from pathlib import Path
from typing import Optional


def detect_environment() -> dict:
    """
    実行環境を特定

    Returns:
        dict: 環境情報
    """
    env_info = {
        "platform": sys.platform,
        "is_docker": Path("/.dockerenv").exists(),
        "is_pyodide": sys.platform == "emscripten",
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "os_name": os.name,
    }
    return env_info


def get_platform_font_dirs() -> list[str]:
    """
    プラットフォームに応じたフォントディレクトリを取得

    Returns:
        list[str]: フォントディレクトリのリスト
    """
    if sys.platform == "win32":
        return ["C:\\Windows\\Fonts\\", "C:\\Program Files\\Common Files\\Adobe\\Fonts\\"]
    elif sys.platform == "darwin":  # macOS
        return [
            "/System/Library/Fonts/",
            "/Library/Fonts/",
            os.path.expanduser("~/Library/Fonts/"),
        ]
    else:  # Linux等
        return [
            "/usr/share/fonts/",
            "/usr/local/share/fonts/",
            os.path.expanduser("~/.fonts/"),
        ]


def find_system_fonts() -> dict:
    """
    システムにインストールされているフォントを検索

    Returns:
        dict: 見つかったフォント情報
    """
    fonts = {
        "noto_cjk": [],
        "noto_sans": [],
        "ipa_gothic": [],
        "ipa_serif": [],
        "heiseifonts": [],
        "other_cjk": [],
    }

    font_dirs = get_platform_font_dirs()

    for font_dir in font_dirs:
        if not Path(font_dir).exists():
            continue

        try:
            # Noto CJKフォント
            noto_cjk = list(Path(font_dir).rglob("*Noto*CJK*.ttc")) + list(
                Path(font_dir).rglob("*Noto*CJK*.ttf")
            )
            fonts["noto_cjk"].extend([str(f) for f in noto_cjk])

            # Noto Sans フォント
            noto_sans = list(Path(font_dir).rglob("*Noto*Sans*.ttf")) + list(
                Path(font_dir).rglob("*Noto*Sans*.ttc")
            )
            fonts["noto_sans"].extend([str(f) for f in noto_sans if "CJK" not in str(f)])

            # IPAフォント
            ipa_files = list(Path(font_dir).rglob("*ipa*.ttf")) + list(
                Path(font_dir).rglob("*ipa*.ttc")
            )
            for f in ipa_files:
                if "gothic" in str(f).lower() or "ipag" in str(f).lower():
                    fonts["ipa_gothic"].append(str(f))
                elif "serif" in str(f).lower() or "ipam" in str(f).lower():
                    fonts["ipa_serif"].append(str(f))

            # Heiseiフォント
            heiseifonts = list(Path(font_dir).rglob("*Heisei*.ttf"))
            fonts["heiseifonts"].extend([str(f) for f in heiseifonts])

        except (PermissionError, OSError):
            continue

    # 重複を削除
    for key in fonts:
        fonts[key] = list(set(fonts[key]))

    return fonts


def check_reportlab_fonts() -> list[str]:
    """
    ReportLabに登録されているフォントを確認

    Returns:
        list[str]: 登録されているフォント名
    """
    try:
        from reportlab.pdfbase import pdfmetrics

        registered = pdfmetrics.getRegisteredFontNames()
        return list(registered)
    except ImportError:
        return []
    except Exception as e:
        print(f"警告: ReportLabのフォント確認に失敗: {e}", file=sys.stderr)
        return []


def read_label_py_font_config() -> dict:
    """
    src/letterpack/label.pyのフォント設定を読み取る

    Returns:
        dict: フォント設定情報
    """
    config = {
        "primary_fonts": [],
        "fallback_fonts": [],
        "bold_fonts": [],
        "font_paths": [],
    }

    label_py = Path("src/letterpack/label.py")
    if not label_py.exists():
        return config

    try:
        with open(label_py, "r", encoding="utf-8") as f:
            content = f.read()

            # IPAフォントパスを抽出
            if "ipa_font_paths" in content:
                # 簡易的な抽出（より正確にはASTパースを使用）
                import re

                # フォントパスをリストから抽出
                pattern = r'"([^"]*(?:ipa|IPA)[^"]*)"'
                matches = re.findall(pattern, content)
                config["font_paths"] = list(set(matches))

                # フォント名を特定
                if "IPAGothic" in content:
                    config["primary_fonts"].append("IPAGothic")
                if "HeiseiMin-W3" in content:
                    config["fallback_fonts"].append("HeiseiMin-W3")
                if "HeiseiKakuGo-W5" in content:
                    config["fallback_fonts"].append("HeiseiKakuGo-W5")
                if "Helvetica" in content:
                    config["fallback_fonts"].append("Helvetica")

    except Exception as e:
        print(f"警告: label.pyの読み取りに失敗: {e}", file=sys.stderr)

    return config


def analyze_pdf_fonts(pdf_path: Optional[str] = None) -> Optional[dict]:
    """
    PDF内のフォント情報を分析

    Args:
        pdf_path: PDFファイルパス（Noneの場合はスキップ）

    Returns:
        dict: フォント情報、またはNone
    """
    if not pdf_path or not Path(pdf_path).exists():
        return None

    try:
        from pypdf import PdfReader

        reader = PdfReader(pdf_path)
        fonts = {}

        for page in reader.pages:
            if "/Font" in page["/Resources"]:
                for font_name, font_ref in page["/Resources"]["/Font"].items():
                    font_obj = font_ref.get_object()
                    if "/BaseFont" in font_obj:
                        base_font = font_obj["/BaseFont"]
                        fonts[base_font] = {
                            "embedded": "/FontFile" in font_obj or "/FontFile2" in font_obj,
                            "type": font_obj.get("/Subtype", "Unknown"),
                        }

        return fonts if fonts else None
    except ImportError:
        return None
    except Exception as e:
        print(f"警告: PDF分析に失敗: {e}", file=sys.stderr)
        return None


def print_diagnostic_report(
    env_info: dict,
    system_fonts: dict,
    reportlab_fonts: list[str],
    label_config: dict,
    pdf_fonts: Optional[dict] = None,
):
    """
    診断レポートを出力

    Args:
        env_info: 環境情報
        system_fonts: システムフォント情報
        reportlab_fonts: ReportLabのフォント情報
        label_config: label.pyのフォント設定
        pdf_fonts: PDF内のフォント情報（オプション）
    """
    print("\n" + "=" * 50)
    print("🔍 フォント診断レポート")
    print("=" * 50 + "\n")

    # 【実行環境】
    print("【実行環境】")
    platform_str = "Windows" if env_info["platform"] == "win32" else (
        "macOS" if env_info["platform"] == "darwin" else "Linux"
    )
    print(f"- プラットフォーム: {platform_str}")
    print(f"- Docker環境: {'はい ✅' if env_info['is_docker'] else 'いいえ'}")
    print(f"- Pyodide環境: {'はい ✅' if env_info['is_pyodide'] else 'いいえ'}")
    print(f"- Python: {env_info['python_version']}\n")

    # 【ReportLab登録フォント】
    print("【ReportLab登録フォント】")
    if reportlab_fonts:
        important_fonts = ["Helvetica", "Times-Roman", "Courier"]
        for font in important_fonts:
            if font in reportlab_fonts:
                print(f"✅ {font} (標準フォント)")
        if "IPAGothic" in reportlab_fonts:
            print("✅ IPAGothic (登録済み)")
        else:
            print("❌ IPAGothic (未登録)")
    else:
        print("❌ ReportLabが初期化されていません\n")

    # 【システムフォント】
    print("\n【システムフォント】")
    has_fonts = False

    if system_fonts["noto_cjk"]:
        for font in system_fonts["noto_cjk"][:2]:  # 最初の2つだけ表示
            print(f"✅ Noto CJK: {Path(font).name}")
            has_fonts = True
        if len(system_fonts["noto_cjk"]) > 2:
            print(f"   ... 他 {len(system_fonts['noto_cjk']) - 2} 個")

    if system_fonts["noto_sans"]:
        for font in system_fonts["noto_sans"][:2]:
            print(f"✅ Noto Sans: {Path(font).name}")
            has_fonts = True
        if len(system_fonts["noto_sans"]) > 2:
            print(f"   ... 他 {len(system_fonts['noto_sans']) - 2} 個")

    if system_fonts["ipa_gothic"]:
        for font in system_fonts["ipa_gothic"][:2]:
            print(f"✅ IPAGothic: {Path(font).name}")
            has_fonts = True
        if len(system_fonts["ipa_gothic"]) > 2:
            print(f"   ... 他 {len(system_fonts['ipa_gothic']) - 2} 個")

    if system_fonts["ipa_serif"]:
        for font in system_fonts["ipa_serif"][:2]:
            print(f"✅ IPASerif: {Path(font).name}")
            has_fonts = True

    if system_fonts["heiseifonts"]:
        print(f"⚠️ Heiseiフォント（フォールバック）: {len(system_fonts['heiseifonts'])} 個")

    if not has_fonts and not system_fonts["heiseifonts"]:
        print("❌ 日本語フォントが見つかりません")

    # 【フォントフォールバック設定】
    print("\n【フォントフォールバック設定】")
    print("label.py内での優先順序:")
    print("1. Noto Sans CJK JP (ゴシック体)", end=" ")
    if system_fonts["noto_cjk"]:
        print("✅")
    else:
        print("❌")

    print("2. IPA Gothic (フォールバック)", end=" ")
    if system_fonts["ipa_gothic"]:
        print("✅")
    else:
        print("❌")

    print("3. Heisei フォント", end=" ")
    if system_fonts["heiseifonts"]:
        print("✅")
    else:
        print("❌")

    print("4. Helvetica (最終フォールバック)", end=" ")
    if "Helvetica" in reportlab_fonts:
        print("✅")
    else:
        print("❌")

    # 【診断結果】
    print("\n【診断結果】")

    # フォント利用可能性を判定
    has_japanese_font = (
        system_fonts["noto_cjk"]
        or system_fonts["noto_sans"]
        or system_fonts["ipa_gothic"]
        or system_fonts["heiseifonts"]
    )
    has_preferred_font = system_fonts["noto_cjk"] or system_fonts["ipa_gothic"]

    if env_info["is_docker"]:
        print("✅ Docker環境でNoto CJKフォントが利用可能")
        print("✅ 日本語PDFの生成に問題ありません")
    elif env_info["is_pyodide"]:
        print("✅ Pyodide環境ではNoto Sans JPが自動ダウンロードされます")
        print("✅ 日本語PDFの生成に問題ありません")
    elif has_preferred_font:
        print("✅ 推奨フォント（Noto CJK/IPA Gothic）が利用可能")
        print("✅ 日本語PDFの生成に問題ありません")
    elif has_japanese_font:
        print("⚠️ 日本語フォント（Heiseiフォント）が利用可能")
        print("⚠️ 生成されるPDFはHeiseiフォントで出力されます（環境依存）")
    else:
        print("❌ 日本語フォント（Noto/IPA/Heisei）が利用できません")
        print("❌ PDF生成時にフォント警告が表示されます")

    # PDF分析結果
    if pdf_fonts:
        print("\n【PDF内のフォント情報】")
        for font_name, info in pdf_fonts.items():
            embedded_str = "埋め込み済み ✅" if info["embedded"] else "埋め込まれていない ❌"
            print(f"- {font_name}: {embedded_str} ({info['type']})")

    # 【推奨事項】
    print("\n【推奨事項】")

    if env_info["is_docker"]:
        print("✅ Docker環境での実行を継続してください")
    elif env_info["is_pyodide"]:
        print("✅ ブラウザ環境での実行を継続してください")
    elif has_preferred_font:
        print("✅ フォント環境が正しく設定されています")
    elif has_japanese_font:
        print("1. Docker環境の使用を推奨します:")
        print("   docker compose up -d\n")
        print("2. または、IPAフォントのインストール:")
        if env_info["platform"] == "win32":
            print("   - https://moji.or.jp/ipafont/ からダウンロード")
            print("   - Fontsフォルダに配置")
        elif env_info["platform"] == "darwin":
            print("   brew install --cask font-ipa")
        else:
            print("   Ubuntu/Debian: sudo apt-get install fonts-ipafont")
            print("   Fedora/RHEL: sudo dnf install ipa-gothic-fonts")
    else:
        print("緊急: フォント環境がセットアップされていません\n")
        print("以下のいずれかの方法で解決してください:\n")
        print("1. **Docker環境の使用（推奨）**")
        print("   docker compose up -d\n")
        print("2. **IPAフォントのインストール**")
        if env_info["platform"] == "win32":
            print("   Windows:")
            print("   - https://moji.or.jp/ipafont/ からダウンロード")
            print("   - Fontsフォルダに配置\n")
        elif env_info["platform"] == "darwin":
            print("   macOS:")
            print("   brew install --cask font-ipa\n")
        else:
            print("   Linux:")
            print("   Ubuntu/Debian: sudo apt-get install fonts-ipafont")
            print("   Fedora/RHEL: sudo dnf install ipa-gothic-fonts\n")
        print("3. **フォントパスを手動指定**")
        print("   create_label(..., font_path='/path/to/font.ttf')")

    print("\n" + "=" * 50 + "\n")


def diagnose_fonts(pdf_path: Optional[str] = None):
    """
    フォント環境を診断

    Args:
        pdf_path: 分析するPDFファイルパス（オプション）
    """
    # 診断実行
    env_info = detect_environment()
    system_fonts = find_system_fonts()
    reportlab_fonts = check_reportlab_fonts()
    label_config = read_label_py_font_config()
    pdf_fonts = analyze_pdf_fonts(pdf_path) if pdf_path else None

    # レポート出力
    print_diagnostic_report(env_info, system_fonts, reportlab_fonts, label_config, pdf_fonts)

    return {
        "environment": env_info,
        "system_fonts": system_fonts,
        "reportlab_fonts": reportlab_fonts,
        "label_config": label_config,
        "pdf_fonts": pdf_fonts,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="フォント診断スクリプト")
    parser.add_argument(
        "--pdf",
        type=str,
        help="分析するPDFファイルのパス",
        default=None,
    )

    args = parser.parse_args()
    diagnose_fonts(args.pdf)
