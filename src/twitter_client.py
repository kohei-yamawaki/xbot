"""Twitter (X) API クライアントモジュール"""

import tweepy


def create_client(
    api_key: str,
    api_secret: str,
    access_token: str,
    access_token_secret: str,
) -> tweepy.Client:
    """Twitter API v2 クライアントを生成する。"""
    return tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_token_secret,
    )


def post_tweet(client: tweepy.Client, text: str) -> dict | None:
    """ツイートを投稿する。

    Returns:
        成功時はレスポンスデータ、失敗時はNone。
    """
    if not text:
        print("[WARN] 投稿テキストが空のためスキップ")
        return None

    try:
        response = client.create_tweet(text=text)
        print(f"[INFO] 投稿成功: {text[:50]}...")
        return response.data
    except tweepy.TweepyException as e:
        print(f"[ERROR] 投稿失敗: {e}")
        return None
