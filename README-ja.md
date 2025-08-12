# Gmail Attachment Downloader

正規表現フィルターに基づいてGmailの添付ファイル（PDF）を自動ダウンロードします。複数アカウントをサポートし、個人Gmail・Google Workspaceアカウント両方で動作します。

## 機能

- **マルチアカウント対応** - 複数のGmail/Google Workspaceアカウントを処理
- **正規表現フィルタリング** - From、To、Subject、Bodyを正規表現でフィルタリング
- **ワイルドカード添付ファイルフィルタリング** - ファイル名パターンで添付ファイルをフィルタリング
- **セキュアな認証情報保存** - OAuth2トークンを暗号化して安全に保存
- **クロスプラットフォーム** - Windows、macOS、Linuxで動作
- **バッチ処理** - スケジューラー/cronジョブに最適
- **日付範囲検索** - 設定可能な検索期間

## インストール

### PyPIからのクイックインストール

PyPIに公開後、簡単にインストール・実行できます：

```bash
# uv使用（推奨）
uvx gmail-attachment-dl  # インストールせずに直接実行

# またはグローバルインストール
uv tool install gmail-attachment-dl

# またはpipでインストール
pip install gmail-attachment-dl
```

### ソースからのインストール

#### 前提条件

仮想環境を作成・有効化：

```bash
python -m venv venv

# Windows
.\venv\Scripts\Activate.ps1

# Linux/macOS
source venv/bin/activate
```

### 基本インストール

プロジェクトを編集可能モードでインストール：

#### プロダクション使用

```bash
pip install -e "."
```

#### 開発

開発ツールを含めてインストール：

```bash
pip install -e ".[dev]"
```

### 依存関係

**コア依存関係**（自動インストール）:

- `google-auth>=2.0.0` - Google認証ライブラリ
- `google-auth-oauthlib>=1.0.0` - OAuth2フロー対応
- `google-auth-httplib2>=0.2.0` - Google APIs用HTTPトランスポート
- `google-api-python-client>=2.0.0` - Gmail APIクライアント
- `cryptography>=41.0.0` - トークン暗号化
- `click>=8.0.0` - コマンドラインインターフェース

**開発依存関係**（`[dev]`でインストール）:

- `pylint` - コードリント
- `pylint-plugin-utils` - Pylintユーティリティ
- `black` - コードフォーマット

### インストール例

#### クイックスタート（プロダクション）

```bash
# クローンしてプロダクション用インストール
git clone <repository-url>
cd gmail-attachment-dl
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows
pip install -e "."
```

#### 開発者セットアップ

```bash
# クローンして開発環境セットアップ
git clone <repository-url>
cd gmail-attachment-dl
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows
pip install -e ".[dev]"

# 開発ツール実行
black src/
ruff check src/
```

## セットアップ

### 1. Google Cloud設定

1. [Google Cloud Console](https://console.cloud.google.com/)にアクセス
2. 新しいプロジェクトを作成するか既存のプロジェクトを選択
3. Gmail APIを有効化：
   - 「APIとサービス」→「ライブラリ」へ移動
   - 「Gmail API」を検索
   - 「有効にする」をクリック
4. OAuth2認証情報を作成：
   - 「APIとサービス」→「認証情報」へ移動
   - 「認証情報を作成」→「OAuth クライアント ID」をクリック
   - アプリケーションタイプとして「デスクトップアプリ」を選択
   - 認証情報JSONファイルをダウンロード
5. ファイルを`client_secret.json`として保存：
   - Windows: `%APPDATA%\gmail-attachment-dl\credentials\`
   - macOS: `~/Library/Application Support/gmail-attachment-dl/credentials/`
   - Linux: `~/.config/gmail-attachment-dl/credentials/`

### 2. 設定ファイル作成

`config.json`ファイルを作成（`config.example.json`を参考）：

```json
{
  "default_days": 7,
  "app_dir": null,
  "credentials_path": null,
  "download_base_path": null,
  "encryption_salt": null,
  "accounts": {
    "user@gmail.com": [
      {
        "from": "invoice@.*\\.example\\.com",
        "subject": ["Receipt", "Invoice"],
        "body": "Payment.*confirmed",
        "attachments": ["*.pdf"]
      },
      {
        "from": "billing@.*\\.example\\.com",
        "attachments": ["report_*.pdf", "invoice_*.pdf"]
      }
    ],
    "user@company.com": [
      {
        "from": ["billing@.*", "accounting@.*"],
        "subject": "Statement",
        "attachments": null
      }
    ]
  }
}
```

**設定構造：**

- 各メールアカウントは**フィルターセットの配列**を持つ
- アカウントごとに複数のフィルターセットで異なるルールを適用可能
- フィルターセット内のすべての条件は一致する必要（AND）
- フィルターセットは独立して処理される（OR）

**パス設定：**

- `app_dir`: アプリケーションデータディレクトリ（デフォルト：プラットフォーム固有）
- `credentials_path`: 認証情報保存ディレクトリ（デフォルト：`{app_dir}/credentials`）
- `download_base_path`: ダウンロード基準ディレクトリ（デフォルト：`{app_dir}/downloads`）
- `encryption_salt`: 認証情報暗号化用ソルト

**注意：** 設定ファイルなしで認証すると、認証情報は現在のディレクトリに保存されます。

### 3. アカウント認証

各アカウントを認証（初回のみ）：

```bash
gmail-attachment-dl --auth user@gmail.com
gmail-attachment-dl --auth user@company.com
```

これは以下を実行します：

1. OAuth2認証用にブラウザを開く
2. アプリケーションの承認を要求
3. 将来使用するため暗号化された認証情報を保存

**認証動作：**

- **設定ファイルあり**: 設定された`credentials_path`に認証情報保存
- **設定ファイルなし**: 現在のディレクトリに認証情報保存

## 使用方法

### コマンドラインオプション

```bash
gmail-attachment-dl --help
```

```text
usage: gmail-attachment-dl [-h] [--version] [--config CONFIG] [--days DAYS]
                          [--auth EMAIL] [--verbose]

Gmail Attachment Downloader

options:
  -h, --help       ヘルプメッセージを表示して終了
  --version        プログラムのバージョン番号を表示して終了
  --config CONFIG  設定ファイルのパス（デフォルト：./config.json）
  --days DAYS      検索する日数（デフォルト：設定から）
  --auth EMAIL     特定のメールアカウントを認証
  --verbose, -v    詳細出力を有効化
```

### コマンド例

```bash
# バージョン確認
gmail-attachment-dl --version
```

### 基本使用法

```bash
# 過去7日間の添付ファイルをダウンロード（デフォルト）
gmail-attachment-dl

# 日数指定
gmail-attachment-dl --days 30

# カスタム設定ファイル使用
gmail-attachment-dl --config /path/to/config.json

# 詳細出力
gmail-attachment-dl -v
```

ダウンロードされたファイルは以下で整理されます：

- メールアカウント
- 年
- 日付とメッセージID
- 元の添付ファイル名

### 定期実行（Cron）

```bash
# cronに追加して午前2時に毎日実行
0 2 * * * /usr/local/bin/gmail-attachment-dl --days 1
```

### uvでの使用

```bash
# 直接実行
uvx gmail-attachment-dl --days 7

# 特定Pythonバージョンで実行
uv run --python 3.11 gmail-attachment-dl
```

## 設定

### フィルターオプション

各フィルターセットは以下のフィールドを持てます（すべてオプション）：

- **from**: 送信者メールパターン（文字列または文字列配列）
- **to**: 受信者メールパターン（文字列または文字列配列）
- **subject**: 件名パターン（文字列または文字列配列）
- **body**: メール本文パターン（文字列または文字列配列）
- **attachments**: 添付ファイル名パターン（文字列または文字列配列）

**パターンタイプ：**

- **メールフィールド**（from/to/subject/body）：完全な正規表現構文
- **添付ファイル名**: ワイルドカードパターン（`*.pdf`、`invoice_*.pdf`など）
- `null`または省略はそのフィールドでフィルタリングしない

**マッチングロジック：**

- フィルターセット内：指定されたすべてのフィールドが一致（AND）
- 配列内の複数パターン：任意のパターンが一致すれば可（OR）
- アカウントあたり複数フィルターセット：それぞれ独立して処理

### 設定例

```json
{
  "default_days": 30,
  "app_dir": "~/my-gmail-app",
  "credentials_path": "~/.private/gmail-creds",
  "download_base_path": "~/Documents/receipts",
  "encryption_salt": "my-custom-salt-string",
  "accounts": {
    "user@gmail.com": [
      {
        "from": ".*@company\\.com",
        "subject": ["Invoice", "Receipt", "Bill"],
        "body": "(Paid|Confirmed|Processed)",
        "attachments": ["*.pdf"]
      },
      {
        "from": "accounting@vendor\\.com",
        "attachments": ["invoice_*.pdf", "receipt_*.pdf"]
      },
      {
        "subject": "Monthly Report",
        "attachments": ["report_202*.pdf"]
      }
    ]
  }
}
```

**添付ファイルパターン例：**

- `"*.pdf"` - すべてのPDFファイル
- `"invoice_*.pdf"` - "invoice_"で始まるPDF
- `["*.pdf", "*.xlsx"]` - PDFとExcelファイル
- `null`または省略 - すべての添付ファイル（フィルタリングなし）

**パスオプション：**

- 相対パス: `"./downloads"`（現在のワーキングディレクトリからの相対）
- 絶対パス: `"/home/user/downloads"`または`"C:\\Users\\name\\Downloads"`
- ホームディレクトリ: `"~/Downloads"`（自動展開）
- 省略時は`{app_dir}/subdirectory`のデフォルト使用

## ファイル保存

ダウンロードされた添付ファイルは階層構造で整理されます：

```text
downloads/
├── user@gmail.com/
│   ├── 2025/
│   │   ├── 0108_abc123def456_invoice.pdf
│   │   ├── 0108_abc123def456_receipt.pdf
│   │   ├── 0109_ghi789jkl012_statement.pdf
│   │   └── 0110_mno345pqr678_report.pdf
│   └── 2024/
│       └── 1231_stu901vwx234_document.pdf
└── user@company.com/
    └── 2025/
        └── 0108_yza567bcd890_summary.pdf
```

**ファイル命名：** `MMDD_messageId_originalname.pdf`

- 各メールアカウントは独自のディレクトリを持つ
- ファイルは年別で整理
- ファイル名プレフィックスに日付（MMDD）とGmailメッセージIDを含む
- 同一メールからの複数添付ファイルは同じプレフィックスを共有
- 重複ファイル名は自動的に`_01`、`_02`などでリネーム

## セキュリティ

- OAuth2リフレッシュトークンはFernet（対称暗号化）で暗号化
- 認証情報は制限ファイル権限（Unixでは600）で保存
- パスワードは保存されない - OAuth2トークンのみ
- 各アカウントは個別認証が必要

## エラーハンドリング

このツールには一般的な問題に対する包括的なエラーハンドリングが含まれます：

- **認証エラー**: 自動トークンリフレッシュと再認証フォールバック
- **ネットワーク問題**: API呼び出しでの指数バックオフ付きリトライ
- **ファイルシステムエラー**: 権限・ディスク容量問題の適切な処理
- **Gmail API制限**: レート制限とクォータ管理

## トラブルシューティング

### トークン有効期限切れ

"Token expired"エラーが表示される場合：

```bash
gmail-attachment-dl --auth user@gmail.com
```

### 認証情報不明

認証情報が見つからない場合、再認証：

```bash
gmail-attachment-dl --auth user@gmail.com
```

### 設定問題

設定が無効の場合：

```bash
# 設定ファイル形式確認
gmail-attachment-dl --config /path/to/config.json --verbose
```

### API制限

Gmail APIには十分なクォータがあります（10億単位/日）が、以下にご注意：

- メッセージ送信あたり250単位
- メッセージ読み取りあたり5単位
- 添付ファイルダウンロードあたり5単位

## 開発

### 開発環境セットアップ

1. **クローンして環境セットアップ：**

```bash
git clone https://github.com/yourusername/gmail-attachment-dl.git
cd gmail-attachment-dl
python -m venv venv

# 仮想環境有効化
# Windows:
.\venv\Scripts\Activate.ps1
# Linux/macOS:
source venv/bin/activate

# 開発モードでインストール
pip install -e ".[dev]"
```

2. **コードフォーマットとリント：**

```bash
# コードフォーマット
black src/

# リンター実行
ruff check src/

# 型チェック
mypy src/
```

3. **開発中のテスト：**

```bash
# テスト実行
pytest

# カバレッジ付きテスト実行
pytest --cov=src/

# CLI テスト
gmail-attachment-dl --help

# 各種オプションでテスト
gmail-attachment-dl --config config.example.json --days 1 --verbose
```
