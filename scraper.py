"""
Scraper du doan chung khoan Viet Nam
Su dung Yahoo Finance API (yfinance) + Tu tinh cac chi bao ky thuat bang pandas.
"""
import sys
import io

# Fix encoding cho console Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import yfinance as yf
import pandas as pd
from datetime import datetime

# Ma co phieu VN tren Yahoo Finance co duoi .VN
SYMBOLS_VN = {
    "FPT": "FPT.VN",
    "HPG": "HPG.VN",
    "VCB": "VCB.VN",
    "VIC": "VIC.VN",
    "VNM": "VNM.VN",
    "MWG": "MWG.VN",
    "TCB": "TCB.VN",
    "SSI": "SSI.VN",
    "VHM": "VHM.VN",
    "VPB": "VPB.VN",
    "MSN": "MSN.VN",
    "ACB": "ACB.VN",
    "GAS": "GAS.VN",
    "SAB": "SAB.VN",
    "CTG": "CTG.VN",
}

INTERVAL_LABELS = {
    "1_day": "1 Ngay",
    "1_week": "1 Tuan",
    "1_month": "1 Thang",
}

# --- CACHE ---
_cache = {}
CACHE_TTL_SECONDS = 300  # Cache 5 phut


# ========== TINH CHI BAO KY THUAT ==========

def calc_sma(series, period):
    """Simple Moving Average"""
    return series.rolling(window=period).mean()

def calc_ema(series, period):
    """Exponential Moving Average"""
    return series.ewm(span=period, adjust=False).mean()

def calc_rsi(series, period=14):
    """Relative Strength Index"""
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calc_macd(series, fast=12, slow=26, signal=9):
    """MACD"""
    ema_fast = calc_ema(series, fast)
    ema_slow = calc_ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = calc_ema(macd_line, signal)
    return macd_line, signal_line

def generate_recommendation(rsi_val, macd_val, macd_signal, sma20, ema20, close_price):
    """
    Tao khuyen nghi dua tren cac chi bao ky thuat.
    Dem so tin hieu mua/ban/trung lap va tra ve khuyen nghi tong hop.
    """
    buy_signals = 0
    sell_signals = 0
    neutral_signals = 0

    # 1. RSI
    if rsi_val is not None:
        if rsi_val < 30:
            buy_signals += 2  # Qua ban - tin hieu mua manh
        elif rsi_val < 45:
            buy_signals += 1
        elif rsi_val > 70:
            sell_signals += 2  # Qua mua - tin hieu ban manh
        elif rsi_val > 55:
            sell_signals += 1
        else:
            neutral_signals += 1

    # 2. MACD
    if macd_val is not None and macd_signal is not None:
        if macd_val > macd_signal:
            buy_signals += 2  # MACD cat len tren signal
        elif macd_val < macd_signal:
            sell_signals += 2
        else:
            neutral_signals += 1

    # 3. SMA20 crossover
    if sma20 is not None and close_price is not None:
        if close_price > sma20:
            buy_signals += 1
        elif close_price < sma20:
            sell_signals += 1
        else:
            neutral_signals += 1

    # 4. EMA20 crossover
    if ema20 is not None and close_price is not None:
        if close_price > ema20:
            buy_signals += 1
        elif close_price < ema20:
            sell_signals += 1
        else:
            neutral_signals += 1

    # Tong hop khuyen nghi
    total = buy_signals + sell_signals + neutral_signals
    if total == 0:
        return "GIU", buy_signals, sell_signals, neutral_signals

    if buy_signals >= sell_signals * 2 and buy_signals >= 4:
        rec = "MUA MANH"
    elif buy_signals > sell_signals:
        rec = "MUA"
    elif sell_signals >= buy_signals * 2 and sell_signals >= 4:
        rec = "BAN MANH"
    elif sell_signals > buy_signals:
        rec = "BAN"
    else:
        rec = "GIU"

    return rec, buy_signals, sell_signals, neutral_signals


def get_stock_predictions(interval_key: str = "1_day"):
    """
    Lay du lieu gia va tinh phan tich ky thuat tu Yahoo Finance.
    """
    # Kiem tra cache
    cache_key = f"predictions_{interval_key}"
    if cache_key in _cache:
        cached_time, cached_data = _cache[cache_key]
        age = (datetime.now() - cached_time).total_seconds()
        if age < CACHE_TTL_SECONDS:
            print(f"[CACHE HIT] Returning cached data ({age:.0f}s old)")
            return cached_data

    # Map interval
    period_map = {
        "1_day": ("3mo", "1d"),
        "1_week": ("1y", "1wk"),
        "1_month": ("5y", "1mo"),
    }
    period, yf_interval = period_map.get(interval_key, ("3mo", "1d"))

    predictions = []

    # Lay du lieu tat ca cac ma cung luc (batch download)
    tickers_str = " ".join(SYMBOLS_VN.values())
    print(f"[INFO] Downloading data for: {tickers_str}")

    try:
        data = yf.download(
            tickers=tickers_str,
            period=period,
            interval=yf_interval,
            group_by='ticker',
            auto_adjust=True,
            threads=True,
            progress=False,
        )
    except Exception as e:
        print(f"[ERROR] yfinance download failed: {e}")
        return predictions

    for display_name, ticker in SYMBOLS_VN.items():
        try:
            # Lay du lieu cua tung ma
            if len(SYMBOLS_VN) == 1:
                df = data
            else:
                df = data[ticker].copy()

            if df.empty or len(df) < 20:
                print(f"[SKIP] {display_name}: Not enough data ({len(df)} rows)")
                continue

            # Flatten MultiIndex columns if needed
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            df = df.dropna(subset=["Close"])

            close = df["Close"]
            last_close = float(close.iloc[-1])
            last_open = float(df["Open"].iloc[-1]) if "Open" in df.columns else 0
            last_high = float(df["High"].iloc[-1]) if "High" in df.columns else 0
            last_low = float(df["Low"].iloc[-1]) if "Low" in df.columns else 0
            last_volume = float(df["Volume"].iloc[-1]) if "Volume" in df.columns else 0

            # Tinh chi bao
            sma20_series = calc_sma(close, 20)
            ema20_series = calc_ema(close, 20)
            rsi_series = calc_rsi(close, 14)
            macd_line, signal_line = calc_macd(close)

            sma20 = float(sma20_series.iloc[-1]) if not pd.isna(sma20_series.iloc[-1]) else None
            ema20 = float(ema20_series.iloc[-1]) if not pd.isna(ema20_series.iloc[-1]) else None
            rsi_val = float(rsi_series.iloc[-1]) if not pd.isna(rsi_series.iloc[-1]) else None
            macd_val = float(macd_line.iloc[-1]) if not pd.isna(macd_line.iloc[-1]) else None
            macd_sig = float(signal_line.iloc[-1]) if not pd.isna(signal_line.iloc[-1]) else None

            # Tinh thay doi gia
            if len(close) >= 2:
                prev_close = float(close.iloc[-2])
                change = last_close - prev_close
                change_pct = (change / prev_close) * 100 if prev_close != 0 else 0
            else:
                change = 0
                change_pct = 0

            # Tao khuyen nghi
            rec, buy_sig, sell_sig, neutral_sig = generate_recommendation(
                rsi_val, macd_val, macd_sig, sma20, ema20, last_close
            )

            total_sig = buy_sig + sell_sig + neutral_sig

            predictions.append({
                "symbol": display_name,
                "recommendation": rec,
                "buy_signals": buy_sig,
                "sell_signals": sell_sig,
                "neutral_signals": neutral_sig,
                "buy_pct": round(buy_sig / total_sig * 100, 1) if total_sig > 0 else 0,
                "sell_pct": round(sell_sig / total_sig * 100, 1) if total_sig > 0 else 0,
                "neutral_pct": round(neutral_sig / total_sig * 100, 1) if total_sig > 0 else 0,
                "close_price": round(last_close, 0),
                "open_price": round(last_open, 0),
                "high_price": round(last_high, 0),
                "low_price": round(last_low, 0),
                "volume": int(last_volume),
                "change": round(change, 0),
                "change_pct": round(change_pct, 2),
                "rsi": round(rsi_val, 2) if rsi_val else None,
                "macd": round(macd_val, 2) if macd_val else None,
                "ema20": round(ema20, 2) if ema20 else None,
                "sma20": round(sma20, 2) if sma20 else None,
            })
            print(f"[OK] {display_name}: {rec} | Close: {last_close:,.0f} | RSI: {rsi_val:.1f}" if rsi_val else f"[OK] {display_name}: {rec}")

        except Exception as e:
            print(f"[ERROR] {display_name}: {e}")

    # Luu cache
    if predictions:
        _cache[cache_key] = (datetime.now(), predictions)
        print(f"[CACHE SET] Saved {len(predictions)} items")

    return predictions


def get_market_summary():
    predictions = get_stock_predictions("1_day")
    total = len(predictions)
    buy_count = sum(1 for p in predictions if "MUA" in p["recommendation"])
    sell_count = sum(1 for p in predictions if "BAN" in p["recommendation"])
    neutral_count = sum(1 for p in predictions if p["recommendation"] == "GIU")
    return {
        "total": total,
        "buy_count": buy_count,
        "sell_count": sell_count,
        "neutral_count": neutral_count,
        "predictions": predictions,
        "updated_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    }


if __name__ == "__main__":
    result = get_market_summary()
    print(f"\nTong: {result['total']} | MUA: {result['buy_count']} | GIU: {result['neutral_count']} | BAN: {result['sell_count']}")
    for p in result["predictions"]:
        print(f"  {p['symbol']:>5}: {p['recommendation']:<10} | Gia: {p['close_price']:>10,.0f} | RSI: {p.get('rsi', 'N/A')}")
