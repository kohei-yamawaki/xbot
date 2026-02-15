# xbot — US Stock Trend Bot

米国株のニュース (Yahoo Finance RSS) と Reddit (r/wallstreetbets 等) のセンチメントを自動収集し、Gemini 2.0 Flash で分析。日次レポートをリポジトリにコミットし、X (Twitter) にも投稿する完全自動ボットです。

**コア哲学: "Zero Runtime Cost"** — レポートは Git コミットとして蓄積されるため、外部サービスが停止しても成果物は失われません。

## 機能

- Yahoo Finance RSS から主要 7 ティッカー (NVDA, AAPL, TSLA, MSFT, AMZN, GOOG, META) のニュースを取得
- Reddit (wallstreetbets / stocks / investing) の HOT 投稿を取得
- Gemini 2.0 Flash が「辛口日本人アナリスト」として分析・投稿文を生成
- Pillow で BULLISH (緑) / BEARISH (赤) のセンチメントカード画像を自動生成
- `reports/YYYY-MM-DD.md` に日次レポートを追記 (ゼロコスト成果物)
- X (Twitter) に投稿 (API エラー時はスキップし、レポートのみ保存)

## 投稿イメージ

```
🐂 $NVDA 決算期待で半導体セクターに資金流入の兆しか。
AI需要の継続性には疑問も残るが、短期的には買い圧力が
優勢とみられる。楽観は禁物だが、流れには逆らえない展開
かもしれない。 #米国株 #NVDA
```

## セットアップ

### 1. リポジトリをクローン

```bash
git clone https://github.com/<your-username>/xbot.git
cd xbot
```

### 2. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 3. API キーの取得

本ボットは以下の外部サービスの API キーが必要です。

| サービス | 必要なキー | 取得先 | 必須 |
|---------|-----------|--------|------|
| Google AI Studio | `GOOGLE_API_KEY` | https://aistudio.google.com/apikey | **必須** |
| Reddit API | `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET` | https://www.reddit.com/prefs/apps | **必須** |
| X (Twitter) API | `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET` | https://developer.x.com | 任意 |

> X API キーがない、または無料枠を超過 (402/403) した場合でも、レポート生成は正常に動作します。

#### Google AI Studio (Gemini)

1. https://aistudio.google.com/apikey にアクセス
2. 「API キーを作成」をクリック
3. 発行されたキーを控える

#### Reddit API

1. https://www.reddit.com/prefs/apps にアクセス
2. 「create another app...」をクリック
3. **script** タイプを選択し、作成
4. `client_id` (アプリ名の下に表示) と `client_secret` を控える

#### X (Twitter) API (任意)

1. https://developer.x.com でプロジェクトを作成
2. User authentication settings で **Read and Write** を有効化
3. Consumer Keys と Access Token & Secret を控える

### 4. GitHub Secrets の登録

リポジトリの **Settings → Secrets and variables → Actions** で以下を登録します。

| Secret 名 | 値 |
|-----------|-----|
| `GOOGLE_API_KEY` | Google AI Studio の API キー |
| `REDDIT_CLIENT_ID` | Reddit アプリの client_id |
| `REDDIT_CLIENT_SECRET` | Reddit アプリの client_secret |
| `X_API_KEY` | X の Consumer Key (任意) |
| `X_API_SECRET` | X の Consumer Secret (任意) |
| `X_ACCESS_TOKEN` | X の Access Token (任意) |
| `X_ACCESS_TOKEN_SECRET` | X の Access Token Secret (任意) |

### 5. 動作確認 (手動実行)

GitHub リポジトリの **Actions** タブ → **US Stock Trend Bot** → **Run workflow** で手動実行できます。

ローカルで試す場合は環境変数を設定してから実行します。

```bash
export GOOGLE_API_KEY="your-key-here"
export REDDIT_CLIENT_ID="your-client-id"
export REDDIT_CLIENT_SECRET="your-client-secret"

python -m src.main
```

## 自動実行スケジュール

GitHub Actions で以下のスケジュールで自動実行されます。

| JST | UTC | 説明 |
|-----|-----|------|
| 23:30 | 14:30 | 米国市場オープン直前 |
| 00:30 | 15:30 | 市場オープン後 |
| 01:30 | 16:30 | |
| 02:30 | 17:30 | |
| 03:30 | 18:30 | |
| 04:30 | 19:30 | |
| 05:30 | 20:30 | |
| 06:30 | 21:30 | 米国市場クローズ後 |

> `concurrency: production` により、前回のジョブ完了前に次のジョブが開始されることはありません。

## プロジェクト構成

```
xbot/
├── .github/
│   └── workflows/
│       └── bot.yml           # GitHub Actions (cron + concurrency)
├── data/
│   └── processed_ids.json    # 重複防止用の処理済み ID
├── reports/                   # 日次レポート (自動生成)
│   └── 2026-02-15.md
├── src/
│   ├── main.py               # エントリポイント (パイプライン全体)
│   ├── news_fetcher.py       # Yahoo Finance RSS 取得
│   ├── reddit_loader.py      # Reddit (PRAW) 取得
│   ├── llm_engine.py         # Gemini 2.0 Flash 分析
│   ├── image_gen.py          # Pillow 画像生成
│   ├── x_client.py           # X (Twitter) 投稿 (エラー耐性)
│   └── utils.py              # ロガー & 状態管理
├── requirements.txt
└── README.md
```

## エラー耐性の設計

| 障害パターン | ボットの挙動 |
|-------------|-------------|
| RSS 取得失敗 | 該当ティッカーをスキップし、他のティッカーで続行 |
| Reddit 取得失敗 | ニュースのみで LLM 分析を続行 |
| LLM 分析失敗 | ジョブを終了 (レポート生成不可のため) |
| 画像生成失敗 | 画像なしでレポートを生成 |
| X API 402/403 | ログ出力のみでスキップ。レポートは正常保存 |
| X API その他エラー | 同上。絶対にクラッシュしない |

## ライセンス

MIT
