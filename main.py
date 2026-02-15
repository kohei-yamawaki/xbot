"""株式市場Twitter Bot - メインエントリポイント"""

import os
import sys
import time

import schedule
from dotenv import load_dotenv

from src.stock_data import fetch_stock_data
from src.post_generator import generate_market_post
from src.twitter_client import create_client, post_tweet


def load_config() -> dict:
    """環境変数から設定を読み込む。"""
    load_dotenv()

    required_keys = [
        "TWITTER_API_KEY",
        "TWITTER_API_SECRET",
        "TWITTER_ACCESS_TOKEN",
        "TWITTER_ACCESS_TOKEN_SECRET",
    ]
    config = {}
    missing = []
    for key in required_keys:
        value = os.getenv(key)
        if not value:
            missing.append(key)
        config[key] = value

    if missing:
        print(f"[ERROR] 必須環境変数が未設定: {', '.join(missing)}")
        print("  .env.example を参考に .env ファイルを作成してください。")
        sys.exit(1)

    config["STOCK_TICKERS"] = os.getenv(
        "STOCK_TICKERS", "^N225,^DJI,^GSPC,^IXIC,USDJPY=X"
    ).split(",")
    config["POST_SCHEDULE"] = os.getenv(
        "POST_SCHEDULE", "08:00,12:00,18:00"
    ).split(",")

    return config


def run_job(config: dict) -> None:
    """株式データ取得 → ポスト生成 → 投稿 の一連の処理を実行する。"""
    print(f"[INFO] ジョブ開始")

    stock_data = fetch_stock_data(config["STOCK_TICKERS"])
    if not stock_data:
        print("[WARN] 株式データを取得できませんでした。投稿をスキップします。")
        return

    post_text = generate_market_post(stock_data)
    if not post_text:
        print("[WARN] 投稿テキストの生成に失敗しました。")
        return

    print(f"[INFO] 生成されたポスト:\n{post_text}")

    client = create_client(
        api_key=config["TWITTER_API_KEY"],
        api_secret=config["TWITTER_API_SECRET"],
        access_token=config["TWITTER_ACCESS_TOKEN"],
        access_token_secret=config["TWITTER_ACCESS_TOKEN_SECRET"],
    )
    post_tweet(client, post_text)


def main() -> None:
    """メイン処理。スケジューラーを起動してbot を常駐させる。"""
    config = load_config()

    print("[INFO] 株式市場Twitter Bot を起動します")
    print(f"[INFO] 監視銘柄: {', '.join(config['STOCK_TICKERS'])}")
    print(f"[INFO] 投稿スケジュール: {', '.join(config['POST_SCHEDULE'])}")

    # スケジュール登録
    for time_str in config["POST_SCHEDULE"]:
        time_str = time_str.strip()
        schedule.every().day.at(time_str).do(run_job, config=config)
        print(f"[INFO] スケジュール登録: 毎日 {time_str}")

    # 起動時に1回即時実行するかどうか
    if "--run-now" in sys.argv:
        print("[INFO] --run-now 指定のため即時実行します")
        run_job(config)

    # スケジューラーループ
    print("[INFO] スケジューラー稼働中... (Ctrl+C で停止)")
    try:
        while True:
            schedule.run_pending()
            time.sleep(30)
    except KeyboardInterrupt:
        print("\n[INFO] Bot を停止しました")


if __name__ == "__main__":
    main()
