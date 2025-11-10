# Docker環境での実行

このドキュメントでは、Docker環境でレターパックラベル作成Webサーバーを実行する方法を説明します。

## なぜDockerを使うのか？

Dockerを使用することで、以下のメリットがあります：

- **フォント環境の統一**: どの環境でも同じフォント（Noto CJK）を使用し、一貫したPDF出力を実現
- **環境構築の簡素化**: Python、依存関係、フォントなどを自動でセットアップ
- **ポータビリティ**: Windows、Mac、Linuxなど、どのOSでも同じ環境で実行可能
- **クリーンな環境**: ホストシステムを汚さずに実行
- **セキュリティ**: 非rootユーザーで実行し、コンテナを安全に運用

## Pythonバージョンについて

このプロジェクトは、以下のPython環境をサポートしています：

- **ローカル開発**: Python 3.8.1以降（`pyproject.toml`に記載）
  - 幅広い環境での動作を保証するため、古いバージョンもサポート
- **Docker環境**: Python 3.12（`Dockerfile`に記載）
  - 最新の安定版を使用して最適なパフォーマンスとセキュリティを確保
  - フォント環境が統一され、一貫した動作を保証

Docker環境では最新のPython 3.12を使用することで、パフォーマンス向上とセキュリティパッチの恩恵を受けられます。ローカル開発では、既存の環境との互換性を保つため、Python 3.8.1以降であれば動作します。

## 必要なもの

- Docker（バージョン20.10以降推奨）
- Docker Compose（バージョン2.0以降推奨）

### Dockerのインストール

まだDockerをインストールしていない場合は、以下から入手してください：

- **Docker Desktop** (Windows/Mac): https://www.docker.com/products/docker-desktop
- **Docker Engine** (Linux): https://docs.docker.com/engine/install/

## クイックスタート

### 1. Docker Composeで起動（推奨）

最も簡単な方法です：

```bash
# Webサーバーを起動
docker compose up

# バックグラウンドで起動する場合
docker compose up -d

# ログを確認
docker compose logs -f

# 停止
docker compose down
```

起動後、ブラウザで http://localhost:5000 にアクセスしてください。

### 2. Dockerコマンドで起動

Docker Composeを使わない場合：

```bash
# イメージをビルド
docker build -t letterpack-label-maker .

# コンテナを起動
docker run -p 5000:5000 letterpack-label-maker

# バックグラウンドで起動する場合
docker run -d -p 5000:5000 --name letterpack letterpack-label-maker

# ログを確認
docker logs -f letterpack

# 停止
docker stop letterpack
docker rm letterpack
```

## 設定のカスタマイズ

### 環境変数

本番環境では、必ず`SECRET_KEY`を設定してください：

```bash
# .envファイルを作成
echo "SECRET_KEY=your-very-secret-key-here" > .env

# Docker Composeで起動（自動的に.envが読み込まれます）
docker compose up
```

### ポート番号の変更

デフォルトではポート5000を使用しますが、変更可能です：

**docker-compose.ymlを編集:**
```yaml
ports:
  - "8080:5000"  # ホストの8080番ポートを使用
```

**Dockerコマンドの場合:**
```bash
docker run -p 8080:5000 letterpack-label-maker
```

### 開発モード

ソースコードの変更をリアルタイムで反映させたい場合：

```bash
# docker-compose.ymlにボリュームマウントが設定されているので、
# そのまま起動すれば変更が反映されます
docker compose up
```

## 使用しているフォント

このDockerイメージには、以下の日本語フォントがインストールされています：

- **Noto Sans CJK JP**: ゴシック体（サンセリフ）
- **Noto Serif CJK JP**: 明朝体（セリフ）

これらのフォントは、Googleが開発したオープンソースフォントで、日本語、中国語、韓国語に対応しています。

## トラブルシューティング

### ポートがすでに使用されている

```
Error: bind: address already in use
```

このエラーが出た場合、ポート5000が他のアプリケーションで使用されています。別のポートを使用してください（上記「ポート番号の変更」参照）。

### イメージのビルドに失敗する

```bash
# キャッシュをクリアして再ビルド
docker compose build --no-cache

# または
docker build --no-cache -t letterpack-label-maker .
```

### コンテナが起動しない

```bash
# ログを確認
docker compose logs

# または
docker logs letterpack
```

### フォントが正しく表示されない

フォントキャッシュを再構築してみてください：

```bash
# コンテナ内でフォントキャッシュを再構築
docker compose exec web fc-cache -fv
```

## 本番環境での使用

本番環境でDockerを使用する場合の推奨設定：

### 1. 環境変数を設定

```bash
# .envファイルを作成（本番環境では強力なキーを使用）
SECRET_KEY=$(openssl rand -hex 32)
echo "SECRET_KEY=$SECRET_KEY" > .env
```

### 2. リバースプロキシを使用

本番環境では、NginxやApacheなどのリバースプロキシを前段に配置することを推奨します：

**nginx.confの例:**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3. ログ管理

```bash
# ログをファイルに出力
docker compose logs -f > letterpack.log &

# ログのローテーション設定を検討してください
```

### 4. 自動再起動の設定

`docker-compose.yml`には既に`restart: unless-stopped`が設定されているため、コンテナがクラッシュしても自動的に再起動します。

## パフォーマンス最適化

### マルチステージビルドの検討

現在のDockerfileは単一ステージですが、より小さなイメージが必要な場合は、マルチステージビルドを検討してください。

### メモリ制限

```yaml
# docker-compose.yml
services:
  web:
    # ... 他の設定 ...
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
```

## セキュリティ

### 非rootユーザーでの実行

より安全性を高めるため、非rootユーザーでアプリケーションを実行することを推奨します：

**Dockerfileに追加:**
```dockerfile
# 非rootユーザーを作成
RUN useradd -m -u 1000 letterpack
USER letterpack
```

### ネットワークの分離

複数のサービスを実行する場合は、Dockerネットワークを適切に分離してください。

## まとめ

Docker環境を使用することで、フォント環境が統一され、どの環境でも一貫したPDF出力が得られます。

基本的な使い方：
```bash
# 起動
docker compose up -d

# 確認
curl http://localhost:5000

# 停止
docker compose down
```

問題が発生した場合は、まずログを確認してください：
```bash
docker compose logs -f
```

ご質問やフィードバックは、GitHubのIssuesでお願いします。
