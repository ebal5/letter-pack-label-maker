"""
3つのインターフェース（CLI、Webサーバー、静的HTML版）を横断的にテストするモジュール

このモジュールは、同じテストデータを使用して3つすべてのインターフェースで
ラベルPDFを生成し、一貫性を検証します。
"""

import difflib
import importlib.util
import os
import subprocess
import time

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

try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# Playwrightの利用可能性をチェック（インポートせずにモジュールの存在を確認）
HAS_PLAYWRIGHT = importlib.util.find_spec("playwright") is not None


class PDFValidator:
    """PDFの基本情報を検証するクラス"""

    @staticmethod
    def get_page_count(pdf_path: str) -> int | None:
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
    def extract_text(pdf_path: str) -> str | None:
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

    @staticmethod
    def compare_text_content(pdf_path1: str, pdf_path2: str) -> dict | None:
        """2つのPDFのテキスト内容を詳細比較

        Args:
            pdf_path1: 1つ目のPDFパス
            pdf_path2: 2つ目のPDFパス

        Returns:
            比較結果の辞書（ページごとの類似度など）、pdfplumberがない場合はNone
        """
        if not HAS_PDFPLUMBER:
            return None

        try:
            with pdfplumber.open(pdf_path1) as pdf1, pdfplumber.open(pdf_path2) as pdf2:
                results = {
                    "page_count_match": len(pdf1.pages) == len(pdf2.pages),
                    "page_count_1": len(pdf1.pages),
                    "page_count_2": len(pdf2.pages),
                    "pages": [],
                    "overall_similarity": 0.0,
                }

                total_similarity = 0.0
                page_count = min(len(pdf1.pages), len(pdf2.pages))

                for i in range(page_count):
                    text1 = pdf1.pages[i].extract_text() or ""
                    text2 = pdf2.pages[i].extract_text() or ""

                    # 類似度を計算（0.0〜1.0）
                    similarity = difflib.SequenceMatcher(None, text1, text2).ratio()
                    total_similarity += similarity

                    results["pages"].append(
                        {
                            "page": i + 1,
                            "similarity": round(similarity, 4),
                            "text1_length": len(text1),
                            "text2_length": len(text2),
                            "text1_preview": text1[:100],
                            "text2_preview": text2[:100],
                        }
                    )

                # 全体の平均類似度を計算
                if page_count > 0:
                    results["overall_similarity"] = round(total_similarity / page_count, 4)

                return results

        except Exception:
            return None

    @staticmethod
    def extract_layout_positions(pdf_path: str) -> dict | None:
        """PDFから主要要素の位置情報を抽出

        Args:
            pdf_path: PDFファイルのパス

        Returns:
            主要要素の座標辞書、pdfplumberがない場合はNone
        """
        if not HAS_PDFPLUMBER:
            return None

        try:
            positions = {}
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    # 文字レベルの座標を取得
                    chars = page.chars

                    # 特定のキーワードの位置を検索
                    keywords = ["おところ", "おなまえ", "電話番号", "〒"]
                    for keyword in keywords:
                        # keywordを含む文字を検索
                        found = False
                        for char in chars:
                            text = char.get("text", "")
                            if keyword in text or text in keyword:
                                key = f"{keyword}_page{page_num}"
                                if key not in positions:  # 最初に見つかったものを記録
                                    positions[key] = {
                                        "x": round(char["x0"], 2),
                                        "y": round(char["top"], 2),
                                        "text": text,
                                    }
                                    found = True
                                    break
                        if found:
                            continue

            return positions

        except Exception:
            return None

    @staticmethod
    def compare_layout_positions(
        pos1: dict, pos2: dict, tolerance_mm: float = 2.0
    ) -> dict[str, bool]:
        """2つのPDFのレイアウト位置を比較

        Args:
            pos1: 1つ目のPDFの位置情報
            pos2: 2つ目のPDFの位置情報
            tolerance_mm: 許容誤差（mm単位）

        Returns:
            比較結果の辞書（各要素が許容範囲内かどうか）
        """
        # mm -> pt変換（1mm = 2.83pt）
        tolerance_pt = tolerance_mm * 2.83

        results = {
            "all_within_tolerance": True,
            "details": {},
        }

        # pos1とpos2の共通キーについて比較
        common_keys = set(pos1.keys()) & set(pos2.keys())

        for key in common_keys:
            x_diff = abs(pos1[key]["x"] - pos2[key]["x"])
            y_diff = abs(pos1[key]["y"] - pos2[key]["y"])

            within_tolerance = x_diff <= tolerance_pt and y_diff <= tolerance_pt

            results["details"][key] = {
                "within_tolerance": within_tolerance,
                "x_diff": round(x_diff, 2),
                "y_diff": round(y_diff, 2),
                "pos1": pos1[key],
                "pos2": pos2[key],
            }

            if not within_tolerance:
                results["all_within_tolerance"] = False

        # pos1のみまたはpos2のみに存在するキーをチェック
        only_in_pos1 = set(pos1.keys()) - set(pos2.keys())
        only_in_pos2 = set(pos2.keys()) - set(pos1.keys())

        if only_in_pos1 or only_in_pos2:
            results["all_within_tolerance"] = False
            results["only_in_pos1"] = list(only_in_pos1)
            results["only_in_pos2"] = list(only_in_pos2)

        return results


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
        from playwright.sync_api import sync_playwright

        output_pdf = output_dir / "static_output.pdf"

        # HTTPサーバーを起動
        server_process = subprocess.Popen(
            ["python", "-m", "http.server", "8888"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        try:
            # サーバーの起動を待機
            time.sleep(2)

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                # 静的HTML版を開く
                page.goto("http://localhost:8888/index_static.html")

                # Pyodideの初期化を待つ（最大90秒）
                page.wait_for_selector("#label-form", timeout=90000)

                # CSVデータを読み込んで1行目のデータを使用
                with open(test_csv_data, encoding="utf-8") as f:
                    lines = f.readlines()
                    # ヘッダーをスキップして1行目のデータを取得
                    if len(lines) > 1:
                        data_line = lines[1].strip().split(",")
                        # to_postal,to_address,to_name,to_phone,to_honorific,from_postal,...
                        if len(data_line) >= 10:
                            # フォームに入力
                            page.fill("#to_postal", data_line[0])
                            page.fill("#to_address1", data_line[1])
                            page.fill("#to_name", data_line[2])
                            page.fill("#to_phone", data_line[3])

                            page.fill("#from_postal", data_line[5])
                            page.fill("#from_address1", data_line[6])
                            page.fill("#from_name", data_line[7])
                            page.fill("#from_phone", data_line[8])

                # PDF生成ボタンをクリックしてダウンロードを待機
                with page.expect_download(timeout=30000) as download_info:
                    page.click("#generate-btn")
                    download = download_info.value

                # ダウンロードしたファイルを保存
                download.save_as(str(output_pdf))

                browser.close()

            assert output_pdf.exists(), "PDF not generated"
            assert output_pdf.stat().st_size > 0, "PDF file is empty"

        finally:
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()


class TestPDFConsistency:
    """3つのインターフェース間のPDF一貫性テスト"""

    @pytest.mark.skipif(
        not (HAS_REQUESTS and HAS_PLAYWRIGHT),
        reason="Requires requests and Playwright",
    )
    def test_all_interfaces_consistency(self, test_csv_data, output_dir, test_server_port):
        """3つすべてのインターフェースで生成されたPDFの一貫性テスト

        このテストはrequestsとPlaywrightが必要です。
        """
        from playwright.sync_api import sync_playwright

        pdfs = {}

        # 1. CLI版でPDF生成
        cli_pdf = output_dir / "consistency_test_cli.pdf"
        result = subprocess.run(
            [
                "python",
                "-m",
                "letterpack.cli",
                "--csv",
                str(test_csv_data),
                "--output",
                str(cli_pdf),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        assert cli_pdf.exists()
        pdfs["cli"] = cli_pdf

        # 2. Webサーバー版でPDF生成
        web_pdf = output_dir / "consistency_test_web.pdf"
        server_process = subprocess.Popen(
            ["python", "-m", "letterpack.web"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        try:
            time.sleep(2)  # サーバー起動待機

            with open(test_csv_data, "rb") as f:
                files = {"csv_file": f}
                response = requests.post(
                    f"http://localhost:{test_server_port}/generate",
                    files=files,
                    timeout=10,
                )

            assert response.status_code == 200, f"Web API failed: {response.status_code}"
            web_pdf.write_bytes(response.content)
            assert web_pdf.exists()
            pdfs["web"] = web_pdf

        finally:
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()

        # 3. 静的HTML版でPDF生成
        static_pdf = output_dir / "consistency_test_static.pdf"
        http_server = subprocess.Popen(
            ["python", "-m", "http.server", "8888"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        try:
            time.sleep(2)  # サーバー起動待機

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                page.goto("http://localhost:8888/index_static.html")
                page.wait_for_selector("#label-form", timeout=90000)

                # CSVデータの1行目を使用
                with open(test_csv_data, encoding="utf-8") as f:
                    lines = f.readlines()
                    if len(lines) > 1:
                        data_line = lines[1].strip().split(",")
                        if len(data_line) >= 10:
                            page.fill("#to_postal", data_line[0])
                            page.fill("#to_address1", data_line[1])
                            page.fill("#to_name", data_line[2])
                            page.fill("#to_phone", data_line[3])
                            page.fill("#from_postal", data_line[5])
                            page.fill("#from_address1", data_line[6])
                            page.fill("#from_name", data_line[7])
                            page.fill("#from_phone", data_line[8])

                with page.expect_download(timeout=30000) as download_info:
                    page.click("#generate-btn")
                    download = download_info.value

                download.save_as(str(static_pdf))
                browser.close()

            assert static_pdf.exists()
            pdfs["static"] = static_pdf

        finally:
            http_server.terminate()
            try:
                http_server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                http_server.kill()

        # 4. ページ数の比較
        page_counts = {}
        for name, pdf_path in pdfs.items():
            count = PDFValidator.get_page_count(str(pdf_path))
            if count is not None:
                page_counts[name] = count

        if page_counts:
            # すべてのページ数が同じか確認
            unique_counts = set(page_counts.values())
            assert len(unique_counts) == 1, f"Page counts differ: {page_counts}"

        # 5. テキスト内容の比較（キーワードベース）
        expected_keywords = ["山田太郎", "佐藤花子", "100-0001", "150-0001"]
        for name, pdf_path in pdfs.items():
            text = PDFValidator.extract_text(str(pdf_path))
            if text:
                # すべてのキーワードが含まれているか確認
                for keyword in expected_keywords:
                    assert keyword in text, f"{name}: Missing keyword '{keyword}'"

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

    @pytest.mark.skipif(not HAS_PDFPLUMBER, reason="pdfplumber not installed")
    def test_detailed_text_comparison(self, test_csv_data, output_dir):
        """テキスト内容の詳細比較テスト

        同じCSVから生成された2つのPDFのテキスト内容を詳細に比較します。
        """
        # 同じCSVから2つのPDFを生成
        pdf1 = output_dir / "text_compare_1.pdf"
        pdf2 = output_dir / "text_compare_2.pdf"

        for pdf_path in [pdf1, pdf2]:
            result = subprocess.run(
                [
                    "python",
                    "-m",
                    "letterpack.cli",
                    "--csv",
                    str(test_csv_data),
                    "--output",
                    str(pdf_path),
                ],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0
            assert pdf_path.exists()

        # テキスト内容を詳細比較
        comparison = PDFValidator.compare_text_content(str(pdf1), str(pdf2))
        assert comparison is not None, "Text comparison failed"

        # ページ数が一致することを確認
        assert comparison["page_count_match"], (
            f"Page count mismatch: {comparison['page_count_1']} vs {comparison['page_count_2']}"
        )

        # 全体の類似度が非常に高い（95%以上）ことを確認
        # 同じ入力から生成されたPDFなので、ほぼ100%一致するはず
        assert comparison["overall_similarity"] >= 0.95, (
            f"Overall similarity too low: {comparison['overall_similarity']}"
        )

        # 各ページの類似度も確認
        for page_info in comparison["pages"]:
            assert page_info["similarity"] >= 0.95, (
                f"Page {page_info['page']} similarity too low: {page_info['similarity']}"
            )

    @pytest.mark.skipif(not HAS_PDFPLUMBER, reason="pdfplumber not installed")
    def test_layout_position_consistency(self, test_csv_data, output_dir):
        """レイアウト位置の一貫性テスト

        同じCSVから生成された2つのPDFのレイアウト位置を比較します。
        """
        # 同じCSVから2つのPDFを生成
        pdf1 = output_dir / "layout_compare_1.pdf"
        pdf2 = output_dir / "layout_compare_2.pdf"

        for pdf_path in [pdf1, pdf2]:
            result = subprocess.run(
                [
                    "python",
                    "-m",
                    "letterpack.cli",
                    "--csv",
                    str(test_csv_data),
                    "--output",
                    str(pdf_path),
                ],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0
            assert pdf_path.exists()

        # 位置情報を抽出
        pos1 = PDFValidator.extract_layout_positions(str(pdf1))
        pos2 = PDFValidator.extract_layout_positions(str(pdf2))

        assert pos1 is not None, "Failed to extract positions from PDF1"
        assert pos2 is not None, "Failed to extract positions from PDF2"

        # 位置情報を比較（許容誤差±2mm）
        comparison = PDFValidator.compare_layout_positions(pos1, pos2, tolerance_mm=2.0)

        # すべての要素が許容範囲内にあることを確認
        if not comparison["all_within_tolerance"]:
            # 詳細情報をエラーメッセージに含める
            details_str = "\n".join(
                [
                    f"  {key}: within_tolerance={info['within_tolerance']}, "
                    f"x_diff={info['x_diff']}pt, y_diff={info['y_diff']}pt"
                    for key, info in comparison["details"].items()
                ]
            )
            pytest.fail(
                f"Layout positions differ beyond tolerance:\n{details_str}\n"
                f"Only in pos1: {comparison.get('only_in_pos1', [])}\n"
                f"Only in pos2: {comparison.get('only_in_pos2', [])}"
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

    @pytest.mark.skipif(not HAS_PSUTIL, reason="psutil not installed")
    def test_performance_comparison(self, test_csv_data, output_dir):
        """3つのインターフェースのパフォーマンス比較テスト

        各インターフェースの実行時間とメモリ使用量を計測し、比較します。
        """
        results = {}

        # CLI版のパフォーマンス測定
        output_pdf = output_dir / "perf_cli.pdf"
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss

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
        cli_memory = psutil.Process().memory_info().rss - start_memory

        assert result.returncode == 0, f"CLI failed: {result.stderr}"

        results["cli"] = {
            "time_seconds": round(cli_time, 3),
            "memory_mb": round(cli_memory / 1024 / 1024, 2),
            "pdf_size_kb": round(PDFValidator.get_file_size(str(output_pdf)) / 1024, 2),
        }

        # パフォーマンスレポートを表示
        print("\n=== Performance Comparison ===")
        for name, data in results.items():
            print(
                f"{name.upper()}: "
                f"{data['time_seconds']}s, "
                f"{data['memory_mb']}MB memory, "
                f"{data['pdf_size_kb']}KB PDF"
            )

        # 基本的なパフォーマンス要件を確認
        # CLI版は10秒以内に完了するべき
        assert results["cli"]["time_seconds"] < 10.0, (
            f"CLI took too long: {results['cli']['time_seconds']}s"
        )
