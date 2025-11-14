"""
フォント診断スクリプトのテスト
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# toolsディレクトリをインポートパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from font_diagnostic import (
    analyze_pdf_fonts,
    check_reportlab_fonts,
    detect_environment,
    find_system_fonts,
    get_platform_font_dirs,
    print_diagnostic_report,
    read_label_py_font_config,
)


def test_detect_environment():
    """環境検出のテスト"""
    env = detect_environment()

    assert isinstance(env, dict)
    assert "platform" in env
    assert "is_docker" in env
    assert "is_pyodide" in env
    assert "python_version" in env
    assert "os_name" in env

    # platformは有効な値
    assert env["platform"] in ["linux", "darwin", "win32", "emscripten"]

    # booleanフィールド
    assert isinstance(env["is_docker"], bool)
    assert isinstance(env["is_pyodide"], bool)

    # python_versionは文字列
    assert isinstance(env["python_version"], str)
    assert "." in env["python_version"]


def test_get_platform_font_dirs():
    """プラットフォーム別フォントディレクトリ取得のテスト"""
    dirs = get_platform_font_dirs()

    assert isinstance(dirs, list)
    assert len(dirs) > 0
    assert all(isinstance(d, str) for d in dirs)

    # プラットフォーム固有のパスを確認
    if sys.platform == "win32":
        assert any("Windows" in d for d in dirs)
    elif sys.platform == "darwin":
        assert any("Library/Fonts" in d for d in dirs)
    else:  # Linux
        assert any("share/fonts" in d for d in dirs)


@patch("font_diagnostic.Path")
def test_find_system_fonts_empty(mock_path):
    """システムフォント検索のテスト（フォントなし）"""
    # 存在しないディレクトリをシミュレート
    mock_path.return_value.exists.return_value = False

    fonts = find_system_fonts()

    assert isinstance(fonts, dict)
    assert "noto_cjk" in fonts
    assert "noto_sans" in fonts
    assert "ipa_gothic" in fonts
    assert "ipa_serif" in fonts
    assert "heiseifonts" in fonts

    # すべて空リスト
    assert all(isinstance(v, list) for v in fonts.values())


def test_find_system_fonts_structure():
    """システムフォント検索の構造テスト"""
    fonts = find_system_fonts()

    assert isinstance(fonts, dict)
    required_keys = ["noto_cjk", "noto_sans", "ipa_gothic", "ipa_serif", "heiseifonts"]

    for key in required_keys:
        assert key in fonts
        assert isinstance(fonts[key], list)


def test_check_reportlab_fonts():
    """ReportLabフォントチェックのテスト"""
    fonts = check_reportlab_fonts()

    assert isinstance(fonts, list)
    # ReportLabがインストールされている場合のみチェック
    # 空リストの場合はImportErrorまたはエラー発生


@patch("reportlab.pdfbase.pdfmetrics.getRegisteredFontNames")
def test_check_reportlab_fonts_error(mock_get_fonts):
    """ReportLabフォントチェックのエラーハンドリング"""
    # エラーをシミュレート
    mock_get_fonts.side_effect = AttributeError("Test error")

    with patch("sys.stderr"):
        fonts = check_reportlab_fonts()

    assert fonts == []


@patch("font_diagnostic.Path")
def test_find_system_fonts_permission_error(mock_path_class):
    """システムフォント検索のパーミッションエラーハンドリング"""
    # Pathのインスタンスを作成
    mock_path = MagicMock()
    mock_path.exists.return_value = True
    mock_path.rglob.side_effect = PermissionError("Access denied")

    # Path()の戻り値を設定
    mock_path_class.return_value = mock_path

    fonts = find_system_fonts()

    # エラーでも空の結果を返す
    assert isinstance(fonts, dict)
    assert all(isinstance(v, list) for v in fonts.values())


def test_analyze_pdf_fonts_not_found():
    """存在しないPDFのテスト"""
    result = analyze_pdf_fonts("/nonexistent/file.pdf")
    assert result is None


def test_analyze_pdf_fonts_none_path():
    """Noneパスのテスト"""
    result = analyze_pdf_fonts(None)
    assert result is None


def test_print_diagnostic_report(capsys):
    """診断レポート出力のテスト"""
    env_info = detect_environment()
    system_fonts = find_system_fonts()
    reportlab_fonts = check_reportlab_fonts()
    label_config = read_label_py_font_config()

    print_diagnostic_report(env_info, system_fonts, reportlab_fonts, label_config)

    captured = capsys.readouterr()
    assert "フォント診断レポート" in captured.out
    assert "実行環境" in captured.out
    assert "ReportLab登録フォント" in captured.out
    assert "システムフォント" in captured.out


def test_print_diagnostic_report_with_pdf_fonts(capsys):
    """PDF情報を含む診断レポート出力のテスト"""
    env_info = detect_environment()
    system_fonts = find_system_fonts()
    reportlab_fonts = check_reportlab_fonts()
    label_config = read_label_py_font_config()
    pdf_fonts = {
        "TestFont": {"embedded": True, "type": "/Type1"},
    }

    print_diagnostic_report(env_info, system_fonts, reportlab_fonts, label_config, pdf_fonts)

    captured = capsys.readouterr()
    assert "PDF内のフォント情報" in captured.out
    assert "TestFont" in captured.out
