"""株式市場データの取得モジュール"""

import yfinance as yf


TICKER_NAMES = {
    "^N225": "日経平均",
    "^DJI": "NYダウ",
    "^GSPC": "S&P500",
    "^IXIC": "NASDAQ",
    "USDJPY=X": "ドル円",
}


def fetch_stock_data(tickers: list[str]) -> list[dict]:
    """指定されたティッカーの最新データを取得する。

    Returns:
        各ティッカーの情報を含む辞書のリスト。
        取得失敗したティッカーはスキップされる。
    """
    results = []
    for ticker_symbol in tickers:
        try:
            ticker = yf.Ticker(ticker_symbol)
            hist = ticker.history(period="2d")
            if hist.empty or len(hist) < 1:
                continue

            latest = hist.iloc[-1]
            price = latest["Close"]

            if len(hist) >= 2:
                prev_close = hist.iloc[-2]["Close"]
                change = price - prev_close
                change_pct = (change / prev_close) * 100
            else:
                change = 0.0
                change_pct = 0.0

            name = TICKER_NAMES.get(ticker_symbol, ticker_symbol)
            results.append({
                "symbol": ticker_symbol,
                "name": name,
                "price": price,
                "change": change,
                "change_pct": change_pct,
                "high": latest["High"],
                "low": latest["Low"],
                "volume": latest.get("Volume", 0),
            })
        except Exception as e:
            print(f"[WARN] {ticker_symbol} のデータ取得に失敗: {e}")
    return results
