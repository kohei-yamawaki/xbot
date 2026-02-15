"""Google Gen AI SDK integration — Gemini 2.0 Flash."""

import json
import os

from google import genai
from tenacity import retry, stop_after_attempt, wait_exponential

from src.utils import setup_logger

logger = setup_logger(__name__)

SYSTEM_PROMPT = """\
あなたは経験20年超の辛口・日本人株式アナリストです。
米国株のニュースや Reddit の投稿を読み、短く鋭い日本語コメントを生成してください。

## ルール
- 出力は **必ず JSON** で返すこと。マークダウンのコードブロックで囲まないこと。
- JSON スキーマ:
  {"post_text": "...", "sentiment": "BULLISH or BEARISH", "reason": "..."}
- post_text は **280文字以内** の X (Twitter) 投稿文とする。
  - ティッカーシンボルを $XXXX 形式で含める。
  - センチメントに応じた絵文字を 1 つ付ける（🐂 or 🐻）。
- sentiment は "BULLISH" または "BEARISH" のいずれかとする。
- reason は判断根拠を 1〜2 文で簡潔に述べる。

## 投資助言に関する制約（厳守）
- 「〜すべき」「買い/売り推奨」など断定的な投資助言は **絶対に行わない**。
- 「〜の可能性がある」「〜とみられる」「〜かもしれない」など推量表現を使う。
- 文末に「※投資は自己責任で」等の免責文言を含める必要はないが、
  読者が投資判断の根拠としないよう配慮した表現を用いること。
"""


def _create_client() -> genai.Client:
    """環境変数から API キーを取得して Client を生成する。"""
    api_key = os.environ.get("GOOGLE_API_KEY", "")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY が設定されていません")
    return genai.Client(api_key=api_key)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=2, max=30))
def analyze(text: str) -> dict:
    """ニュース/Reddit テキストを Gemini に渡し、構造化された分析結果を返す。

    Returns:
        dict: {"post_text": str, "sentiment": str, "reason": str}
    """
    client = _create_client()

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=text,
        config=genai.types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.7,
        ),
    )

    raw = response.text.strip()
    logger.info("Gemini raw response: %s", raw)

    result = json.loads(raw)

    # バリデーション
    required_keys = {"post_text", "sentiment", "reason"}
    missing = required_keys - result.keys()
    if missing:
        raise ValueError(f"Gemini 応答に必須キーが不足: {missing}")

    if result["sentiment"] not in ("BULLISH", "BEARISH"):
        raise ValueError(f"sentiment が不正: {result['sentiment']}")

    if len(result["post_text"]) > 280:
        logger.warning("post_text が280文字超 (%d文字)。切り詰めます。", len(result["post_text"]))
        result["post_text"] = result["post_text"][:280]

    return result
