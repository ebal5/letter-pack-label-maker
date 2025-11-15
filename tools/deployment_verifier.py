#!/usr/bin/env python3
"""
Deployment Verification Tool

このスクリプトは、Letter Pack Label Makerのデプロイメントを検証します。
GitHub Pages、Docker環境、ローカル環境の3つのデプロイメント方法をサポートします。
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import time
from dataclasses import dataclass, field
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
    import requests
except ImportError:
    print("Warning: requests not installed. Install with: uv pip install requests")
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Warning: BeautifulSoup not installed. Install with: uv pip install beautifulsoup4")
    BeautifulSoup = None


@dataclass
class LinkCheckResult:
    """リンクチェックの結果"""

    url: str
    status: int | None
    ok: bool
    error: str | None = None
    is_external: bool = False


@dataclass
class VerificationResult:
    """検証結果の基本クラス"""

    success: bool
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class GitHubPagesVerificationResult(VerificationResult):
    """GitHub Pages検証の結果"""

    accessible: bool = False
    status_code: int | None = None
    page_load_time_ms: float | None = None
    pyodide_init_time_ms: float | None = None
    critical_elements_found: list[str] = field(default_factory=list)
    critical_elements_missing: list[str] = field(default_factory=list)
    link_check_results: list[LinkCheckResult] = field(default_factory=list)


@dataclass
class DockerVerificationResult(VerificationResult):
    """Docker検証の結果"""

    build_success: bool = False
    image_id: str | None = None
    image_size_mb: float | None = None
    container_started: bool = False
    health_check_passed: bool = False
    health_check_time_ms: float | None = None
    fonts_available: list[str] = field(default_factory=list)
    web_server_responding: bool = False


class DeploymentVerifier:
    """デプロイメント検証の基本クラス"""

    def __init__(self, config_path: str | Path | None = None):
        """初期化

        Args:
            config_path: 設定ファイルのパス。Noneの場合はデフォルト設定を使用
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
            self.config = self._get_default_config()

        self.debug = self.config.get("debug", {}).get("enabled", False)

    def _get_default_config(self) -> dict[str, Any]:
        """デフォルト設定を返す"""
        return {
            "github_pages": {
                "production_url": "https://ebal5.github.io/letter-pack-label-maker/",
                "performance_thresholds": {
                    "page_load_ms": 3000,
                    "pyodide_init_ms": 90000,
                },
            },
            "docker": {
                "image_name": "letterpack-web",
                "health_check_timeout": 30,
            },
        }

    def _log(self, message: str, level: str = "INFO"):
        """ログメッセージを出力

        Args:
            message: ログメッセージ
            level: ログレベル (INFO, WARNING, ERROR, DEBUG)
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if level == "DEBUG" and not self.debug:
            return
        print(f"[{timestamp}] [{level}] {message}")


class GitHubPagesVerifier(DeploymentVerifier):
    """GitHub Pages検証クラス"""

    async def verify(
        self, check_links: bool = True, measure_performance: bool = True
    ) -> GitHubPagesVerificationResult:
        """GitHub Pagesを検証

        Args:
            check_links: リンクチェックを実行するか
            measure_performance: パフォーマンスを計測するか

        Returns:
            検証結果
        """
        self._log("Starting GitHub Pages verification")

        result = GitHubPagesVerificationResult(success=False, message="Verification started")

        if async_playwright is None:
            result.errors.append(
                "Playwright not installed. Install with: uv run playwright install chromium"
            )
            result.message = "Verification failed: Missing dependencies"
            return result

        config = self.config.get("github_pages", {})
        url = config.get("production_url")

        if not url:
            result.errors.append("production_url not configured")
            result.message = "Verification failed: Missing configuration"
            return result

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page()

                # ページアクセス
                self._log(f"Accessing {url}")
                start_time = time.time()

                try:
                    response = await page.goto(url, wait_until="domcontentloaded")
                    page_load_time = (time.time() - start_time) * 1000

                    result.status_code = response.status if response else None
                    result.accessible = response and response.ok
                    result.page_load_time_ms = page_load_time

                    if result.accessible:
                        self._log(
                            f"✅ Page accessible (HTTP {result.status_code}, {page_load_time:.0f}ms)"
                        )
                    else:
                        self._log(
                            f"❌ Page not accessible (HTTP {result.status_code})",
                            "ERROR",
                        )
                        result.errors.append(f"HTTP {result.status_code}")

                except Exception as e:
                    self._log(f"❌ Failed to access page: {e}", "ERROR")
                    result.errors.append(f"Page access failed: {e}")
                    await browser.close()
                    result.message = "Verification failed: Page access error"
                    return result

                # 必須要素のチェック
                critical_elements = config.get("critical_elements", [])
                if critical_elements:
                    self._log("Checking critical elements")
                    await self._check_critical_elements(page, critical_elements, result)

                # リンクチェック
                if check_links:
                    self._log("Checking links")
                    link_results = await self._check_links(page, url, config)
                    result.link_check_results = link_results

                    # リンクチェック結果のサマリー
                    broken_internal = [
                        lr for lr in link_results if not lr.ok and not lr.is_external
                    ]
                    broken_external = [lr for lr in link_results if not lr.ok and lr.is_external]

                    if broken_internal:
                        result.errors.append(f"Found {len(broken_internal)} broken internal links")
                    if broken_external:
                        if config.get("link_check", {}).get("external_as_warning", True):
                            result.warnings.append(
                                f"Found {len(broken_external)} broken external links"
                            )
                        else:
                            result.errors.append(
                                f"Found {len(broken_external)} broken external links"
                            )

                    self._log(
                        f"Link check: {len([lr for lr in link_results if lr.ok])} OK, "
                        f"{len(broken_internal)} broken internal, "
                        f"{len(broken_external)} broken external"
                    )

                await browser.close()

        except Exception as e:
            self._log(f"❌ Verification failed: {e}", "ERROR")
            result.errors.append(f"Verification exception: {e}")
            result.message = "Verification failed: Unexpected error"
            return result

        # 結果の判定
        result.success = len(result.errors) == 0
        if result.success:
            result.message = "✅ GitHub Pages verification passed"
            self._log(result.message)
        else:
            result.message = f"❌ GitHub Pages verification failed with {len(result.errors)} errors"
            self._log(result.message, "ERROR")

        return result

    async def _check_critical_elements(
        self,
        page,
        critical_elements: list[dict],
        result: GitHubPagesVerificationResult,
    ):
        """必須要素をチェック

        Args:
            page: Playwrightのページオブジェクト
            critical_elements: チェックする要素のリスト
            result: 結果オブジェクト
        """
        for element in critical_elements:
            selector = element.get("selector")
            description = element.get("description", selector)
            timeout = element.get("timeout_ms", 5000)

            try:
                await page.wait_for_selector(selector, timeout=timeout)
                result.critical_elements_found.append(description)
                self._log(f"  ✅ {description}: Found")
            except Exception:
                result.critical_elements_missing.append(description)
                result.errors.append(f"Critical element not found: {description}")
                self._log(f"  ❌ {description}: Not found", "ERROR")

    async def _check_links(self, page, base_url: str, config: dict) -> list[LinkCheckResult]:
        """ページ内のリンクをチェック

        Args:
            page: Playwrightのページオブジェクト
            base_url: ベースURL
            config: 設定

        Returns:
            リンクチェック結果のリスト
        """
        link_config = config.get("link_check", {})
        ignore_patterns = link_config.get("ignore_patterns", [])
        timeout_seconds = link_config.get("timeout_seconds", 10)

        # ページ内のすべてのリンクを抽出
        links = await page.evaluate(
            """
            () => Array.from(document.querySelectorAll('a'))
                .map(a => a.href)
                .filter(href => href && href.trim() !== '')
        """
        )

        # 重複を削除
        unique_links = list(set(links))
        results = []

        for link in unique_links:
            # 無視パターンのチェック
            if any(pattern in link for pattern in ignore_patterns):
                continue

            is_external = not link.startswith(base_url)

            try:
                # HEAD リクエストでリンクをチェック
                if requests is not None:
                    response = requests.head(link, timeout=timeout_seconds, allow_redirects=True)
                    results.append(
                        LinkCheckResult(
                            url=link,
                            status=response.status_code,
                            ok=response.ok,
                            is_external=is_external,
                        )
                    )
                else:
                    # requestsがない場合はPlaywrightを使用
                    response = await page.request.head(link)
                    results.append(
                        LinkCheckResult(
                            url=link,
                            status=response.status,
                            ok=response.ok,
                            is_external=is_external,
                        )
                    )
            except Exception as e:
                results.append(
                    LinkCheckResult(
                        url=link,
                        status=None,
                        ok=False,
                        error=str(e),
                        is_external=is_external,
                    )
                )

        return results


class DockerVerifier(DeploymentVerifier):
    """Docker環境検証クラス"""

    def verify(self, build_image: bool = True) -> DockerVerificationResult:
        """Docker環境を検証

        Args:
            build_image: イメージをビルドするか

        Returns:
            検証結果
        """
        self._log("Starting Docker verification")

        result = DockerVerificationResult(success=False, message="Verification started")

        try:
            import docker
        except ImportError:
            result.errors.append("Docker SDK not installed. Install with: uv pip install docker")
            result.message = "Verification failed: Missing dependencies"
            return result

        config = self.config.get("docker", {})

        try:
            client = docker.from_env()
            self._log("✅ Connected to Docker daemon")
        except Exception as e:
            self._log(f"❌ Cannot connect to Docker daemon: {e}", "ERROR")
            result.errors.append(f"Docker daemon not running: {e}")
            result.message = "Verification failed: Docker daemon error"
            return result

        # イメージのビルド
        if build_image:
            self._log("Building Docker image")
            try:
                image_name = config.get("image_name", "letterpack-web")
                image_tag = config.get("image_tag", "latest")
                full_image_name = f"{image_name}:{image_tag}"

                # ビルド
                image, build_logs = client.images.build(
                    path=str(Path(__file__).parent.parent),
                    tag=full_image_name,
                    rm=True,
                )

                result.build_success = True
                result.image_id = image.id
                result.image_size_mb = image.attrs["Size"] / (1024 * 1024)

                self._log(f"✅ Image built: {result.image_size_mb:.2f} MB")

                # イメージサイズの警告
                warning_threshold = config.get("image_size_warning_mb", 500)
                if result.image_size_mb > warning_threshold:
                    result.warnings.append(
                        f"Image size ({result.image_size_mb:.2f} MB) exceeds warning threshold ({warning_threshold} MB)"
                    )
                    self._log(
                        f"⚠️  Image size warning: {result.image_size_mb:.2f} MB",
                        "WARNING",
                    )

            except Exception as e:
                self._log(f"❌ Image build failed: {e}", "ERROR")
                result.errors.append(f"Image build failed: {e}")
                result.message = "Verification failed: Build error"
                return result

        # コンテナの起動とヘルスチェック
        self._log("Starting container for health check")
        container = None
        try:
            container_name = config.get("container_name", "letterpack-web-verification-test")
            image_name = config.get("image_name", "letterpack-web")
            image_tag = config.get("image_tag", "latest")
            full_image_name = f"{image_name}:{image_tag}"

            # 既存のテストコンテナを削除
            try:
                old_container = client.containers.get(container_name)
                old_container.stop()
                old_container.remove()
                self._log(f"Removed old test container: {container_name}")
            except docker.errors.NotFound:
                pass

            # コンテナを起動
            test_env = config.get("test_environment", {})
            container = client.containers.run(
                full_image_name,
                detach=True,
                name=container_name,
                ports={"5000/tcp": 5000},
                environment=test_env,
            )

            result.container_started = True
            self._log("✅ Container started")

            # ヘルスチェックを待つ
            timeout = config.get("health_check_timeout", 30)
            start_time = time.time()

            while time.time() - start_time < timeout:
                container.reload()
                state = container.attrs["State"]

                if "Health" in state:
                    health = state["Health"]["Status"]

                    if health == "healthy":
                        health_check_time = (time.time() - start_time) * 1000
                        result.health_check_passed = True
                        result.health_check_time_ms = health_check_time
                        self._log(f"✅ Health check passed ({health_check_time:.0f}ms)")
                        break
                    elif health == "unhealthy":
                        result.errors.append("Container became unhealthy")
                        self._log("❌ Container became unhealthy", "ERROR")
                        break
                else:
                    # ヘルスチェックが定義されていない場合、コンテナが実行中かチェック
                    if state.get("Running"):
                        health_check_time = (time.time() - start_time) * 1000
                        result.health_check_passed = True
                        result.health_check_time_ms = health_check_time
                        self._log(
                            f"✅ Container running ({health_check_time:.0f}ms) [No health check defined]"
                        )
                        break

                time.sleep(1)

            if not result.health_check_passed:
                result.warnings.append(f"Health check timeout after {timeout} seconds")

        except Exception as e:
            self._log(f"❌ Container verification failed: {e}", "ERROR")
            result.errors.append(f"Container verification failed: {e}")
        finally:
            # クリーンアップ
            if container:
                try:
                    container.stop()
                    container.remove()
                    self._log("Cleaned up test container")
                except Exception as e:
                    self._log(f"Warning: Failed to cleanup container: {e}", "WARNING")

        # 結果の判定
        result.success = len(result.errors) == 0
        if result.success:
            result.message = "✅ Docker verification passed"
            self._log(result.message)
        else:
            result.message = f"❌ Docker verification failed with {len(result.errors)} errors"
            self._log(result.message, "ERROR")

        return result


def generate_markdown_report(results: dict[str, VerificationResult]) -> str:
    """検証結果をMarkdownレポートとして生成

    Args:
        results: 検証結果の辞書

    Returns:
        Markdownレポート
    """
    lines = [
        "# Deployment Verification Report",
        "",
        f"**Generated at**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
    ]

    # サマリー
    lines.append("## Summary")
    lines.append("")

    total_errors = sum(len(r.errors) for r in results.values())
    total_warnings = sum(len(r.warnings) for r in results.values())

    if total_errors == 0:
        lines.append("✅ **All verifications passed**")
    else:
        lines.append(
            f"❌ **Verification failed with {total_errors} error(s) and {total_warnings} warning(s)**"
        )

    lines.append("")

    # 各検証結果
    for target, result in results.items():
        lines.append(f"## {target.title()} Verification")
        lines.append("")

        if result.success:
            lines.append("✅ **Status**: PASSED")
        else:
            lines.append("❌ **Status**: FAILED")

        lines.append("")

        # GitHub Pages固有の情報
        if isinstance(result, GitHubPagesVerificationResult):
            lines.append("### Details")
            lines.append("")
            lines.append(f"- **Accessible**: {'✅ Yes' if result.accessible else '❌ No'}")
            lines.append(f"- **Status Code**: {result.status_code}")
            if result.page_load_time_ms:
                lines.append(f"- **Page Load Time**: {result.page_load_time_ms:.0f} ms")
            if result.pyodide_init_time_ms:
                lines.append(f"- **Pyodide Init Time**: {result.pyodide_init_time_ms:.0f} ms")
            lines.append("")

            if result.critical_elements_found:
                lines.append("### Critical Elements Found")
                lines.append("")
                for element in result.critical_elements_found:
                    lines.append(f"- ✅ {element}")
                lines.append("")

            if result.critical_elements_missing:
                lines.append("### Critical Elements Missing")
                lines.append("")
                for element in result.critical_elements_missing:
                    lines.append(f"- ❌ {element}")
                lines.append("")

            if result.link_check_results:
                broken_links = [lr for lr in result.link_check_results if not lr.ok]
                if broken_links:
                    lines.append("### Broken Links")
                    lines.append("")
                    for link in broken_links:
                        status_str = f"HTTP {link.status}" if link.status else link.error
                        external_marker = " (external)" if link.is_external else ""
                        lines.append(f"- ❌ {link.url}{external_marker} - {status_str}")
                    lines.append("")

        # Docker固有の情報
        elif isinstance(result, DockerVerificationResult):
            lines.append("### Details")
            lines.append("")
            lines.append(f"- **Build Success**: {'✅ Yes' if result.build_success else '❌ No'}")
            if result.image_size_mb:
                lines.append(f"- **Image Size**: {result.image_size_mb:.2f} MB")
            lines.append(
                f"- **Container Started**: {'✅ Yes' if result.container_started else '❌ No'}"
            )
            lines.append(
                f"- **Health Check**: {'✅ Passed' if result.health_check_passed else '❌ Failed'}"
            )
            if result.health_check_time_ms:
                lines.append(f"- **Health Check Time**: {result.health_check_time_ms:.0f} ms")
            lines.append("")

        # エラー
        if result.errors:
            lines.append("### Errors")
            lines.append("")
            for error in result.errors:
                lines.append(f"- ❌ {error}")
            lines.append("")

        # 警告
        if result.warnings:
            lines.append("### Warnings")
            lines.append("")
            for warning in result.warnings:
                lines.append(f"- ⚠️ {warning}")
            lines.append("")

    return "\n".join(lines)


async def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="Deployment verification tool for Letter Pack Label Maker"
    )
    parser.add_argument(
        "--target",
        choices=["all", "github-pages", "docker"],
        default="all",
        help="Verification target",
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file",
    )
    parser.add_argument(
        "--check-links-only",
        action="store_true",
        help="Only check links (GitHub Pages only)",
    )
    parser.add_argument(
        "--skip-links",
        action="store_true",
        help="Skip link checking",
    )
    parser.add_argument(
        "--output-file",
        type=str,
        help="Output report to file",
    )

    args = parser.parse_args()

    results = {}

    # GitHub Pages検証
    if args.target in ["all", "github-pages"]:
        print("\n" + "=" * 60)
        print("GitHub Pages Verification")
        print("=" * 60 + "\n")

        verifier = GitHubPagesVerifier(args.config)
        result = await verifier.verify(
            check_links=not args.skip_links, measure_performance=not args.check_links_only
        )
        results["github-pages"] = result

    # Docker検証
    if args.target in ["all", "docker"] and not args.check_links_only:
        print("\n" + "=" * 60)
        print("Docker Verification")
        print("=" * 60 + "\n")

        verifier = DockerVerifier(args.config)
        result = verifier.verify()
        results["docker"] = result

    # レポート生成
    print("\n" + "=" * 60)
    print("Verification Report")
    print("=" * 60 + "\n")

    report = generate_markdown_report(results)
    print(report)

    # ファイルに出力
    if args.output_file:
        output_path = Path(args.output_file)
        output_path.write_text(report, encoding="utf-8")
        print(f"\n📄 Report saved to: {output_path}")

    # 終了コード
    has_errors = any(len(r.errors) > 0 for r in results.values())
    sys.exit(1 if has_errors else 0)


if __name__ == "__main__":
    asyncio.run(main())
