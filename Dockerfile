# レターパックラベル作成 - Dockerイメージ
# フォント環境を統一したWebサーバー実行環境

# ===== ビルドステージ =====
# uvを使って依存関係をrequirements.txtに出力
FROM python:3.12-slim AS builder

# uvのインストール
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    curl -LsSf https://astral.sh/uv/install.sh | sh && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /build

# 依存関係ファイルのコピー
COPY pyproject.toml README.md ./

# uvを使ってrequirements.txtを生成
# --no-dev: 開発用依存関係は除外
# --no-emit-project: プロジェクト自体を除外（後でeditable installする）
RUN uv export --no-dev --no-hashes --no-emit-project -o requirements.txt

# ===== 実行ステージ =====
FROM python:3.12-slim

# メタデータ
LABEL maintainer="Letter Pack Label Maker Contributors"
LABEL description="レターパックラベル作成Webサーバー"

# 環境変数
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# システムパッケージの更新と必要なパッケージのインストール
# - fonts-noto-cjk: Noto CJKフォント（日本語、中国語、韓国語対応）
# - fonts-noto-cjk-extra: 追加のCJKフォント
# - fontconfig: フォント設定ツール
# - curl: ヘルスチェックに必要
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

# ビルドステージからrequirements.txtをコピー
COPY --from=builder --chown=letterpack:letterpack /build/requirements.txt ./

# 仮想環境の作成と依存関係のインストール
RUN python -m venv /app/.venv && \
    /app/.venv/bin/pip install --no-cache-dir -r requirements.txt

# 仮想環境のPythonを使用
ENV PATH="/app/.venv/bin:${PATH}"

# アプリケーションコードとpyproject.tomlをコピー
# （editable installのために必要）
COPY --chown=letterpack:letterpack pyproject.toml README.md ./
COPY --chown=letterpack:letterpack src/ ./src/

# editable installを実行（メタデータのみ）
RUN /app/.venv/bin/pip install --no-deps -e .

# ポート公開
EXPOSE 5000

# ヘルスチェック（curlを使用してより確実に）
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Webサーバー起動
# --host 0.0.0.0 でコンテナ外部からアクセス可能にする
CMD ["python", "-m", "letterpack.web", "--host", "0.0.0.0", "--port", "5000"]
