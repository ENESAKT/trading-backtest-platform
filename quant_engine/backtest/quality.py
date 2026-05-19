def compute_quality_score(metrics: dict) -> dict:
    """
    Computes a backtest quality score and generates warnings based on standard metrics.
    
    Expected metrics dictionary keys (all optional, defaults assumed if missing):
    - total_trades: int
    - days_tested: int
    - max_drawdown_pct: float (positive number representing percentage, e.g. 20.0 for 20%)
    - param_count: int
    - num_symbols: int
    - intrabar_risks: int (number of warnings/risks related to intrabar data)
    - missing_data_pct: float
    - max_win_contribution_pct: float (percentage of net profit from the single largest win)
    
    Returns:
        dict: {"score": int (0-100), "warnings": [{"message": str, "severity": str}]}
    """
    score = 100.0
    warnings = []

    # Defaults
    total_trades = metrics.get('total_trades', 0)
    days_tested = metrics.get('days_tested', 0)
    mdd = metrics.get('max_drawdown_pct', 0.0)
    param_count = metrics.get('param_count', 1)
    num_symbols = metrics.get('num_symbols', 1)
    intrabar_risks = metrics.get('intrabar_risks', 0)
    missing_data_pct = metrics.get('missing_data_pct', 0.0)
    max_win = metrics.get('max_win_contribution_pct', 0.0)

    # 1. Trade count
    if total_trades < 30:
        score -= 20
        warnings.append({"message": "Düşük işlem sayısı (<30). Sonuçlar istatistiksel olarak anlamsız olabilir.", "severity": "high"})
    elif total_trades < 100:
        score -= 5
        warnings.append({"message": "İşlem sayısı nispeten düşük (<100).", "severity": "medium"})

    # 2. Testing period
    if days_tested < 90:
        score -= 15
        warnings.append({"message": "Kısa test aralığı (<90 gün). Farklı piyasa koşullarını kapsamayabilir.", "severity": "high"})
    elif days_tested < 180:
        score -= 5
        warnings.append({"message": "Test aralığı 6 aydan kısa.", "severity": "medium"})

    # 3. Max Drawdown
    if mdd > 50.0:
        score -= 30
        warnings.append({"message": f"Çok yüksek drawdown (%{mdd:.1f}). Strateji iflas riski taşıyor.", "severity": "high"})
    elif mdd > 30.0:
        score -= 10
        warnings.append({"message": f"Yüksek drawdown (%{mdd:.1f}).", "severity": "medium"})

    # 4. Overfit risk (param count)
    if param_count > 5:
        score -= 15
        warnings.append({"message": f"Çok fazla parametre ({param_count}). Overfit (aşırı optimizasyon) riski yüksek.", "severity": "high"})
    elif param_count > 3:
        score -= 5
        warnings.append({"message": "Parametre sayısı yüksek. Optimizasyona dikkat edin.", "severity": "medium"})

    # 5. Single symbol risk
    if num_symbols == 1:
        score -= 5
        warnings.append({"message": "Tek sembol testi. Strateji bu sembole overfit olmuş olabilir.", "severity": "low"})

    # 6. Intrabar risks
    if intrabar_risks > 0:
        score -= 10
        warnings.append({"message": f"İntrabar (bar içi) gerçekleşme riski tespit edildi ({intrabar_risks} adet). Slippage etkileri yanıltıcı olabilir.", "severity": "medium"})

    # 7. Missing data
    if missing_data_pct > 5.0:
        score -= 20
        warnings.append({"message": f"Yüksek eksik veri oranı (%{missing_data_pct:.1f}). Test güvenilmez.", "severity": "high"})
    elif missing_data_pct > 1.0:
        score -= 5
        warnings.append({"message": f"Verilerde boşluklar var (%{missing_data_pct:.1f}).", "severity": "low"})

    # 8. Outlier effect
    if max_win > 40.0:
        score -= 15
        warnings.append({"message": f"Kârın %{max_win:.1f}'i tek bir işlemden geliyor. Outlier (aykırı değer) etkisi yüksek.", "severity": "high"})
    elif max_win > 20.0:
        score -= 5
        warnings.append({"message": f"Tek işlem kâr katkısı yüksek (%{max_win:.1f}).", "severity": "medium"})

    score = max(0.0, min(100.0, score))

    return {
        "score": int(score),
        "warnings": warnings
    }
