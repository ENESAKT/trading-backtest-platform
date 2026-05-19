from datetime import datetime

LIFECYCLE_STATES = [
    "draft",
    "pretest",
    "optimized",
    "wfa_passed",
    "monte_carlo_passed",
    "paper_watching",
    "retired"
]

VALID_TRANSITIONS = {
    "draft": ["pretest", "retired"],
    "pretest": ["draft", "optimized", "retired"],
    "optimized": ["pretest", "wfa_passed", "retired"],
    "wfa_passed": ["optimized", "monte_carlo_passed", "retired"],
    "monte_carlo_passed": ["wfa_passed", "paper_watching", "retired"],
    "paper_watching": ["monte_carlo_passed", "retired"],
    "retired": ["draft"] # Can resurrect to draft
}

def can_transition(current_state: str, new_state: str) -> bool:
    """
    Validates if a strategy can transition from current_state to new_state.
    """
    if current_state not in LIFECYCLE_STATES or new_state not in LIFECYCLE_STATES:
        return False
    return new_state in VALID_TRANSITIONS.get(current_state, [])

def get_next_logical_step(current_state: str) -> str:
    """
    Returns the most logical next step for the strategy lifecycle.
    """
    flow = {
        "draft": "pretest",
        "pretest": "optimized",
        "optimized": "wfa_passed",
        "wfa_passed": "monte_carlo_passed",
        "monte_carlo_passed": "paper_watching",
        "paper_watching": "retired",
        "retired": "none"
    }
    return flow.get(current_state, "none")

def generate_risk_cards(metrics: dict) -> list[dict]:
    """
    Generates risk cards (data, overfit, liquidity, slippage, short sim, repaint).
    Returns a JSON serializable list of dicts.
    """
    cards = []

    # 1. Data Risk
    if metrics.get("data_gap_pct", 0.0) > 1.0 or metrics.get("bar_count", 0) < 500:
        cards.append({
            "type": "data_risk",
            "severity": "high",
            "title": "Veri Eksikliği / Yetersiz Bar",
            "description": "Strateji yeterince uzun bir dönemde veya temiz veride test edilmedi."
        })

    # 2. Overfit Risk
    if metrics.get("param_count", 1) > 5 or metrics.get("wfa_passed") is False:
        cards.append({
            "type": "overfit_risk",
            "severity": "high",
            "title": "Aşırı Optimizasyon (Overfit) Riski",
            "description": "Çok fazla parametre kullanıldı veya WFA doğrulamasından geçemedi."
        })

    # 3. Liquidity Risk
    avg_volume = metrics.get("avg_volume")
    if avg_volume is None:
        cards.append({
            "type": "liquidity_risk",
            "severity": "medium",
            "title": "Kapasite Verisi Yok",
            "description": "Hacim verisi sağlanmadı; likidite/kapasite kartı hesaplanamadı.",
            "capacity": "veri yetersiz",
        })
    elif avg_volume < 100000:
        cards.append({
            "type": "liquidity_risk",
            "severity": "medium",
            "title": "Düşük Likidite",
            "description": "Sinyal üretilen varlık sığ. Gerçekte slippage çok yüksek olabilir.",
        })

    # 4. Slippage Risk
    if not metrics.get("has_slippage_assumptions", False):
        cards.append({
            "type": "slippage_risk",
            "severity": "high",
            "title": "Slippage/Komisyon Yok",
            "description": "Backtest maliyetleri hesaba katılmamış. Kârlılık yanıltıcıdır."
        })

    # 5. Short Simulation Risk
    if metrics.get("market") == "BIST" and metrics.get("allows_short", False):
        cards.append({
            "type": "short_sim_risk",
            "severity": "high",
            "title": "BIST Short Simülasyonu",
            "description": "BIST'te açığa satış kısıtlamaları (uptick rule vb.) vardır. Teorik backtest gerçekleşmeyebilir."
        })

    # 6. Repaint Risk
    if metrics.get("uses_future_data", False) or metrics.get("intrabar_fill", False):
        cards.append({
            "type": "repaint_risk",
            "severity": "critical",
            "title": "Repaint / Gelecek Verisi Riski",
            "description": "Strateji mantığında geçmişe dönük değişiklik veya bar kapanmadan gerçekleşme varsayımı var."
        })

    return cards

def generate_postmortem(
    strategy_id: str,
    reason: str,
    lesson: str,
    metrics_summary: dict,
    tags: list[str] = None
) -> dict:
    """
    Generates a postmortem report for a retired strategy.
    JSON serializable dict.
    """
    return {
        "strategy_id": strategy_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "reason": reason,
        "lesson_learned": lesson,
        "metrics_summary": metrics_summary,
        "tags": tags or []
    }
