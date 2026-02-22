# X Bot Manager

X (Twitter) アカウントの投稿を管理・自動化するツールです。
複数アカウントへのツイート予約・一括登録・画像投稿・スケジュール管理をブラウザから操作できます。

## 機能

- **複数アカウント管理** — X API キーをアカウントごとに登録・管理（暗号化して保存）
- **ツイート予約** — 日時を指定して投稿を予約（1分ごとに自動チェックして投稿）
- **一括予約** — CSV テキストや画像を使って複数ツイートをまとめて登録
- **画像投稿** — 1ツイートあたり最大4枚の画像を添付
- **スケジュール設定** — 「何時に投稿する」というパターンをアカウントごとに管理
- **テスト投稿** — アカウント登録後に "Hello World!" で動作確認

## 必要なもの

- Python 3.13 以上（または Docker）
- X Developer アカウントと API キー（Read & Write 権限が必要）

### X API キーの取得

[X Developer Portal](https://developer.twitter.com/) でアプリを作成し、以下の4つを取得してください。

| 項目 | 説明 |
|------|------|
| API Key | Consumer Key |
| API Secret | Consumer Secret |
| Access Token | アクセストークン |
| Access Token Secret | アクセストークンシークレット |

> アプリの権限設定で **Read and Write** を選択してください。

---

## セットアップ

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd x-bot-manager
```

### 2. 環境変数ファイルの作成

`.env` ファイルをプロジェクトルートに作成します。

```bash
cp .env.example .env  # .env.example がない場合は手動で作成
```

`.env` の内容:

```env
ENCRYPTION_KEY=<生成した暗号化キー>
```

`ENCRYPTION_KEY` は以下のコマンドで生成できます。

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

> **注意:** 一度生成したキーは絶対に変更しないでください。キーを変えると既存の登録済み API キーが復号できなくなります。

---

## 起動方法

### ローカル環境（uv を使う場合）

```bash
# 依存関係のインストール
uv sync

# サーバー起動
uv run uvicorn main:app --reload
```

### ローカル環境（pip を使う場合）

```bash
pip install -e .
uvicorn main:app --reload
```

起動後、ブラウザで http://localhost:8000 にアクセスします。

---

### Docker で起動する場合

#### 1. `.env` の準備

```env
ENCRYPTION_KEY=<生成した暗号化キー>
TUNNEL_TOKEN=<Cloudflare Tunnel のトークン（使わない場合は空欄でも可）>
```

#### 2. 起動

```bash
docker-compose up -d
```

- アプリは http://localhost:8000 で起動します
- データは `./data/` ディレクトリに永続化されます
- アップロード画像は `./uploads/` ディレクトリに永続化されます

#### 3. 停止

```bash
docker-compose down
```

#### Cloudflare Tunnel（外部公開）

`docker-compose.yml` には Cloudflare Tunnel のコンテナが含まれています。
外部からアクセスしたい場合は `.env` に `TUNNEL_TOKEN` を設定してください。

```env
TUNNEL_TOKEN=eyJ...（Cloudflare ダッシュボードで発行したトークン）
```

---

## 使い方

### アカウントの登録

1. ダッシュボード右上の **「+ アカウント追加」** をクリック
2. アカウント名と X API の4つのキーを入力
3. **「保存」** をクリック
4. 保存後、**「テスト投稿」** で接続確認（"Hello World!" が投稿されます）

### ツイートの予約

1. アカウントカードをクリックしてアカウント詳細ページへ
2. **「ツイートを予約」** から投稿内容・日時・画像を設定
3. 登録されたツイートは1分ごとに自動チェックされ、予定時刻になると投稿されます

### 一括予約（メガ予約）

CSVテキストと画像を組み合わせて大量のツイートを一括登録できます。

1. アカウント詳細ページの **「一括予約」** タブを開く
2. CSVファイルからテキストを読み込む（1行1ツイート）
3. 画像をアップロードして組み合わせを設定
4. 開始日時と投稿間隔を指定して一括登録

### スケジュール設定

「平日は9時・12時・18時に投稿」のようなパターンを登録できます。

1. アカウント詳細ページの **「スケジュール設定」** タブを開く
2. スケジュール名と投稿する時間帯を登録
3. 登録したスケジュールを有効化する

---

## プロジェクト構成

```
x-bot-manager/
├── main.py              # FastAPI アプリ本体（API エンドポイント定義）
├── models.py            # データベースモデル（SQLModel）
├── pyproject.toml       # 依存関係の定義
├── Dockerfile
├── docker-compose.yml
├── services/
│   ├── encryption.py    # APIキーの暗号化・復号（Fernet）
│   ├── scheduler.py     # 自動投稿スケジューラー（APScheduler）
│   └── x_service.py     # X API との通信（Tweepy）
└── static/              # フロントエンド（HTML / JS / CSS）
    ├── index.html        # ダッシュボード
    ├── register.html     # アカウント登録
    ├── account_detail.html  # アカウント詳細・ツイート管理
    ├── edit_account.html    # アカウント編集
    └── schedule_settings.html  # スケジュール設定
```

## 技術スタック

| 用途 | ライブラリ |
|------|-----------|
| Web フレームワーク | FastAPI |
| データベース | SQLite + SQLModel |
| X API クライアント | Tweepy |
| スケジューラー | APScheduler |
| 暗号化 | cryptography (Fernet) |
| フロントエンド | Vanilla JS / HTML / CSS |

---

## 注意事項

- API キーはデータベースに暗号化して保存されます。`ENCRYPTION_KEY` は安全に管理してください。
- X API の無料プランでは投稿数に制限があります。過剰な投稿はアカウント停止のリスクがあります。
- 一度に登録できるツイートは最大100件です。
