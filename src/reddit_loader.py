"""Reddit (PRAW) からサブレディットの投稿を取得する。"""

import os

import praw
from tenacity import retry, stop_after_attempt, wait_exponential

from src.utils import setup_logger

logger = setup_logger(__name__)

TARGET_SUBREDDITS = ["wallstreetbets", "stocks", "investing"]


def _create_reddit() -> praw.Reddit:
    """環境変数から認証情報を取得して PRAW インスタンスを生成する。"""
    return praw.Reddit(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        user_agent="xbot/1.0 (by u/xbot-stock-tracker)",
    )


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=2, max=30))
def _fetch_subreddit_hot(reddit: praw.Reddit, subreddit_name: str, limit: int) -> list:
    """サブレディットの HOT 投稿を取得する。"""
    subreddit = reddit.subreddit(subreddit_name)
    return list(subreddit.hot(limit=limit))


def fetch_posts(limit: int = 10) -> list[dict]:
    """対象サブレディットから HOT 投稿を取得する。

    Returns:
        list[dict]: 各要素は以下のキーを持つ。
            - id: Reddit 投稿 ID
            - subreddit: サブレディット名
            - title: 投稿タイトル
            - selftext: 本文 (あれば)
            - score: スコア
            - url: 投稿 URL
    """
    reddit = _create_reddit()
    results: list[dict] = []

    for sub_name in TARGET_SUBREDDITS:
        try:
            posts = _fetch_subreddit_hot(reddit, sub_name, limit)
        except Exception:
            logger.exception("Reddit 取得失敗 (subreddit=%s)", sub_name)
            continue

        for post in posts:
            results.append(
                {
                    "id": post.id,
                    "subreddit": sub_name,
                    "title": post.title,
                    "selftext": post.selftext[:500] if post.selftext else "",
                    "score": post.score,
                    "url": f"https://reddit.com{post.permalink}",
                }
            )

    logger.info("Reddit 投稿取得完了: %d 件", len(results))
    return results
