# レターパックラベル作成 - Dockerイメージ
# フォント環境を統一したWebサーバー実行環境

FROM python:3.12-slim

# メタデータ
LABEL maintainer="Letter Pack Label Maker Contributors"
LABEL description="レターパックラベル作成Webサーバー"

# 環境変数
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1

# システムパッケージの更新と必要なパッケージのインストール
# - fonts-noto-cjk: Noto CJKフォント（日本語、中国語、韓国語対応）
# - fonts-noto-cjk-extra: 追加のCJKフォント
# - fontconfig: フォント設定ツール
# - curl: uvのインストールとヘルスチェックに必要
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        fonts-noto-cjk \
        fonts-noto-cjk-extra \
        fontconfig \
        curl \
    && fc-cache -fv \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 非rootユーザーの作成（セキュリティ強化）
# UID/GIDを1000に設定（一般的なユーザーIDと互換性を保つ）
RUN groupadd -r -g 1000 letterpack && \
    useradd -r -u 1000 -g letterpack -d /app -s /bin/bash letterpack

# 作業ディレクトリを作成して所有権を設定
WORKDIR /app
RUN chown -R letterpack:letterpack /app

# ここから非rootユーザーで実行
USER letterpack

# uvのインストール（非rootユーザーのホームディレクトリに）
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/app/.local/bin:${PATH}"

# 依存関係ファイルのコピー
COPY --chown=letterpack:letterpack pyproject.toml README.md ./

# 依存関係のインストール
RUN uv pip install -e .

# アプリケーションコードのコピー
COPY --chown=letterpack:letterpack src/ ./src/

# ポート公開
EXPOSE 5000

# ヘルスチェック（curlを使用してより確実に）
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Webサーバー起動
# --host 0.0.0.0 でコンテナ外部からアクセス可能にする
CMD ["python", "-m", "letterpack.web", "--host", "0.0.0.0", "--port", "5000"]
