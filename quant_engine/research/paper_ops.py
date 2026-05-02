import pandas as pd


def get_robot_summary(state: dict) -> dict:
    """
    Produces a summary for a paper robot's state.
    """
    return {
        "robot_id": state.get("robot_id", "unknown"),
        "strategy_id": state.get("strategy_id", "unknown"),
        "strategy_label": state.get("strategy_label", ""),
        "symbol": state.get("symbol", ""),
        "timeframe": state.get("timeframe", ""),
        "status": state.get("status", "stopped"),
        "last_signal": state.get("last_signal", "none"),
        "last_signal_time": state.get("last_signal_time", None),
        "last_order": state.get("last_order", None),
        "pnl_pct": float(state.get("pnl_pct", 0.0)),
        "daily_drawdown_pct": float(state.get("daily_drawdown_pct", 0.0)),
        "health": state.get("health", "unknown"),
        "warnings": list(state.get("warnings", []))
    }

def kill_all_robots(active_robots: list[dict]) -> dict:
    """
    Kill switch for all paper robots. Returns a dict of commands.
    """
    commands = []
    for r in active_robots:
        if r.get("status") == "active":
            commands.append({"robot_id": r.get("robot_id"), "action": "stop", "reason": "global_kill_switch"})
    return {"affected_count": len(commands), "commands": commands}

def kill_robot(robot_id: str, active_robots: list[dict], reason: str = "manual_kill") -> dict:
    """
    Kill switch for a specific robot.
    """
    for r in active_robots:
        if r.get("robot_id") == robot_id and r.get("status") == "active":
            return {"robot_id": robot_id, "action": "stop", "reason": reason}
    return {"robot_id": robot_id, "action": "none", "reason": "not_active_or_not_found"}

def reduce_risk_limit(robot_state: dict, new_limit: float) -> dict:
    """
    Reduces the daily risk limit of a robot.
    """
    current_limit = robot_state.get("daily_risk_limit", 100.0)
    if new_limit >= current_limit:
        return {"action": "rejected", "reason": "new_limit_must_be_lower", "current": current_limit}

    return {
        "action": "update_limit",
        "robot_id": robot_state.get("robot_id"),
        "new_limit": float(new_limit),
        "reason": "risk_reduction"
    }

def generate_preflight_checklist(metrics: dict) -> dict:
    """
    Generates a pre-flight checklist before starting a robot.
    """
    checklist = {
        "has_real_data": metrics.get("has_real_data", False),
        "has_enough_bars": metrics.get("bar_count", 0) > 200,
        "wfa_passed": metrics.get("wfa_passed", False),
        "monte_carlo_passed": metrics.get("monte_carlo_passed", False),
        "has_slippage_assumptions": metrics.get("has_slippage", False),
        "liquidity_warning": metrics.get("avg_volume", 0) < 100000,
        "short_bist_warning": metrics.get("market") == "BIST" and metrics.get("allows_short", False)
    }

    ready_to_start = (
        checklist["has_real_data"] and
        checklist["has_enough_bars"] and
        checklist["wfa_passed"] and
        not checklist["liquidity_warning"]
    )

    return {
        "checklist": checklist,
        "ready_to_start": ready_to_start,
        "warnings": [k for k, v in checklist.items() if (k.endswith("warning") and v) or not v and not k.endswith("warning")]
    }

def process_signal_action(signal_dict: dict) -> dict:
    """
    Separates alarm logic from paper trade execution logic.
    """
    signal_type = signal_dict.get("type")
    is_live = signal_dict.get("is_live_bar", False)

    if not is_live:
        return {"action": "none", "reason": "historical_signal_ignored"}

    if signal_dict.get("mode") == "alarm_only":
        return {
            "action": "alarm",
            "message": f"{signal_dict.get('symbol')} için {signal_type} sinyali alındı.",
            "reason": "mode_is_alarm_only"
        }

    return {
        "action": "paper_trade",
        "signal_type": signal_type,
        "symbol": signal_dict.get("symbol"),
        "reason": "live_signal_in_trade_mode"
    }

def is_safe_to_trade_gap(df: pd.DataFrame, max_gap_pct: float = 2.0) -> dict:
    """
    Filter for gap / rollover risks.
    """
    if len(df) < 2:
        return {"safe": False, "reason": "insufficient_data"}

    prev_close = df['close'].iloc[-2]
    curr_open = df['open'].iloc[-1]

    if pd.isna(prev_close) or pd.isna(curr_open) or prev_close == 0:
        return {"safe": False, "reason": "invalid_price_data"}

    gap_pct = abs(curr_open - prev_close) / prev_close * 100

    if gap_pct > max_gap_pct:
        return {"safe": False, "reason": f"gap_too_large_{gap_pct:.1f}pct", "gap_pct": float(gap_pct)}

    return {"safe": True, "reason": "normal_gap", "gap_pct": float(gap_pct)}
