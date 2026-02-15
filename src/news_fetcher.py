"""Yahoo Finance RSS からニュースを取得する。"""

import feedparser
from tenacity import retry, stop_after_attempt, wait_exponential

from src.utils import setup_logger

logger = setup_logger(__name__)

# 主要ティッカーごとの Yahoo Finance RSS URL
TICKER_RSS = {
    "NVDA": "https://feeds.finance.yahoo.com/rss/2.0/headline?s=NVDA&region=US&lang=en-US",
    "AAPL": "https://feeds.finance.yahoo.com/rss/2.0/headline?s=AAPL&region=US&lang=en-US",
    "TSLA": "https://feeds.finance.yahoo.com/rss/2.0/headline?s=TSLA&region=US&lang=en-US",
    "MSFT": "https://feeds.finance.yahoo.com/rss/2.0/headline?s=MSFT&region=US&lang=en-US",
    "AMZN": "https://feeds.finance.yahoo.com/rss/2.0/headline?s=AMZN&region=US&lang=en-US",
    "GOOG": "https://feeds.finance.yahoo.com/rss/2.0/headline?s=GOOG&region=US&lang=en-US",
    "META": "https://feeds.finance.yahoo.com/rss/2.0/headline?s=META&region=US&lang=en-US",
}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=2, max=30))
def _fetch_feed(url: str) -> list[dict]:
    """単一の RSS フィードをパースしてエントリ一覧を返す。"""
    feed = feedparser.parse(url)
    if feed.bozo and not feed.entries:
        raise ConnectionError(f"RSS フィードの取得に失敗: {url}")
    return feed.entries


def fetch_news(tickers: list[str] | None = None) -> list[dict]:
    """指定ティッカー (デフォルト: 全件) のニュースを取得する。

    Returns:
        list[dict]: 各要素は以下のキーを持つ。
            - id: エントリの一意識別子 (link)
            - ticker: ティッカーシンボル
            - title: ニュースタイトル
            - link: 記事 URL
            - summary: 概要テキスト
    """
    targets = tickers or list(TICKER_RSS.keys())
    results: list[dict] = []

    for ticker in targets:
        url = TICKER_RSS.get(ticker)
        if not url:
            logger.warning("未登録のティッカー: %s", ticker)
            continue

        try:
            entries = _fetch_feed(url)
        except Exception:
            logger.exception("RSS 取得失敗 (ticker=%s)", ticker)
            continue

        for entry in entries:
            results.append(
                {
                    "id": entry.get("link", entry.get("id", "")),
                    "ticker": ticker,
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "summary": entry.get("summary", ""),
                }
            )

    logger.info("ニュース取得完了: %d 件", len(results))
    return results
