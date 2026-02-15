"""Pillow による OGP / Twitter Card 画像生成。"""

import pathlib

from PIL import Image, ImageDraw, ImageFont
from tenacity import retry, stop_after_attempt, wait_exponential

from src.utils import setup_logger

logger = setup_logger(__name__)

# Twitter Card 推奨サイズ
WIDTH = 1200
HEIGHT = 675

# カラーパレット
BULLISH_BG = (16, 138, 62)     # 緑基調
BEARISH_BG = (190, 30, 45)     # 赤基調
TEXT_COLOR = (255, 255, 255)
SUB_TEXT_COLOR = (220, 220, 220)


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """利用可能なフォントを読み込む。見つからなければデフォルトフォントを返す。"""
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for path in candidates:
        if pathlib.Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=5))
def generate_card(
    ticker: str,
    sentiment: str,
    reason: str,
    output_path: str | pathlib.Path,
) -> pathlib.Path:
    """センチメントカード画像を生成して保存する。

    Args:
        ticker: ティッカーシンボル (例: "NVDA")
        sentiment: "BULLISH" or "BEARISH"
        reason: 短い解説テキスト
        output_path: 保存先パス

    Returns:
        保存先の Path オブジェクト
    """
    output_path = pathlib.Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    bg_color = BULLISH_BG if sentiment == "BULLISH" else BEARISH_BG
    emoji = "\u2191 BULLISH" if sentiment == "BULLISH" else "\u2193 BEARISH"

    img = Image.new("RGB", (WIDTH, HEIGHT), bg_color)
    draw = ImageDraw.Draw(img)

    # ティッカーシンボル (大きく中央上部)
    font_ticker = _load_font(120)
    ticker_text = f"${ticker}"
    bbox = draw.textbbox((0, 0), ticker_text, font=font_ticker)
    tw = bbox[2] - bbox[0]
    draw.text(((WIDTH - tw) / 2, 100), ticker_text, fill=TEXT_COLOR, font=font_ticker)

    # センチメントラベル
    font_sentiment = _load_font(60)
    bbox = draw.textbbox((0, 0), emoji, font=font_sentiment)
    sw = bbox[2] - bbox[0]
    draw.text(((WIDTH - sw) / 2, 280), emoji, fill=TEXT_COLOR, font=font_sentiment)

    # 区切り線
    line_y = 380
    draw.line([(100, line_y), (WIDTH - 100, line_y)], fill=SUB_TEXT_COLOR, width=2)

    # 理由テキスト (折り返し)
    font_reason = _load_font(32)
    _draw_wrapped_text(draw, reason, font_reason, SUB_TEXT_COLOR, 80, 420, WIDTH - 160)

    img.save(str(output_path), quality=95)
    logger.info("画像生成完了: %s", output_path)
    return output_path


def _draw_wrapped_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    fill: tuple,
    x: int,
    y: int,
    max_width: int,
) -> None:
    """テキストを max_width 内で折り返して描画する。"""
    words = list(text)
    lines: list[str] = []
    current_line = ""

    for char in words:
        test = current_line + char
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current_line = test
        else:
            if current_line:
                lines.append(current_line)
            current_line = char

    if current_line:
        lines.append(current_line)

    line_height = draw.textbbox((0, 0), "あ", font=font)[3] + 8
    for i, line in enumerate(lines):
        draw.text((x, y + i * line_height), line, fill=fill, font=font)
