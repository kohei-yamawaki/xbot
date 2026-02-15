"""X (Twitter) クライアント — 402/403 で絶対にクラッシュさせない。"""

import os

import tweepy

from src.utils import setup_logger

logger = setup_logger(__name__)


def _create_client() -> tweepy.Client:
    """環境変数から認証情報を取得して tweepy.Client を生成する。"""
    return tweepy.Client(
        consumer_key=os.environ.get("X_API_KEY", ""),
        consumer_secret=os.environ.get("X_API_SECRET", ""),
        access_token=os.environ.get("X_ACCESS_TOKEN", ""),
        access_token_secret=os.environ.get("X_ACCESS_TOKEN_SECRET", ""),
    )


def post_tweet(text: str) -> bool:
    """ツイートを投稿する。失敗しても絶対にクラッシュさせない。

    Returns:
        True: 投稿成功
        False: 投稿失敗 (エラーはログに記録済み)
    """
    try:
        client = _create_client()
        response = client.create_tweet(text=text)
        logger.info("X 投稿成功: id=%s", response.data["id"])
        return True

    except tweepy.Forbidden:
        # 403 Forbidden — API 権限不足
        logger.warning("X Posting Skipped (Cost/Permission): 403 Forbidden")
        return False

    except tweepy.errors.HTTPException as e:
        # 402 Payment Required は tweepy に専用例外がないため status_code で判定
        status = getattr(e.response, "status_code", None) if hasattr(e, "response") else None
        if status == 402:
            logger.warning("X Posting Skipped (Cost/Permission): 402 Payment Required")
            return False
        logger.warning("X Posting Skipped (HTTP %s): %s", status, e)
        return False

    except Exception as e:
        # その他あらゆる例外もクラッシュさせない
        logger.warning("X Posting Skipped (Unexpected): %s", e)
        return False
