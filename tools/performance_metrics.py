#!/usr/bin/env python3
"""
Performance Metrics Tool

このスクリプトは、Letter Pack Label Makerのパフォーマンスを計測します。
GitHub Pages、Docker環境、ローカル環境のパフォーマンスメトリクスを収集し、
ベースラインと比較してパフォーマンスの回帰を検出します。
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("Warning: Playwright not installed. Install with: uv run playwright install chromium")
    async_playwright = None

try:
    import psutil
except ImportError:
    print("Warning: psutil not installed. Install with: uv pip install psutil")
    psutil = None


@dataclass
class PerformanceMetrics:
    """パフォーマンスメトリクス"""

    target: str
    timestamp: str
    page_load_ms: float | None = None
    pyodide_init_ms: float | None = None
    font_download_ms: float | None = None
    time_to_interactive_ms: float | None = None
    first_contentful_paint_ms: float | None = None
    largest_contentful_paint_ms: float | None = None
    memory_mb: float | None = None
    docker_startup_ms: float | None = None
    pdf_generation_ms: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceComparison:
    """パフォーマンス比較結果"""

    metric_name: str
    baseline_value: float
    current_value: float
    change_percent: float
    regression: bool
    warning: bool


class PerformanceMonitor:
    """パフォーマンス監視クラス"""

    def __init__(self, config_path: str | Path | None = None):
        """初期化

        Args:
            config_path: 設定ファイルのパス
        """
        if config_path is None:
            config_path = (
                Path(__file__).parent.parent / ".claude/skills/deployment-verification/config.yaml"
            )
        else:
            config_path = Path(config_path)

        if config_path.exists():
            with open(config_path, encoding="utf-8") as f:
                self.config = yaml.safe_load(f)
        else:
            print(f"Warning: Config file not found at {config_path}, using defaults")
            self.config = {}

        self.debug = self.config.get("debug", {}).get("enabled", False)

    def _log(self, message: str, level: str = "INFO"):
        """ログメッセージを出力"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if level == "DEBUG" and not self.debug:
            return
        print(f"[{timestamp}] [{level}] {message}")

    async def measure_github_pages(self, url: str) -> PerformanceMetrics:
        """GitHub Pagesのパフォーマンスを計測

        Args:
            url: 計測するURL

        Returns:
            パフォーマンスメトリクス
        """
        self._log(f"Measuring GitHub Pages performance: {url}")

        metrics = PerformanceMetrics(target="github-pages", timestamp=datetime.now().isoformat())

        if async_playwright is None:
            self._log("Playwright not available, skipping measurement", "WARNING")
            return metrics

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page()

                # ページロード時間を計測
                start_time = time.time()
                await page.goto(url, wait_until="domcontentloaded")
                load_time = (time.time() - start_time) * 1000
                metrics.page_load_ms = load_time

                self._log(f"Page load time: {load_time:.0f}ms")

                # Playwrightのパフォーマンスメトリクスを取得
                try:
                    perf_data = await page.evaluate(
                        """
                        () => {
                            const perfData = performance.getEntriesByType('navigation')[0];
                            const paintData = performance.getEntriesByType('paint');

                            const fcp = paintData.find(p => p.name === 'first-contentful-paint');
                            const lcp = paintData.find(p => p.name === 'largest-contentful-paint');

                            return {
                                domContentLoaded: perfData ? perfData.domContentLoadedEventEnd - perfData.fetchStart : null,
                                fcp: fcp ? fcp.startTime : null,
                                lcp: lcp ? lcp.startTime : null,
                            };
                        }
                    """
                    )

                    if perf_data.get("fcp"):
                        metrics.first_contentful_paint_ms = perf_data["fcp"]
                        self._log(f"First Contentful Paint: {perf_data['fcp']:.0f}ms")

                    if perf_data.get("lcp"):
                        metrics.largest_contentful_paint_ms = perf_data["lcp"]
                        self._log(f"Largest Contentful Paint: {perf_data['lcp']:.0f}ms")

                except Exception as e:
                    self._log(f"Could not get performance metrics: {e}", "WARNING")

                # Pyodide初期化時間を計測
                self._log("Waiting for Pyodide initialization...")
                pyodide_start = time.time()
                try:
                    # config.yamlからタイムアウト値を読み込む
                    config = self.config.get("github_pages", {})
                    thresholds = config.get("performance_thresholds", {})
                    timeout_ms = int(thresholds.get("pyodide_init_ms", 90000))

                    await page.wait_for_selector("#label-form", timeout=timeout_ms)
                    pyodide_time = (time.time() - pyodide_start) * 1000
                    metrics.pyodide_init_ms = pyodide_time
                    self._log(f"Pyodide initialization: {pyodide_time:.0f}ms")
                except asyncio.TimeoutError:
                    self._log(f"Pyodide initialization timeout after {timeout_ms}ms", "WARNING")
                except Exception as e:
                    self._log(f"Pyodide initialization failed: {e}", "WARNING")

                # メモリ使用量
                if psutil is not None:
                    metrics.memory_mb = psutil.Process().memory_info().rss / (1024 * 1024)
                    self._log(f"Memory usage: {metrics.memory_mb:.2f}MB")

                await browser.close()

        except Exception as e:
            self._log(f"Performance measurement failed: {e}", "ERROR")

        return metrics

    def measure_docker_startup(self) -> PerformanceMetrics:
        """Dockerの起動時間を計測

        Returns:
            パフォーマンスメトリクス
        """
        self._log("Measuring Docker startup performance")

        metrics = PerformanceMetrics(target="docker", timestamp=datetime.now().isoformat())

        try:
            import docker

            client = docker.from_env()

            # コンテナ起動時間を計測
            start_time = time.time()

            config = self.config.get("docker", {})
            image_name = config.get("image_name", "letterpack-web")
            image_tag = config.get("image_tag", "latest")
            full_image_name = f"{image_name}:{image_tag}"

            container = client.containers.run(
                full_image_name,
                detach=True,
                ports={"5000/tcp": 5000},
                environment={"SECRET_KEY": "test-key"},
                remove=True,
            )

            # ヘルスチェックまたは実行確認
            timeout = 30
            while time.time() - start_time < timeout:
                container.reload()
                state = container.attrs["State"]

                if "Health" in state and state["Health"]["Status"] == "healthy":
                    break
                elif state.get("Running"):
                    # ヘルスチェックがない場合、実行中になったら完了
                    break

                time.sleep(0.5)

            startup_time = (time.time() - start_time) * 1000
            metrics.docker_startup_ms = startup_time
            self._log(f"Docker startup time: {startup_time:.0f}ms")

            # クリーンアップ
            container.stop()

        except ImportError:
            self._log("Docker SDK not installed, skipping Docker metrics", "WARNING")
        except Exception as e:
            self._log(f"Docker measurement failed: {e}", "ERROR")

        return metrics

    def load_baseline(self, baseline_path: str | Path) -> dict[str, PerformanceMetrics] | None:
        """ベースラインメトリクスを読み込む

        Args:
            baseline_path: ベースラインファイルのパス

        Returns:
            ベースラインメトリクス、ファイルがない場合はNone
        """
        baseline_path = Path(baseline_path)

        if not baseline_path.exists():
            self._log(f"Baseline file not found: {baseline_path}", "WARNING")
            return None

        try:
            with open(baseline_path, encoding="utf-8") as f:
                data = json.load(f)

            baselines = {}
            for target, metric_data in data.items():
                baselines[target] = PerformanceMetrics(**metric_data)

            self._log(f"Loaded baseline from {baseline_path}")
            return baselines

        except Exception as e:
            self._log(f"Failed to load baseline: {e}", "ERROR")
            return None

    def save_metrics(self, metrics: dict[str, PerformanceMetrics], output_path: str | Path):
        """メトリクスをファイルに保存

        Args:
            metrics: 保存するメトリクス
            output_path: 出力先のパス
        """
        output_path = Path(output_path)

        data = {target: asdict(metric) for target, metric in metrics.items()}

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        self._log(f"Saved metrics to {output_path}")

    def compare_metrics(
        self,
        baseline: PerformanceMetrics,
        current: PerformanceMetrics,
    ) -> list[PerformanceComparison]:
        """メトリクスを比較

        Args:
            baseline: ベースラインメトリクス
            current: 現在のメトリクス

        Returns:
            比較結果のリスト
        """
        comparisons = []

        perf_config = self.config.get("performance", {})
        warning_threshold = perf_config.get("regression_warning_threshold", 10)
        error_threshold = perf_config.get("regression_error_threshold", 20)

        # 比較するメトリクスのリスト
        metrics_to_compare = [
            ("page_load_ms", "Page Load Time"),
            ("pyodide_init_ms", "Pyodide Initialization"),
            ("font_download_ms", "Font Download"),
            ("first_contentful_paint_ms", "First Contentful Paint"),
            ("largest_contentful_paint_ms", "Largest Contentful Paint"),
            ("docker_startup_ms", "Docker Startup"),
            ("pdf_generation_ms", "PDF Generation"),
        ]

        for metric_key, metric_name in metrics_to_compare:
            baseline_value = getattr(baseline, metric_key)
            current_value = getattr(current, metric_key)

            if baseline_value is None or current_value is None:
                continue

            change_percent = (current_value - baseline_value) / baseline_value * 100

            comparison = PerformanceComparison(
                metric_name=metric_name,
                baseline_value=baseline_value,
                current_value=current_value,
                change_percent=change_percent,
                regression=change_percent > error_threshold,
                warning=change_percent > warning_threshold,
            )

            comparisons.append(comparison)

        return comparisons

    def generate_report(
        self,
        metrics: dict[str, PerformanceMetrics],
        baselines: dict[str, PerformanceMetrics] | None = None,
    ) -> str:
        """パフォーマンスレポートを生成

        Args:
            metrics: 現在のメトリクス
            baselines: ベースラインメトリクス

        Returns:
            Markdownレポート
        """
        lines = [
            "# Performance Metrics Report",
            "",
            f"**Generated at**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
        ]

        # 各ターゲットのメトリクス
        for target, metric in metrics.items():
            lines.append(f"## {target.title()} Performance")
            lines.append("")

            if metric.page_load_ms is not None:
                lines.append(f"- **Page Load**: {metric.page_load_ms:.0f} ms")

            if metric.pyodide_init_ms is not None:
                lines.append(f"- **Pyodide Init**: {metric.pyodide_init_ms:.0f} ms")

            if metric.font_download_ms is not None:
                lines.append(f"- **Font Download**: {metric.font_download_ms:.0f} ms")

            if metric.first_contentful_paint_ms is not None:
                lines.append(
                    f"- **First Contentful Paint**: {metric.first_contentful_paint_ms:.0f} ms"
                )

            if metric.largest_contentful_paint_ms is not None:
                lines.append(
                    f"- **Largest Contentful Paint**: {metric.largest_contentful_paint_ms:.0f} ms"
                )

            if metric.docker_startup_ms is not None:
                lines.append(f"- **Docker Startup**: {metric.docker_startup_ms:.0f} ms")

            if metric.pdf_generation_ms is not None:
                lines.append(f"- **PDF Generation**: {metric.pdf_generation_ms:.0f} ms")

            if metric.memory_mb is not None:
                lines.append(f"- **Memory Usage**: {metric.memory_mb:.2f} MB")

            lines.append("")

            # ベースラインとの比較
            if baselines and target in baselines:
                baseline = baselines[target]
                comparisons = self.compare_metrics(baseline, metric)

                if comparisons:
                    lines.append("### Comparison with Baseline")
                    lines.append("")

                    for comp in comparisons:
                        status = "✅"
                        if comp.regression:
                            status = "❌"
                        elif comp.warning:
                            status = "⚠️"

                        lines.append(
                            f"- {status} **{comp.metric_name}**: "
                            f"{comp.baseline_value:.0f}ms → {comp.current_value:.0f}ms "
                            f"({comp.change_percent:+.1f}%)"
                        )

                    lines.append("")

        return "\n".join(lines)


async def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="Performance metrics tool for Letter Pack Label Maker"
    )
    parser.add_argument(
        "--target",
        choices=["all", "github-pages", "docker"],
        default="all",
        help="Measurement target",
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file",
    )
    parser.add_argument(
        "--baseline-file",
        type=str,
        help="Path to baseline metrics file",
    )
    parser.add_argument(
        "--output-file",
        type=str,
        default="performance-metrics.json",
        help="Output metrics file",
    )
    parser.add_argument(
        "--report-file",
        type=str,
        help="Output report file (markdown)",
    )

    args = parser.parse_args()

    monitor = PerformanceMonitor(args.config)
    metrics = {}

    # GitHub Pagesの計測
    if args.target in ["all", "github-pages"]:
        print("\n" + "=" * 60)
        print("Measuring GitHub Pages Performance")
        print("=" * 60 + "\n")

        config = monitor.config.get("github_pages", {})
        url = config.get("production_url", "https://ebal5.github.io/letter-pack-label-maker/")

        github_metrics = await monitor.measure_github_pages(url)
        metrics["github-pages"] = github_metrics

    # Dockerの計測
    if args.target in ["all", "docker"]:
        print("\n" + "=" * 60)
        print("Measuring Docker Performance")
        print("=" * 60 + "\n")

        docker_metrics = monitor.measure_docker_startup()
        metrics["docker"] = docker_metrics

    # ベースラインの読み込み
    baselines = None
    if args.baseline_file:
        baselines = monitor.load_baseline(args.baseline_file)

    # レポート生成
    print("\n" + "=" * 60)
    print("Performance Report")
    print("=" * 60 + "\n")

    report = monitor.generate_report(metrics, baselines)
    print(report)

    # メトリクスの保存
    monitor.save_metrics(metrics, args.output_file)

    # レポートの保存
    if args.report_file:
        Path(args.report_file).write_text(report, encoding="utf-8")
        print(f"\n📄 Report saved to: {args.report_file}")

    # 回帰チェック
    if baselines:
        has_regression = False
        for target, metric in metrics.items():
            if target in baselines:
                comparisons = monitor.compare_metrics(baselines[target], metric)
                if any(c.regression for c in comparisons):
                    has_regression = True
                    break

        if has_regression:
            print("\n❌ Performance regression detected!")
            sys.exit(1)
        else:
            print("\n✅ No performance regression detected")

    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
