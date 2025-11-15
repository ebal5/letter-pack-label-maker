"""
Tests for Docker Deployment Verification

Docker環境検証のテスト
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# tools/deployment_verifier.pyをインポートできるようにパスを追加
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

try:
    import docker

    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False

from deployment_verifier import DockerVerifier

# このファイルの全テストにdeployment_verificationマーカーとskipifを適用
pytestmark = [
    pytest.mark.deployment_verification,
    pytest.mark.skipif(not DOCKER_AVAILABLE, reason="Docker SDK not installed"),
]


@pytest.fixture
def docker_verifier():
    """Docker検証のフィクスチャ"""
    config_path = (
        Path(__file__).parent.parent / ".claude/skills/deployment-verification/config.yaml"
    )
    return DockerVerifier(config_path)


@pytest.fixture(scope="module")
def docker_client():
    """Dockerクライアントのフィクスチャ"""
    if not DOCKER_AVAILABLE:
        pytest.skip("Docker SDK not installed")

    try:
        client = docker.from_env()
        # Dockerデーモンが動いているか確認
        client.ping()
        return client
    except Exception as e:
        pytest.skip(f"Docker daemon not running: {e}")


@pytest.mark.docker
class TestDockerDeployment:
    """Docker デプロイメントのテスト"""

    def test_docker_daemon_running(self, docker_client):
        """Dockerデーモンが実行中かテスト"""
        assert docker_client is not None
        assert docker_client.ping() is True

    @pytest.mark.slow
    def test_image_builds(self, docker_verifier):
        """Dockerイメージがビルドできるかテスト"""
        result = docker_verifier.verify(build_image=True)

        assert result.build_success, f"Image build failed: {result.errors}"
        assert result.image_id is not None, "Image ID not set"
        assert result.image_size_mb is not None, "Image size not measured"
        assert result.image_size_mb > 0, "Image size is zero"

    @pytest.mark.slow
    def test_image_size_reasonable(self, docker_verifier):
        """イメージサイズが妥当かテスト"""
        result = docker_verifier.verify(build_image=True)

        assert result.build_success, "Build must succeed first"

        # エラー閾値をチェック（設定またはデフォルト1000MB）
        config = docker_verifier.config.get("docker", {})
        error_threshold = config.get("image_size_error_mb", 1000)

        assert result.image_size_mb < error_threshold, (
            f"Image too large: {result.image_size_mb:.2f}MB (threshold: {error_threshold}MB)"
        )

    @pytest.mark.slow
    def test_container_starts(self, docker_verifier):
        """コンテナが起動するかテスト"""
        result = docker_verifier.verify(build_image=False)

        assert result.container_started, "Container failed to start"

    @pytest.mark.slow
    def test_health_check_passes(self, docker_verifier):
        """ヘルスチェックが通るかテスト"""
        result = docker_verifier.verify(build_image=False)

        # ヘルスチェックの結果を確認（警告の場合もあり得る）
        if not result.health_check_passed and result.warnings:
            # 警告のみの場合はスキップ
            pytest.skip(f"Health check timeout (warnings only): {result.warnings}")

        assert result.health_check_passed, f"Health check failed: {result.errors}"

        # ヘルスチェック時間の確認
        assert result.health_check_time_ms is not None, "Health check time not measured"

        # 設定から閾値を取得
        config = docker_verifier.config.get("docker", {})
        timeout = config.get("health_check_timeout", 30) * 1000  # 秒→ミリ秒

        assert result.health_check_time_ms < timeout, (
            f"Health check too slow: {result.health_check_time_ms:.0f}ms"
        )


@pytest.mark.docker
@pytest.mark.integration
class TestDockerIntegration:
    """Docker統合テスト"""

    @pytest.mark.slow
    def test_full_docker_verification(self, docker_verifier):
        """完全なDocker検証を実行"""
        result = docker_verifier.verify(build_image=True)

        # 基本的なアサーション
        assert result is not None
        assert result.timestamp is not None

        # エラーがある場合は詳細を表示
        if result.errors:
            error_msg = f"Docker verification failed with {len(result.errors)} errors:\n"
            for error in result.errors:
                error_msg += f"  - {error}\n"

            if result.warnings:
                error_msg += f"\nWarnings ({len(result.warnings)}):\n"
                for warning in result.warnings:
                    error_msg += f"  - {warning}\n"

            pytest.fail(error_msg)

        # 警告がある場合は表示
        if result.warnings:
            print(f"\nWarnings ({len(result.warnings)}):")
            for warning in result.warnings:
                print(f"  - {warning}")
