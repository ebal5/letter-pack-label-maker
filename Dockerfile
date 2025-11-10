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

# 作業ディレクトリ
WORKDIR /app

# システムパッケージの更新と必要なパッケージのインストール
# - fonts-noto-cjk: Noto CJKフォント（日本語、中国語、韓国語対応）
# - fonts-noto-cjk-extra: 追加のCJKフォント
# - fontconfig: フォント設定ツール
# - curl: uvのインストールに必要
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        fonts-noto-cjk \
        fonts-noto-cjk-extra \
        fontconfig \
        curl \
    && fc-cache -fv \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# uvのインストール（高速なPythonパッケージマネージャー）
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# 依存関係ファイルのコピー
COPY pyproject.toml README.md ./

# 依存関係のインストール
RUN uv pip install -e .

# アプリケーションコードのコピー
COPY src/ ./src/

# ポート公開
EXPOSE 5000

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000')" || exit 1

# Webサーバー起動
# --host 0.0.0.0 でコンテナ外部からアクセス可能にする
CMD ["python", "-m", "letterpack.web", "--host", "0.0.0.0", "--port", "5000"]
