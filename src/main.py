"""Entry point — RSS → 重複チェック → Reddit → LLM → 画像生成 → レポート → X 投稿。"""

import datetime
import pathlib
import sys

from src.image_gen import generate_card
from src.llm_engine import analyze
from src.news_fetcher import fetch_news
from src.reddit_loader import fetch_posts
from src.utils import (
    is_duplicate,
    load_processed_ids,
    save_processed_ids,
    setup_logger,
)
from src.x_client import post_tweet

logger = setup_logger(__name__)

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"


def _today_str() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")


def _build_llm_input(news_items: list[dict], reddit_items: list[dict]) -> str:
    """ニュースと Reddit 投稿を LLM に渡す入力テキストに整形する。"""
    parts: list[str] = []

    if news_items:
        parts.append("## Yahoo Finance ニュース")
        for item in news_items[:10]:
            parts.append(f"- [{item['ticker']}] {item['title']}")
            if item["summary"]:
                parts.append(f"  {item['summary'][:200]}")

    if reddit_items:
        parts.append("\n## Reddit 注目投稿")
        for item in reddit_items[:10]:
            parts.append(f"- [r/{item['subreddit']}] {item['title']} (score: {item['score']})")
            if item["selftext"]:
                parts.append(f"  {item['selftext'][:200]}")

    return "\n".join(parts)


def _append_report(date_str: str, ticker: str, analysis: dict, image_path: pathlib.Path) -> pathlib.Path:
    """レポートを reports/YYYY-MM-DD.md に追記する。"""
    report_path = REPORTS_DIR / f"{date_str}.md"
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # ファイルが存在しなければヘッダーを書く
    if not report_path.exists():
        header = f"# Daily US Stock Report — {date_str}\n\n"
        report_path.write_text(header, encoding="utf-8")

    sentiment_emoji = "\U0001f402" if analysis["sentiment"] == "BULLISH" else "\U0001f43b"
    entry = (
        f"## ${ticker} {sentiment_emoji} {analysis['sentiment']}\n\n"
        f"**Post:**\n> {analysis['post_text']}\n\n"
        f"**Reason:** {analysis['reason']}\n\n"
        f"**Image:** `{image_path.name}`\n\n"
        f"---\n\n"
    )

    with open(report_path, "a", encoding="utf-8") as f:
        f.write(entry)

    logger.info("レポート追記: %s", report_path)
    return report_path


def run() -> None:
    """メインパイプラインを実行する。"""
    date_str = _today_str()
    logger.info("=== xbot 実行開始 (%s) ===", date_str)

    # 1. 処理済み ID をロード
    processed_ids = load_processed_ids()
    logger.info("処理済み ID: %d 件", len(processed_ids))

    # 2. RSS ニュース取得
    news_items = fetch_news()
    logger.info("RSS ニュース: %d 件取得", len(news_items))

    # 3. 重複除外
    new_news = [item for item in news_items if not is_duplicate(item["id"], processed_ids)]
    logger.info("新規ニュース: %d 件 (重複除外後)", len(new_news))

    if not new_news:
        logger.info("新規ニュースなし。Reddit のみで分析を試みます。")

    # 4. Reddit 投稿取得
    reddit_items: list[dict] = []
    try:
        reddit_items = fetch_posts(limit=10)
    except Exception:
        logger.exception("Reddit 取得に失敗。ニュースのみで続行します。")

    new_reddit = [item for item in reddit_items if not is_duplicate(item["id"], processed_ids)]

    # 5. 処理対象がなければ終了
    if not new_news and not new_reddit:
        logger.info("処理対象なし。終了します。")
        return

    # 6. LLM 入力を構築して分析
    llm_input = _build_llm_input(new_news, new_reddit)
    logger.info("LLM 入力テキスト長: %d 文字", len(llm_input))

    try:
        analysis = analyze(llm_input)
    except Exception:
        logger.exception("LLM 分析に失敗。終了します。")
        return

    # ティッカーを特定 (ニュースがあれば先頭、なければ "MKT")
    ticker = new_news[0]["ticker"] if new_news else "MKT"

    # 7. 画像生成
    image_path = REPORTS_DIR / f"{date_str}_{ticker}.png"
    try:
        generate_card(ticker, analysis["sentiment"], analysis["reason"], image_path)
    except Exception:
        logger.exception("画像生成に失敗。レポートは画像なしで続行します。")
        image_path = pathlib.Path("N/A")

    # 8. レポート追記 (ゼロコスト成果物)
    _append_report(date_str, ticker, analysis, image_path)

    # 9. 処理済み ID を更新・保存
    new_ids = [item["id"] for item in new_news] + [item["id"] for item in new_reddit]
    processed_ids.extend(new_ids)
    save_processed_ids(processed_ids)
    logger.info("処理済み ID 更新: +%d 件 (合計 %d 件)", len(new_ids), len(processed_ids))

    # 10. X に投稿 (失敗してもクラッシュしない)
    posted = post_tweet(analysis["post_text"])
    if posted:
        logger.info("X 投稿完了")
    else:
        logger.info("X 投稿スキップ (レポートは正常に保存済み)")

    logger.info("=== xbot 実行完了 ===")


if __name__ == "__main__":
    try:
        run()
    except Exception:
        logger.exception("予期しないエラーが発生しました")
        sys.exit(1)
