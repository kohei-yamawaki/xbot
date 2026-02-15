"""ポスト内容を生成するモジュール"""

from datetime import datetime


def _format_price(price: float) -> str:
    """価格を見やすくフォーマットする。"""
    if price >= 100:
        return f"{price:,.0f}"
    return f"{price:,.2f}"


def _change_indicator(change_pct: float) -> str:
    """変動率に応じた矢印を返す。"""
    if change_pct >= 2.0:
        return "📈⬆️"
    elif change_pct >= 0.5:
        return "📈"
    elif change_pct > 0:
        return "▲"
    elif change_pct <= -2.0:
        return "📉⬇️"
    elif change_pct <= -0.5:
        return "📉"
    elif change_pct < 0:
        return "▼"
    return "→"


def _format_change(change: float, change_pct: float) -> str:
    """変動額と変動率をフォーマットする。"""
    sign = "+" if change >= 0 else ""
    if abs(change) >= 1:
        return f"{sign}{change:,.0f} ({sign}{change_pct:.2f}%)"
    return f"{sign}{change:.2f} ({sign}{change_pct:.2f}%)"


def generate_market_post(stock_data: list[dict]) -> str:
    """株式市場データからTwitter投稿用テキストを生成する。

    280文字（Twitter上限）以内に収まるよう調整する。
    """
    if not stock_data:
        return ""

    now = datetime.now()
    date_str = now.strftime("%m/%d %H:%M")

    lines = [f"【株式市場速報 {date_str}】", ""]

    for data in stock_data:
        indicator = _change_indicator(data["change_pct"])
        price_str = _format_price(data["price"])
        change_str = _format_change(data["change"], data["change_pct"])
        lines.append(f"{indicator} {data['name']}: {price_str}")
        lines.append(f"  {change_str}")

    # 市場全体のサマリーコメントを追加
    summary = _generate_summary(stock_data)
    if summary:
        lines.append("")
        lines.append(summary)

    lines.append("")
    lines.append("#株式投資 #マーケット速報")

    post = "\n".join(lines)

    # Twitterの文字数制限（280文字）チェック
    if len(post) > 280:
        # ハッシュタグを短縮
        lines[-1] = "#株式市場"
        post = "\n".join(lines)

    if len(post) > 280:
        # サマリーを削除して再構成
        lines_without_summary = [l for i, l in enumerate(lines)
                                  if i < len(stock_data) * 2 + 2]
        lines_without_summary.append("")
        lines_without_summary.append("#株式市場")
        post = "\n".join(lines_without_summary)

    return post


def _generate_summary(stock_data: list[dict]) -> str:
    """市場全体の動向からサマリーコメントを生成する。"""
    if not stock_data:
        return ""

    avg_change = sum(d["change_pct"] for d in stock_data) / len(stock_data)

    # 最も変動が大きい銘柄を特定
    most_moved = max(stock_data, key=lambda d: abs(d["change_pct"]))

    if avg_change >= 1.5:
        return "全面高の展開。リスクオン相場が継続中。"
    elif avg_change >= 0.5:
        return "堅調な値動き。買い意欲が優勢。"
    elif avg_change <= -1.5:
        return "全面安の展開。リスクオフの流れが強まる。"
    elif avg_change <= -0.5:
        return "やや軟調。売り圧力がやや優勢。"
    elif abs(most_moved["change_pct"]) >= 2.0:
        direction = "上昇" if most_moved["change_pct"] > 0 else "下落"
        return f"{most_moved['name']}が大幅{direction}。他は小動き。"
    else:
        return "小動きの展開。方向感に乏しい。"
