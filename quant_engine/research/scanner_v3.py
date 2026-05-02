import pandas as pd


def scan_market(
    universe_data: dict,
    filters: list = None,
    signal_evaluator=None,
    quality_evaluator=None
) -> list:
    """
    Scans a market universe based on provided data, filters, and evaluators.
    
    Args:
        universe_data: dict of symbol -> pd.DataFrame (must have at least 'close', 'volume', and datetime index/time column)
        filters: list of callables. Each callable takes (df) and returns a boolean or dict. If boolean False, symbol is skipped.
        signal_evaluator: callable that takes (df) and returns (signal_type, signal_time)
        quality_evaluator: callable that takes (symbol, df) and returns a quality score
        
    Returns:
        List of JSON serializable dictionaries.
    """
    results = []

    for symbol, df in universe_data.items():
        if df is None or df.empty:
            results.append({
                "symbol": symbol,
                "last_price": None,
                "signal_type": None,
                "signal_time": None,
                "strategy_quality_score": 0,
                "data_status": "empty",
                "liquidity_warning": False,
                "matched_conditions": [],
                "warnings": ["Veri boş veya yüklenemedi."]
            })
            continue

        last_price = float(df['close'].iloc[-1]) if 'close' in df.columns else None

        # Check filters
        skip = False
        matched_conditions = []
        warnings = []
        liquidity_warning = False
        data_status = "ready"

        if filters:
            for f in filters:
                res = f(df)
                if res is False:
                    skip = True
                    break
                elif isinstance(res, dict):
                    if not res.get('passed', True):
                        skip = True
                        break
                    if 'condition' in res:
                        matched_conditions.append(res['condition'])
                    if res.get('liquidity_warning'):
                        liquidity_warning = True
                    if 'warning' in res:
                        warnings.append(res['warning'])
                    if 'data_status' in res:
                        data_status = res['data_status']

        if skip:
            continue

        signal_type = None
        signal_time = None
        if signal_evaluator:
            s_type, s_time = signal_evaluator(df)
            if s_type:
                signal_type = s_type
                # Convert timestamp to ISO string if needed
                signal_time = s_time.isoformat() if hasattr(s_time, 'isoformat') else str(s_time)

        score = 0
        if quality_evaluator:
            score = quality_evaluator(symbol, df)

        results.append({
            "symbol": symbol,
            "last_price": last_price,
            "signal_type": signal_type,
            "signal_time": signal_time,
            "strategy_quality_score": score,
            "data_status": data_status,
            "liquidity_warning": liquidity_warning,
            "matched_conditions": matched_conditions,
            "warnings": warnings
        })

    return results

# --- Scanner Helper Filters ---

def filter_recent_signal(df: pd.DataFrame, signal_column: str = 'signal', bars_lookback: int = 3):
    if signal_column not in df.columns:
        return False
    recent = df[signal_column].iloc[-bars_lookback:]
    passed = recent.notna().any() and (recent != 0).any()
    return {"passed": passed, "condition": "recent_signal"}

def filter_new_cross(df: pd.DataFrame, col1: str, col2: str):
    if col1 not in df.columns or col2 not in df.columns:
        return False
    s1, s2 = df[col1], df[col2]
    # Check if crossed up or down on the last bar
    curr_diff = s1.iloc[-1] - s2.iloc[-1]
    prev_diff = s1.iloc[-2] - s2.iloc[-2] if len(df) > 1 else curr_diff

    crossed_up = curr_diff > 0 and prev_diff <= 0
    crossed_down = curr_diff < 0 and prev_diff >= 0
    passed = crossed_up or crossed_down
    return {"passed": passed, "condition": f"new_cross_{col1}_{col2}"}

def filter_price_ma_distance(df: pd.DataFrame, ma_col: str, max_pct_distance: float = 5.0):
    if 'close' not in df.columns or ma_col not in df.columns:
        return False
    price = df['close'].iloc[-1]
    ma = df[ma_col].iloc[-1]
    if pd.isna(price) or pd.isna(ma) or ma == 0:
        return False

    dist = abs(price - ma) / ma * 100
    passed = dist <= max_pct_distance
    return {"passed": passed, "condition": f"price_ma_dist_{dist:.1f}%"}

def filter_rsi_zone(df: pd.DataFrame, rsi_col: str = 'rsi', min_val: float = 30.0, max_val: float = 70.0):
    if rsi_col not in df.columns:
        return False
    rsi = df[rsi_col].iloc[-1]
    if pd.isna(rsi):
        return False
    passed = min_val <= rsi <= max_val
    return {"passed": passed, "condition": "rsi_in_zone"}

def filter_volume_above_avg(df: pd.DataFrame, vol_col: str = 'volume', avg_vol_col: str = 'avg_volume'):
    if vol_col not in df.columns or avg_vol_col not in df.columns:
        return False
    vol = df[vol_col].iloc[-1]
    avg = df[avg_vol_col].iloc[-1]
    if pd.isna(vol) or pd.isna(avg):
        return False
    return {"passed": vol > avg, "condition": "volume_above_avg"}

def filter_trend(df: pd.DataFrame, fast_ma: str, slow_ma: str, bullish: bool = True):
    if fast_ma not in df.columns or slow_ma not in df.columns:
        return False
    f = df[fast_ma].iloc[-1]
    s = df[slow_ma].iloc[-1]
    if pd.isna(f) or pd.isna(s):
        return False
    passed = (f > s) if bullish else (f < s)
    return {"passed": passed, "condition": "trend_" + ("bullish" if bullish else "bearish")}

def filter_data_status(df: pd.DataFrame, min_bars: int = 100):
    if len(df) < min_bars:
        return {"passed": True, "data_status": "insufficient_data", "warning": f"Veri yetersiz (<{min_bars} bar)"}
    return {"passed": True, "data_status": "ready"}

def filter_liquidity(df: pd.DataFrame, min_volume: float = 100000, vol_col: str = 'volume'):
    if vol_col not in df.columns:
        return {"passed": True, "liquidity_warning": True, "warning": "Hacim verisi yok"}

    vol = df[vol_col].iloc[-5:].mean() # avg of last 5 bars
    if pd.isna(vol) or vol < min_volume:
        return {"passed": True, "liquidity_warning": True, "warning": "Düşük likidite"}
    return {"passed": True, "liquidity_warning": False}
