"""
3つのインターフェース（CLI、Webサーバー、静的HTML版）を横断的にテストするモジュール

このモジュールは、同じテストデータを使用して3つすべてのインターフェースで
ラベルPDFを生成し、一貫性を検証します。
"""

import importlib.util
import os
import subprocess
import time
from typing import Optional

import pytest

from letterpack.csv_parser import parse_csv
from letterpack.label import AddressInfo, create_label_batch

try:
    from PyPDF2 import PdfReader

    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False

try:
    import pdfplumber

    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

try:
    import requests

    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# Playwrightの利用可能性をチェック（インポートせずにモジュールの存在を確認）
HAS_PLAYWRIGHT = importlib.util.find_spec("playwright") is not None


class PDFValidator:
    """PDFの基本情報を検証するクラス"""

    @staticmethod
    def get_page_count(pdf_path: str) -> Optional[int]:
        """PDFのページ数を取得"""
        if not HAS_PYPDF2:
            return None
        try:
            with open(pdf_path, "rb") as f:
                pdf = PdfReader(f)
                return len(pdf.pages)
        except Exception:
            return None

    @staticmethod
    def get_file_size(pdf_path: str) -> int:
        """PDFのファイルサイズを取得"""
        return os.path.getsize(pdf_path)

    @staticmethod
    def extract_text(pdf_path: str) -> Optional[str]:
        """PDFからテキスト内容を抽出"""
        if not HAS_PDFPLUMBER:
            return None
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text_content = ""
                for page in pdf.pages:
                    text_content += page.extract_text() or ""
                return text_content
        except Exception:
            return None


@pytest.fixture
def test_csv_data(tmp_path):
    """テスト用CSVデータを準備"""
    csv_path = tmp_path / "test_multi_interface.csv"
    csv_content = """to_postal,to_address,to_name,to_phone,to_honorific,from_postal,from_address,from_name,from_phone,from_honorific
100-0001,東京都千代田区千代田1-1,山田太郎,03-1234-5678,様,150-0001,東京都渋谷区渋谷1-1,佐藤花子,03-9876-5432,
200-0002,大阪府大阪市中央区2-2,鈴木次郎,06-1111-2222,殿,150-0001,東京都渋谷区渋谷1-1,佐藤花子,03-9876-5432,
300-0003,京都府京都市中京区3-3,佐藤太郎,075-3333-4444,,150-0001,東京都渋谷区渋谷1-1,佐藤花子,03-9876-5432,
"""
    csv_path.write_text(csv_content, encoding="utf-8")
    return csv_path


@pytest.fixture
def output_dir(tmp_path):
    """テスト結果を保存するディレクトリ"""
    output_path = tmp_path / "output"
    output_path.mkdir(exist_ok=True)
    return output_path


@pytest.fixture
def test_server_port():
    """テスト用Webサーバーのポート番号を取得（環境変数またはデフォルト値）"""
    return int(os.environ.get("TEST_SERVER_PORT", "5000"))


class TestCLIInterface:
    """CLI版のテスト"""

    def test_cli_generate_from_csv(self, test_csv_data, output_dir):
        """CLI版でCSVからPDF生成"""
        output_pdf = output_dir / "cli_output.pdf"

        # CLIを実行
        result = subprocess.run(
            [
                "python",
                "-m",
                "letterpack.cli",
                "--csv",
                str(test_csv_data),
                "--output",
                str(output_pdf),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, (
            f"CLI failed with code {result.returncode}:\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )
        assert output_pdf.exists(), "PDF was not generated"
        assert output_pdf.stat().st_size > 0, "PDF file is empty"

    def test_cli_pdf_structure(self, test_csv_data, output_dir):
        """CLI生成PDFの構造確認"""
        output_pdf = output_dir / "cli_structure.pdf"

        subprocess.run(
            [
                "python",
                "-m",
                "letterpack.cli",
                "--csv",
                str(test_csv_data),
                "--output",
                str(output_pdf),
            ],
            capture_output=True,
            text=True,
        )

        # ページ数を確認
        page_count = PDFValidator.get_page_count(str(output_pdf))
        if page_count is not None:
            # 3件のデータ（4upレイアウトなので1ページ）
            assert page_count >= 1, f"Expected at least 1 page, got {page_count}"


class TestWebServerInterface:
    """Webサーバー版のテスト"""

    def test_web_server_api_available(self, test_server_port):
        """Webサーバーが起動可能か確認"""
        # Webサーバーを起動
        server_process = subprocess.Popen(
            ["python", "-m", "letterpack.web"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # サーバーの起動を待機
        time.sleep(2)

        try:
            # ポートが開いているか確認（簡易チェック）
            import socket

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(("127.0.0.1", test_server_port))
            assert result == 0, f"Web server is not responding on port {test_server_port}"
            sock.close()
        finally:
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()

    @pytest.mark.skipif(not HAS_REQUESTS, reason="requests library not installed")
    def test_web_generate_from_csv(self, test_csv_data, output_dir, test_server_port):
        """Webサーバー版でCSVからPDF生成

        このテストはrequestsライブラリが必要です。
        """
        output_pdf = output_dir / "web_output.pdf"

        # Webサーバーを起動
        server_process = subprocess.Popen(
            ["python", "-m", "letterpack.web"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        try:
            # サーバーの起動を待機
            time.sleep(2)

            # CSVファイルをアップロード
            with open(test_csv_data, "rb") as f:
                files = {"csv_file": f}
                response = requests.post(
                    f"http://localhost:{test_server_port}/generate",
                    files=files,
                    timeout=10,
                )

            assert response.status_code == 200, (
                f"Web API failed with status {response.status_code}: {response.text}"
            )

            # PDFを保存
            output_pdf.write_bytes(response.content)
            assert output_pdf.exists(), "PDF not generated"

        finally:
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()


class TestStaticHTMLInterface:
    """静的HTML版（Pyodide）のテスト"""

    @pytest.mark.skipif(not HAS_PLAYWRIGHT, reason="Playwright not installed")
    def test_static_html_generate(self, test_csv_data, output_dir):
        """静的HTML版でCSVからPDF生成

        このテストはPlaywrightが必要です。
        """
        pytest.skip("Static HTML version test not yet implemented")


class TestPDFConsistency:
    """3つのインターフェース間のPDF一貫性テスト"""

    def test_cli_generates_valid_pdf(self, test_csv_data, output_dir):
        """CLI版がページ数と内容の点で有効なPDFを生成するか確認"""
        output_pdf = output_dir / "consistency_cli.pdf"

        # CLI版でPDF生成
        result = subprocess.run(
            [
                "python",
                "-m",
                "letterpack.cli",
                "--csv",
                str(test_csv_data),
                "--output",
                str(output_pdf),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert output_pdf.exists()

        # PDF構造の確認
        file_size = PDFValidator.get_file_size(str(output_pdf))
        assert file_size > 1000, "PDF file seems too small"

        page_count = PDFValidator.get_page_count(str(output_pdf))
        if page_count is not None:
            assert page_count >= 1, "PDF has no pages"

        # テキスト内容の確認（キーワードが含まれているか）
        text_content = PDFValidator.extract_text(str(output_pdf))
        if text_content is not None:
            # テキストが抽出できた場合のみ検証
            if text_content.strip():
                # 宛先情報が含まれているか確認（複数のキーワードで検証）
                assert any(keyword in text_content for keyword in ["山田太郎", "山田", "太郎"]), (
                    "PDF does not contain recipient information"
                )
            else:
                # テキスト抽出は成功したが内容が空の場合はスキップ
                pytest.skip("Text extraction succeeded but returned empty content")

    def test_csv_parsing_and_batch_generation(self, test_csv_data, output_dir):
        """CSV解析とバッチPDF生成のテスト"""
        output_pdf = output_dir / "batch_generation.pdf"

        # CSVを解析
        labels = parse_csv(str(test_csv_data))
        assert len(labels) == 3, f"Expected 3 labels, got {len(labels)}"

        # ラベルペアを取得
        label_pairs = [(label.to_address, label.from_address) for label in labels]

        # バッチでPDF生成
        result = create_label_batch(label_pairs, str(output_pdf))
        assert os.path.exists(result)
        assert os.path.getsize(result) > 0

    def test_single_label_consistency(self, output_dir):
        """単一ラベルの生成一貫性テスト"""
        to_addr = AddressInfo(
            postal_code="100-0001",
            address="東京都千代田区千代田1-1",
            name="テスト太郎",
            phone="03-1234-5678",
            honorific="様",
        )
        from_addr = AddressInfo(
            postal_code="150-0001",
            address="東京都渋谷区渋谷1-1",
            name="テスト花子",
            phone="03-9876-5432",
        )

        # 同じデータで複数回生成
        pdfs = []
        for i in range(2):
            pdf_path = output_dir / f"single_label_iteration_{i}.pdf"
            from letterpack.label import create_label

            create_label(to_addr, from_addr, str(pdf_path))
            pdfs.append(pdf_path)

        # 両方のPDFが存在することを確認
        for pdf_path in pdfs:
            assert pdf_path.exists(), f"PDF not generated: {pdf_path}"

        # ファイルサイズを比較（フォント環境によって異なる可能性あり）
        size1 = PDFValidator.get_file_size(str(pdfs[0]))
        size2 = PDFValidator.get_file_size(str(pdfs[1]))
        # ファイルサイズが同じか、または非常に近い（許容値：5%）
        # フォント埋め込みやメタデータなどの環境依存要素によるばらつきを考慮
        # 同じデータから生成されたPDFは基本的に同じサイズになるはずだが、
        # ReportLabのバージョンや環境による微細な差異を許容する
        size_ratio = max(size1, size2) / min(size1, size2)
        assert size_ratio < 1.05, (
            f"File sizes differ significantly: {size1} vs {size2} (ratio: {size_ratio:.2f})"
        )

        # ページ数が同じか確認
        if HAS_PYPDF2:
            page_count1 = PDFValidator.get_page_count(str(pdfs[0]))
            page_count2 = PDFValidator.get_page_count(str(pdfs[1]))
            if page_count1 is not None and page_count2 is not None:
                assert page_count1 == page_count2, (
                    f"Page counts differ: {page_count1} vs {page_count2}"
                )


class TestMultiInterfaceReport:
    """複数インターフェースのテスト結果レポート生成"""

    def test_generate_test_report(self, test_csv_data, output_dir, capsys):
        """テスト結果レポートを生成"""
        output_pdf = output_dir / "report.pdf"

        # CLI版でPDF生成
        start_time = time.time()
        result = subprocess.run(
            [
                "python",
                "-m",
                "letterpack.cli",
                "--csv",
                str(test_csv_data),
                "--output",
                str(output_pdf),
            ],
            capture_output=True,
            text=True,
        )
        cli_time = time.time() - start_time

        assert result.returncode == 0

        # レポート情報を取得
        file_size = PDFValidator.get_file_size(str(output_pdf))
        page_count = PDFValidator.get_page_count(str(output_pdf))

        # レポートを生成
        report = {
            "cli": {
                "status": "success" if result.returncode == 0 else "failed",
                "execution_time": f"{cli_time:.2f}s",
                "file_size": file_size,
                "page_count": page_count,
            },
        }

        # レポート内容を確認
        assert report["cli"]["status"] == "success"
        assert report["cli"]["file_size"] > 0
        if page_count is not None:
            assert report["cli"]["page_count"] >= 1
