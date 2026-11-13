"""Quotes retain provider timestamps; offline observations are explicitly synthetic."""
import re
from datetime import datetime, timezone


def validate_symbol(symbol):
    symbol = symbol.strip().upper()
    if not re.fullmatch(r'[A-Z0-9^][A-Z0-9.\-^=]{0,14}', symbol):
        raise ValueError('Enter a valid ticker, for example AAPL or INFY.NS.')
    return symbol


def market_data(symbol, demo=True):
    symbol = validate_symbol(symbol)
    if demo:
        if symbol != 'AAPL':
            return {'status': 'unavailable', 'symbol': symbol, 'message': 'Offline fixture only supports AAPL. Enable live mode for another ticker.'}
        prices = [100, 101, 100.5, 102, 101.8, 103, 102.2, 104, 103.5, 105]
        return {'status': 'ok', 'symbol': symbol, 'mode': 'synthetic demo', 'currency': 'DEMO',
                'last_close': prices[-1], 'period_change_pct': 5.0,
                'as_of': 'synthetic session 10; not a real quote',
                'history': [{'session': str(i + 1), 'close': p} for i, p in enumerate(prices)]}
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        history = ticker.history(period='1mo', interval='1d', auto_adjust=True, timeout=15)
        if history.empty:
            return {'status': 'unavailable', 'symbol': symbol, 'message': 'Provider returned no price history.'}
        close = history['Close'].dropna()
        if len(close) < 2 or float(close.iloc[0]) <= 0:
            return {'status': 'unavailable', 'symbol': symbol, 'message': 'Insufficient price observations.'}
        return {'status': 'ok', 'symbol': symbol, 'mode': 'Yahoo Finance daily adjusted close; may be delayed',
                'currency': ticker.history_metadata.get('currency', 'unknown'),
                'last_close': round(float(close.iloc[-1]), 4),
                'period_change_pct': round(float((close.iloc[-1] / close.iloc[0] - 1) * 100), 2),
                'as_of': str(close.index[-1]), 'fetched_at': datetime.now(timezone.utc).isoformat(),
                'history': [{'session': str(d.date()), 'close': round(float(p), 4)} for d, p in close.items()]}
    except Exception:
        # Do not disclose provider internals, credentials, or raw response text to users.
        return {'status': 'unavailable', 'symbol': symbol, 'message': 'Market provider could not be reached. Try again later.'}
