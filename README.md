# xbot - 株式市場 Twitter Bot

株式市場の最新情報を自動取得し、Twitter (X) に投稿するbotです。

## 機能

- 日経平均、NYダウ、S&P500、NASDAQ、ドル円の最新データを自動取得
- 前日比の変動率を算出し、市場動向のサマリーを生成
- 指定した時間に自動でTwitterに投稿

## 投稿例

```
【株式市場速報 02/15 12:00】

📈 日経平均: 39,150
  +320 (+0.82%)
📈 NYダウ: 44,500
  +150 (+0.34%)
▲ S&P500: 6,120
  +15 (+0.25%)
▼ NASDAQ: 19,800
  -30 (-0.15%)
▲ ドル円: 152.30
  +0.45 (+0.30%)

堅調な値動き。買い意欲が優勢。

#株式投資 #マーケット速報
```

## セットアップ

### 1. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定

`.env.example` をコピーして `.env` を作成し、Twitter API の認証情報を設定します。

```bash
cp .env.example .env
```

Twitter Developer Portal でAPIキーを取得し、`.env` に記入してください。

### 3. 実行

```bash
# スケジュール通りに自動投稿（常駐）
python main.py

# 起動時に即時実行してからスケジュール稼働
python main.py --run-now
```

## 設定

`.env` ファイルで以下をカスタマイズできます：

| 変数 | 説明 | デフォルト |
|------|------|-----------|
| `STOCK_TICKERS` | 監視するティッカーシンボル（カンマ区切り） | `^N225,^DJI,^GSPC,^IXIC,USDJPY=X` |
| `POST_SCHEDULE` | 投稿時刻（24h形式、カンマ区切り） | `08:00,12:00,18:00` |

## プロジェクト構成

```
xbot/
├── main.py              # エントリポイント・スケジューラー
├── src/
│   ├── stock_data.py    # 株式データ取得
│   ├── post_generator.py # 投稿テキスト生成
│   └── twitter_client.py # Twitter API クライアント
├── requirements.txt
├── .env.example
└── .gitignore
```
