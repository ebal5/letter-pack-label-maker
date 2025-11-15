"""
Tests for Performance Metrics

パフォーマンス計測のテスト
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# tools/performance_metrics.pyをインポートできるようにパスを追加
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from performance_metrics import PerformanceComparison, PerformanceMetrics, PerformanceMonitor


@pytest.fixture
def performance_monitor():
    """パフォーマンスモニターのフィクスチャ"""
    config_path = (
        Path(__file__).parent.parent / ".claude/skills/deployment-verification/config.yaml"
    )
    return PerformanceMonitor(config_path)


@pytest.fixture
def sample_metrics():
    """サンプルメトリクスのフィクスチャ"""
    return PerformanceMetrics(
        target="github-pages",
        timestamp="2025-01-01T00:00:00",
        page_load_ms=1500.0,
        pyodide_init_ms=45000.0,
        font_download_ms=2000.0,
        first_contentful_paint_ms=800.0,
        memory_mb=150.0,
    )


@pytest.fixture
def baseline_metrics():
    """ベースラインメトリクスのフィクスチャ"""
    return PerformanceMetrics(
        target="github-pages",
        timestamp="2024-12-01T00:00:00",
        page_load_ms=1200.0,
        pyodide_init_ms=40000.0,
        font_download_ms=1800.0,
        first_contentful_paint_ms=700.0,
        memory_mb=140.0,
    )


class TestPerformanceMetrics:
    """PerformanceMetricsデータクラスのテスト"""

    def test_metrics_creation(self, sample_metrics):
        """メトリクスの作成テスト"""
        assert sample_metrics.target == "github-pages"
        assert sample_metrics.page_load_ms == 1500.0
        assert sample_metrics.pyodide_init_ms == 45000.0

    def test_metrics_serialization(self, sample_metrics, tmp_path):
        """メトリクスのシリアライズテスト"""
        from dataclasses import asdict

        data = asdict(sample_metrics)

        # JSONに変換できるか確認
        json_str = json.dumps(data)
        assert json_str is not None

        # 復元できるか確認
        restored_data = json.loads(json_str)
        restored_metrics = PerformanceMetrics(**restored_data)

        assert restored_metrics.target == sample_metrics.target
        assert restored_metrics.page_load_ms == sample_metrics.page_load_ms


class TestPerformanceMonitor:
    """PerformanceMonitorクラスのテスト"""

    def test_monitor_initialization(self, performance_monitor):
        """モニターの初期化テスト"""
        assert performance_monitor is not None
        assert performance_monitor.config is not None

    def test_save_and_load_metrics(self, performance_monitor, sample_metrics, tmp_path):
        """メトリクスの保存と読み込みテスト"""
        metrics_file = tmp_path / "test_metrics.json"

        # 保存
        metrics_dict = {"github-pages": sample_metrics}
        performance_monitor.save_metrics(metrics_dict, metrics_file)

        assert metrics_file.exists()

        # 読み込み
        loaded_metrics = performance_monitor.load_baseline(metrics_file)

        assert loaded_metrics is not None
        assert "github-pages" in loaded_metrics
        assert loaded_metrics["github-pages"].page_load_ms == sample_metrics.page_load_ms

    def test_load_nonexistent_baseline(self, performance_monitor, tmp_path):
        """存在しないベースラインの読み込みテスト"""
        nonexistent_file = tmp_path / "nonexistent.json"

        loaded = performance_monitor.load_baseline(nonexistent_file)

        assert loaded is None

    def test_compare_metrics(self, performance_monitor, baseline_metrics, sample_metrics):
        """メトリクスの比較テスト"""
        comparisons = performance_monitor.compare_metrics(baseline_metrics, sample_metrics)

        assert len(comparisons) > 0

        # ページロード時間の比較を確認
        page_load_comp = next((c for c in comparisons if c.metric_name == "Page Load Time"), None)

        assert page_load_comp is not None
        assert page_load_comp.baseline_value == 1200.0
        assert page_load_comp.current_value == 1500.0
        # (1500 - 1200) / 1200 * 100 = 25%
        assert abs(page_load_comp.change_percent - 25.0) < 0.1

    def test_report_generation(self, performance_monitor, sample_metrics, baseline_metrics):
        """レポート生成のテスト"""
        metrics_dict = {"github-pages": sample_metrics}
        baselines_dict = {"github-pages": baseline_metrics}

        report = performance_monitor.generate_report(metrics_dict, baselines_dict)

        assert report is not None
        assert "Performance Metrics Report" in report
        assert "github-pages" in report.lower()
        assert "Page Load" in report


class TestPerformanceComparison:
    """PerformanceComparisonデータクラスのテスト"""

    def test_comparison_creation(self):
        """比較結果の作成テスト"""
        comp = PerformanceComparison(
            metric_name="Page Load Time",
            baseline_value=1000.0,
            current_value=1200.0,
            change_percent=20.0,
            regression=True,
            warning=True,
        )

        assert comp.metric_name == "Page Load Time"
        assert comp.change_percent == 20.0
        assert comp.regression is True
        assert comp.warning is True

    def test_comparison_no_regression(self):
        """回帰なしの比較テスト"""
        comp = PerformanceComparison(
            metric_name="Page Load Time",
            baseline_value=1000.0,
            current_value=1050.0,
            change_percent=5.0,
            regression=False,
            warning=False,
        )

        assert comp.regression is False
        assert comp.warning is False


@pytest.mark.performance
@pytest.mark.asyncio
@pytest.mark.slow
class TestGitHubPagesPerformance:
    """GitHub Pagesパフォーマンステスト"""

    async def test_measure_github_pages(self, performance_monitor):
        """GitHub Pagesのパフォーマンス計測テスト"""
        config = performance_monitor.config.get("github_pages", {})
        url = config.get("production_url", "https://ebal5.github.io/letter-pack-label-maker/")

        metrics = await performance_monitor.measure_github_pages(url)

        assert metrics is not None
        assert metrics.target == "github-pages"
        assert metrics.timestamp is not None

        # ページロード時間が計測されているか確認
        if metrics.page_load_ms is not None:
            assert metrics.page_load_ms > 0, "Page load time should be positive"

            # 閾値チェック
            threshold = config.get("performance_thresholds", {}).get("page_load_ms", 3000)
            assert metrics.page_load_ms < threshold * 2, (
                f"Page load extremely slow: {metrics.page_load_ms:.0f}ms"
            )

    async def test_performance_regression_detection(
        self, performance_monitor, baseline_metrics, tmp_path
    ):
        """パフォーマンス回帰検出のテスト"""
        # ベースラインを保存
        baseline_file = tmp_path / "baseline.json"
        baseline_dict = {"github-pages": baseline_metrics}
        performance_monitor.save_metrics(baseline_dict, baseline_file)

        # 現在のメトリクスを計測
        config = performance_monitor.config.get("github_pages", {})
        url = config.get("production_url", "https://ebal5.github.io/letter-pack-label-maker/")

        current_metrics = await performance_monitor.measure_github_pages(url)

        # ベースラインを読み込み
        baselines = performance_monitor.load_baseline(baseline_file)
        assert baselines is not None

        # 比較
        if current_metrics.page_load_ms is not None:
            comparisons = performance_monitor.compare_metrics(
                baselines["github-pages"], current_metrics
            )

            # 比較結果が取得できることを確認
            assert len(comparisons) > 0


@pytest.mark.performance
@pytest.mark.docker
@pytest.mark.slow
class TestDockerPerformance:
    """Dockerパフォーマンステスト"""

    def test_measure_docker_startup(self, performance_monitor):
        """Dockerの起動時間計測テスト"""
        try:
            import docker

            # Dockerデーモンが動いているか確認
            client = docker.from_env()
            client.ping()
        except Exception:
            pytest.skip("Docker not available")

        metrics = performance_monitor.measure_docker_startup()

        assert metrics is not None
        assert metrics.target == "docker"

        # 起動時間が計測されているか確認
        if metrics.docker_startup_ms is not None:
            assert metrics.docker_startup_ms > 0, "Docker startup time should be positive"


@pytest.mark.performance
@pytest.mark.integration
class TestPerformanceIntegration:
    """パフォーマンス統合テスト"""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_full_performance_measurement(self, performance_monitor, tmp_path):
        """完全なパフォーマンス計測テスト"""
        # GitHub Pagesの計測
        config = performance_monitor.config.get("github_pages", {})
        url = config.get("production_url", "https://ebal5.github.io/letter-pack-label-maker/")

        github_metrics = await performance_monitor.measure_github_pages(url)

        # メトリクスの保存
        output_file = tmp_path / "metrics.json"
        metrics_dict = {"github-pages": github_metrics}
        performance_monitor.save_metrics(metrics_dict, output_file)

        assert output_file.exists()

        # レポートの生成
        report = performance_monitor.generate_report(metrics_dict)

        assert report is not None
        assert len(report) > 0
