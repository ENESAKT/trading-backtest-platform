from typing import Dict, Any, Optional

def fixed_bps_slippage(price: float, side: str, bps: float) -> float:
    """
    Apply a fixed basis point slippage to a price.
    For BUY orders, slippage increases the price.
    For SELL (and SHORT) orders, slippage decreases the price.
    """
    if price <= 0:
        return price
        
    slippage_amount = price * (bps / 10000.0)
    
    side_upper = side.upper()
    if side_upper == "BUY" or side_upper == "COVER":
        return price + slippage_amount
    elif side_upper == "SELL" or side_upper == "SHORT":
        return price - slippage_amount
    else:
        # Default fallback, no slippage applied for unknown side
        return price

def fixed_tick_slippage(price: float, side: str, tick_size: float, ticks: int) -> float:
    """
    Apply a fixed tick slippage to a price.
    For BUY orders, slippage increases the price by (tick_size * ticks).
    For SELL orders, slippage decreases the price by (tick_size * ticks).
    """
    if price <= 0 or tick_size <= 0 or ticks <= 0:
        return price
        
    slippage_amount = tick_size * ticks
    
    side_upper = side.upper()
    if side_upper == "BUY" or side_upper == "COVER":
        return price + slippage_amount
    elif side_upper == "SELL" or side_upper == "SHORT":
        return max(0.0, price - slippage_amount)
    else:
        return price

def volume_capacity_warning(order_value: float, avg_volume_value: float, max_participation_pct: float) -> Optional[str]:
    """
    Check if the order value exceeds the maximum allowed participation in the average volume.
    Returns a warning message if it does, else None.
    """
    if avg_volume_value <= 0:
        return "Market volume is zero or negative, illiquid symbol."
        
    participation_pct = (order_value / avg_volume_value) * 100.0
    
    if participation_pct > max_participation_pct:
        return f"Order value ({order_value:.2f}) exceeds max participation limit ({max_participation_pct}%) of avg volume ({avg_volume_value:.2f}). Current participation: {participation_pct:.2f}%"
        
    return None

def build_assumption_card(
    slippage_bps: float = 0.0,
    tick_size: float = 0.0,
    commission_rate: float = 0.0,
    max_participation_pct: float = 0.0,
    is_short_bist: bool = False
) -> Dict[str, Any]:
    """
    Build a JSON serializable assumption card for reporting and debugging.
    """
    warnings = []
    if is_short_bist:
        warnings.append("SHORT on BIST symbols requires uptick rule compliance and borrow availability. Results may be overly optimistic.")
        
    return {
        "slippage_bps": slippage_bps,
        "tick_size": tick_size,
        "commission_rate": commission_rate,
        "max_participation_pct": max_participation_pct,
        "is_short_bist": is_short_bist,
        "warnings": warnings
    }
