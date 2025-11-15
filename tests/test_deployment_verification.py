"""
Tests for Deployment Verification

GitHub Pages検証のテスト
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# tools/deployment_verifier.pyをインポートできるようにパスを追加
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from deployment_verifier import GitHubPagesVerifier, LinkCheckResult


@pytest.fixture
def github_verifier():
    """GitHub Pages検証のフィクスチャ"""
    config_path = (
        Path(__file__).parent.parent / ".claude/skills/deployment-verification/config.yaml"
    )
    return GitHubPagesVerifier(config_path)


class TestGitHubPagesDeployment:
    """GitHub Pagesデプロイメントのテスト"""

    @pytest.mark.asyncio
    async def test_pages_accessibility(self, github_verifier):
        """GitHub Pagesがアクセス可能かテスト"""
        result = await github_verifier.verify(check_links=False, measure_performance=False)

        assert result.accessible, f"GitHub Pages not accessible: {result.status_code}"
        assert result.status_code == 200, f"Expected 200, got {result.status_code}"

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_critical_elements(self, github_verifier):
        """必須要素が存在するかテスト"""
        result = await github_verifier.verify(check_links=False, measure_performance=False)

        # 少なくとも一つの必須要素が見つかっているか確認
        assert len(result.critical_elements_found) > 0, "No critical elements found"

        # 欠損している要素がある場合は警告
        if result.critical_elements_missing:
            pytest.fail(f"Missing critical elements: {', '.join(result.critical_elements_missing)}")

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.skipif(
        not Path(__file__)
        .parent.parent.joinpath(".claude/skills/deployment-verification/config.yaml")
        .exists(),
        reason="Config file not found",
    )
    async def test_link_integrity(self, github_verifier):
        """リンクの整合性をテスト"""
        result = await github_verifier.verify(check_links=True, measure_performance=False)

        # 内部リンクの壊れたものをチェック
        broken_internal_links = [
            lr for lr in result.link_check_results if not lr.ok and not lr.is_external
        ]

        if broken_internal_links:
            error_msg = "Found broken internal links:\n"
            for link in broken_internal_links:
                status_str = f"HTTP {link.status}" if link.status else link.error
                error_msg += f"  - {link.url}: {status_str}\n"
            pytest.fail(error_msg)

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_page_load_performance(self, github_verifier):
        """ページロードのパフォーマンステスト"""
        result = await github_verifier.verify(check_links=False, measure_performance=True)

        assert result.page_load_time_ms is not None, "Page load time not measured"

        # 設定から閾値を取得
        config = github_verifier.config.get("github_pages", {})
        threshold = config.get("performance_thresholds", {}).get("page_load_ms", 3000)

        assert result.page_load_time_ms < threshold, (
            f"Page load too slow: {result.page_load_time_ms:.0f}ms (threshold: {threshold}ms)"
        )


class TestLinkCheckResult:
    """LinkCheckResultデータクラスのテスト"""

    def test_link_check_result_ok(self):
        """成功したリンクチェック結果のテスト"""
        result = LinkCheckResult(url="https://example.com", status=200, ok=True)

        assert result.url == "https://example.com"
        assert result.status == 200
        assert result.ok is True
        assert result.error is None
        assert result.is_external is False

    def test_link_check_result_error(self):
        """失敗したリンクチェック結果のテスト"""
        result = LinkCheckResult(
            url="https://example.com/404",
            status=404,
            ok=False,
            error="Not Found",
            is_external=True,
        )

        assert result.url == "https://example.com/404"
        assert result.status == 404
        assert result.ok is False
        assert result.error == "Not Found"
        assert result.is_external is True


@pytest.mark.integration
class TestGitHubPagesIntegration:
    """GitHub Pages統合テスト"""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_full_verification(self, github_verifier):
        """完全な検証を実行"""
        result = await github_verifier.verify(check_links=True, measure_performance=True)

        # 基本的なアサーション
        assert result is not None
        assert result.timestamp is not None

        # エラーがある場合は詳細を表示
        if result.errors:
            error_msg = f"Verification failed with {len(result.errors)} errors:\n"
            for error in result.errors:
                error_msg += f"  - {error}\n"

            if result.warnings:
                error_msg += f"\nWarnings ({len(result.warnings)}):\n"
                for warning in result.warnings:
                    error_msg += f"  - {warning}\n"

            pytest.fail(error_msg)
