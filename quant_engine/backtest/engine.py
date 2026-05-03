"""
Quant Engine — Backtest Engine

Minimal backtest motoru. Tek sembol, long-only, market order.

Execution Spec:
    1. bar[t].close'da sinyal üret
    2. bar[t+1].open'da execute et (lookahead bias yok)
    3. Her barda portfolio invariant doğrula
    4. Audit trail: signal → order → fill → position → pnl

Düzeltmeler (Aşama 2):
    - signal_timestamp artık sinyal barının tarihini yazar
    - execution_timestamp dolum barının tarihini yazar
    - CompletedTrade eşleştirmesi eklendi
    - Açık pozisyonlar final equity'de doğru değerlenir
    - Son barda pending signal açık davranışı tanımlı
    - Negatif nakit koruması
    - Invariant ihlali RuntimeError fırlatır

Kullanım:
    from quant_engine.backtest.engine import BacktestEngine

    engine = BacktestEngine(config)
    result = engine.run(data, signal_func)
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd
from loguru import logger

from quant_engine.backtest.domain import (
    CompletedTrade,
    EquityPoint,
    Fill,
    Order,
    OrderSide,
    OrderStatus,
    OrderType,
    Portfolio,
)


@dataclass
class BacktestConfig:
    """Backtest çalıştırma konfigürasyonu."""

    initial_capital: float = 100_000.0
    commission_rate: float = 0.001
    slippage_bps: int = 5
    max_position_pct: float = 0.20
    warm_up_bars: int = 0
    allow_short: bool = False
    
    # Realism eklentileri
    slippage_model: str = "fixed_bps"  # "fixed_bps", "fixed_tick"
    slippage_tick: float = 0.01  # tick bazlı model için
    volume_limit_pct: float = 0.05  # likidite: son hacmin max % kaçı
    volume_window: int = 5


@dataclass
class BacktestAssumptions:
    """Backtest varsayımları — audit trail için."""

    signal_timing: str = "bar[t].close"
    execution_timing: str = "bar[t+1].open"
    fill_policy: str = "full_fill_at_open"
    cost_model: str = "fixed_bps"
    position_sizing: str = "max_position_pct"
    pending_at_end: str = "discard"


@dataclass
class QualityWarning:
    """Kalite kontrol uyarısı."""

    code: str  # "LOW_TRADE_COUNT", "HIGH_DRAWDOWN", "OVERFIT_RISK",vb.
    severity: str  # "high", "medium", "low" (frontend renkleri için)
    message: str


@dataclass
class BacktestResult:
    """Backtest sonucu — tüm audit verisi dahil."""

    equity_curve: list[EquityPoint] = field(
        default_factory=list
    )
    orders: list[Order] = field(default_factory=list)
    fills: list[Fill] = field(default_factory=list)
    trades: list[CompletedTrade] = field(
        default_factory=list
    )
    final_equity: float = 0.0
    total_return_pct: float = 0.0
    max_drawdown_pct: float = 0.0
    total_trades: int = 0
    total_commission: float = 0.0
    total_slippage: float = 0.0
    sharpe_ratio: float = 0.0
    win_rate: float = 0.0
    quality_score: int = 100
    assumptions: BacktestAssumptions = field(
        default_factory=BacktestAssumptions
    )
    warnings: list[QualityWarning] = field(default_factory=list)
    
    # Eski list[str] formatına geriye dönük uyumluluk veya loglama için 
    # uyarı metinlerini direkt veren property
    @property
    def warning_messages(self) -> list[str]:
        return [w.message for w in self.warnings]
    has_open_position: bool = False


class BacktestEngine:
    """
    Minimal backtest motoru.

    Signal function imzası:
        def signal_func(
            data: pd.DataFrame,
            bar_index: int,
            portfolio: Portfolio,
        ) -> int:
            # +1 = al, -1 = sat, 0 = bekle
            return 0

    Invariant: cash + position_value == total_equity (her bar)
    """

    def __init__(self, config: BacktestConfig | None = None):
        self.config = config or BacktestConfig()

    def _calculate_slippage(
        self, price: float, side: OrderSide
    ) -> float:
        """Slippage hesapla (model bazlı)."""
        if self.config.slippage_model == "fixed_tick":
            if side == OrderSide.BUY:
                return price + self.config.slippage_tick
            return max(price - self.config.slippage_tick, 0.0001)

        # Varsayılan: fixed_bps
        slippage_pct = self.config.slippage_bps / 10_000
        if side == OrderSide.BUY:
            return price * (1 + slippage_pct)
        return price * (1 - slippage_pct)

    def _calculate_commission(
        self, price: float, quantity: int
    ) -> float:
        """Komisyon hesapla."""
        return price * quantity * self.config.commission_rate

    def _calculate_position_size(
        self,
        portfolio: Portfolio,
        price: float,
        prices: dict[str, float],
        max_qty_by_volume: int = -1,
    ) -> int:
        """
        Pozisyon büyüklüğü hesapla.

        max_position_pct ile sınırlandırılmış.
        Komisyon ve slippage sonrası negatif cash üretmez.
        """
        equity = portfolio.total_equity(prices)
        max_value = equity * self.config.max_position_pct

        # Komisyon ve slippage için marj bırak
        commission_margin = 1 + self.config.commission_rate
        slippage_margin = 1 + self.config.slippage_bps / 10_000
        safety_factor = commission_margin * slippage_margin

        available = min(
            portfolio.cash / safety_factor,
            max_value,
        )
        if price <= 0:
            return 0
        quantity = int(available / price)
        
        if max_qty_by_volume >= 0 and quantity > max_qty_by_volume:
            quantity = max_qty_by_volume
            
        return max(0, quantity)

    def run(
        self,
        data: pd.DataFrame,
        signal_func,
        symbol: str = "UNKNOWN",
    ) -> BacktestResult:
        """
        Backtest çalıştır.

        Args:
            data: OHLCV verisi (date, open, high, low,
                  close, volume sütunları)
            signal_func: Sinyal fonksiyonu
                (data, bar_index, portfolio) → int
            symbol: Sembol adı

        Returns:
            BacktestResult: Backtest sonucu
        """
        if data.empty or len(data) < 2:
            logger.error("Yetersiz veri!")
            return BacktestResult()

        # Sıralı veri garantile
        data = data.sort_values("date").reset_index(
            drop=True
        )
        
        if "volume" in data.columns and self.config.volume_limit_pct > 0:
            data["avg_vol"] = data["volume"].rolling(self.config.volume_window).mean()

        portfolio = Portfolio(
            initial_capital=self.config.initial_capital
        )
        result = BacktestResult()
        peak_equity = self.config.initial_capital
        pending_signal: int = 0
        pending_signal_bar: int = -1

        # Buy fill'leri trade eşleştirme için sakla
        _open_buy_fills: dict[str, Fill] = {}

        logger.info(
            f"🚀 Backtest: {symbol} | "
            f"{len(data)} bar | "
            f"₺{self.config.initial_capital:,.0f} sermaye"
        )

        for i in range(len(data)):
            bar = data.iloc[i]
            current_price = float(bar["close"])
            current_open = float(bar["open"])
            current_volume = float(bar.get("avg_vol", 0.0))
            
            max_qty_by_vol = -1
            if current_volume > 0 and self.config.volume_limit_pct > 0:
                max_qty_by_vol = int(current_volume * self.config.volume_limit_pct)
                
            prices = {symbol: current_price}
            bar_date = pd.Timestamp(bar["date"])

            # --- EXECUTION PHASE ---
            # Önceki bardan gelen sinyali bu barın
            # open'ında execute et
            if i > 0 and pending_signal != 0:
                # signal_timestamp = sinyalin üretildiği
                # barın tarihi (pending_signal_bar)
                signal_bar = data.iloc[pending_signal_bar]
                signal_date = pd.Timestamp(
                    signal_bar["date"]
                )

                fill = self._execute_signal(
                    pending_signal,
                    symbol,
                    current_open,
                    portfolio,
                    prices,
                    bar_index=i,
                    signal_bar_index=pending_signal_bar,
                    signal_date=signal_date,
                    execution_date=bar_date,
                    max_qty_by_vol=max_qty_by_vol,
                )
                if fill:
                    if max_qty_by_vol >= 0 and fill.fill_quantity >= max_qty_by_vol:
                        result.warnings.append(
                            QualityWarning(
                                code="LIQUIDITY_LIMIT",
                                severity="low",
                                message=f"[{bar_date:%Y-%m-%d}] Likidite kısıtı uygulandı. (Max Qty: {max_qty_by_vol})"
                            )
                        )
                    portfolio.process_fill(fill)
                    result.orders.append(fill.order)
                    result.fills.append(fill)

                    # Trade eşleştirme
                    if fill.order.side == OrderSide.BUY:
                        _open_buy_fills[symbol] = fill
                    elif fill.order.side == OrderSide.SELL:
                        buy_fill = _open_buy_fills.pop(
                            symbol, None
                        )
                        if buy_fill:
                            trade = CompletedTrade(
                                symbol=symbol,
                                entry_date=(
                                    buy_fill.fill_timestamp
                                ),
                                exit_date=(
                                    fill.fill_timestamp
                                ),
                                entry_price=(
                                    buy_fill.fill_price
                                ),
                                exit_price=fill.fill_price,
                                quantity=(
                                    buy_fill.fill_quantity
                                ),
                                entry_bar_index=(
                                    buy_fill.bar_index
                                ),
                                exit_bar_index=(
                                    fill.bar_index
                                ),
                                entry_commission=(
                                    buy_fill.commission
                                ),
                                exit_commission=(
                                    fill.commission
                                ),
                                entry_slippage_cost=(
                                    buy_fill.slippage_cost
                                ),
                                exit_slippage_cost=(
                                    fill.slippage_cost
                                ),
                            )
                            result.trades.append(trade)
                            result.total_trades += 1

                pending_signal = 0

            # --- SIGNAL PHASE ---
            # Warm-up kontrolü
            if i < self.config.warm_up_bars:
                signal = 0
            else:
                # bar[t].close'da sinyal üret
                signal = signal_func(data, i, portfolio)

            # Son barda pending signal kaybolur
            if i < len(data) - 1:
                pending_signal = signal
                pending_signal_bar = i
            else:
                if signal != 0:
                    result.warnings.append(
                        QualityWarning(
                            code="ORPHAN_SIGNAL",
                            severity="low",
                            message=f"Son barda sinyal ({signal}) üretildi ama execute edilemedi (sonraki bar yok)."
                        )
                    )

            # --- EQUITY TRACKING ---
            equity = portfolio.total_equity(prices)
            pos_value = portfolio.total_position_value(
                prices
            )

            # Portfolio invariant doğrula
            expected = portfolio.cash + pos_value
            if abs(equity - expected) > 0.01:
                raise RuntimeError(
                    f"Bar {i}: Portfolio invariant "
                    f"kırıldı! equity={equity:.2f} != "
                    f"cash+pos={expected:.2f}"
                )

            # Negatif cash kontrolü
            if portfolio.cash < -0.01:
                result.warnings.append(
                    QualityWarning(
                        code="NEGATIVE_CASH",
                        severity="high",
                        message=f"Bar {i}: Negatif nakit! cash={portfolio.cash:.2f}"
                    )
                )

            # Drawdown hesapla
            peak_equity = max(peak_equity, equity)
            drawdown = peak_equity - equity
            dd_pct = (
                (drawdown / peak_equity * 100)
                if peak_equity > 0
                else 0.0
            )

            result.equity_curve.append(
                EquityPoint(
                    timestamp=bar_date.to_pydatetime(),
                    bar_index=i,
                    cash=portfolio.cash,
                    position_value=pos_value,
                    total_equity=equity,
                    drawdown=drawdown,
                    drawdown_pct=dd_pct,
                )
            )

        # --- SON DURUM ---
        final_prices = {
            symbol: float(data.iloc[-1]["close"])
        }
        result.final_equity = portfolio.total_equity(
            final_prices
        )
        result.total_return_pct = (
            (
                result.final_equity
                / self.config.initial_capital
                - 1
            )
            * 100
        )
        result.max_drawdown_pct = (
            max(
                ep.drawdown_pct
                for ep in result.equity_curve
            )
            if result.equity_curve
            else 0.0
        )
        result.total_commission = portfolio.total_commission
        result.total_slippage = sum(f.slippage_cost for f in result.fills)

        # Açık pozisyon kontrolü
        position = portfolio.get_or_create_position(symbol)
        if position.is_open:
            result.has_open_position = True
            result.warnings.append(
                QualityWarning(
                    code="OPEN_POSITION",
                    severity="low",
                    message=(
                        f"Açık pozisyon kaldı: "
                        f"{position.quantity}x {symbol} @ "
                        f"avg_entry={position.avg_entry_price:.2f}"
                        f" — final equity'de piyasa değeriyle değerlendi."
                    )
                )
            )

        # Sharpe Ratio (günlük)
        if len(result.equity_curve) > 1:
            equities = [
                ep.total_equity
                for ep in result.equity_curve
            ]
            returns = (
                pd.Series(equities).pct_change().dropna()
            )
            if returns.std() > 0:
                result.sharpe_ratio = (
                    returns.mean() / returns.std()
                ) * (252**0.5)

        # Win rate — CompletedTrade'lerden hesapla
        if result.trades:
            winners = sum(
                1 for t in result.trades if t.is_winner
            )
            result.win_rate = (
                winners / len(result.trades)
            )

        self._finalize_quality(result, len(data))

        logger.success(
            f"✅ Backtest tamamlandı: "
            f"₺{result.final_equity:,.0f} "
            f"({result.total_return_pct:+.2f}%) | "
            f"Max DD: {result.max_drawdown_pct:.2f}% | "
            f"Sharpe: {result.sharpe_ratio:.2f}"
        )

        return result

    def run_intents(
        self,
        data: pd.DataFrame,
        intent_func,
        symbol: str = "UNKNOWN",
    ) -> BacktestResult:
        """
        Trade intent modeliyle backtest çalıştır.

        ``intent_func`` dönüşleri:
            BUY, SELL, SHORT, COVER, HOLD, CONFLICT

        Eski ``run`` metodu geriye uyumluluk için long-only ``+1/-1`` akışını
        korur; bu metot Sprint 12 ``strategy_spec`` ve short simülasyonu için
        kullanılır.
        """
        if data.empty or len(data) < 2:
            logger.error("Yetersiz veri!")
            return BacktestResult()

        data = data.sort_values("date").reset_index(drop=True)
        
        if "volume" in data.columns and self.config.volume_limit_pct > 0:
            data["avg_vol"] = data["volume"].rolling(self.config.volume_window).mean()

        portfolio = Portfolio(initial_capital=self.config.initial_capital)
        result = BacktestResult()
        peak_equity = self.config.initial_capital
        pending_intent = "HOLD"
        pending_signal_bar = -1
        pending_reason = ""

        open_long_fills: dict[str, Fill] = {}
        open_short_fills: dict[str, Fill] = {}

        logger.info(
            f"🚀 Intent Backtest: {symbol} | "
            f"{len(data)} bar | "
            f"₺{self.config.initial_capital:,.0f} sermaye"
        )

        for i in range(len(data)):
            bar = data.iloc[i]
            current_price = float(bar["close"])
            current_open = float(bar["open"])
            current_volume = float(bar.get("avg_vol", 0.0))
            
            max_qty_by_vol = -1
            if current_volume > 0 and self.config.volume_limit_pct > 0:
                max_qty_by_vol = int(current_volume * self.config.volume_limit_pct)
                
            prices = {symbol: current_price}
            bar_date = pd.Timestamp(bar["date"])

            if i > 0 and pending_intent != "HOLD":
                signal_bar = data.iloc[pending_signal_bar]
                signal_date = pd.Timestamp(signal_bar["date"])

                fill = self._execute_intent(
                    pending_intent,
                    symbol,
                    current_open,
                    portfolio,
                    prices,
                    bar_index=i,
                    signal_bar_index=pending_signal_bar,
                    signal_date=signal_date,
                    execution_date=bar_date,
                    reason=pending_reason,
                    max_qty_by_vol=max_qty_by_vol,
                )
                if fill:
                    if max_qty_by_vol >= 0 and fill.fill_quantity >= max_qty_by_vol:
                        result.warnings.append(
                            QualityWarning(
                                code="LIQUIDITY_LIMIT",
                                severity="low",
                                message=f"[{bar_date:%Y-%m-%d}] Likidite kısıtı uygulandı. (Max Qty: {max_qty_by_vol})"
                            )
                        )
                    portfolio.process_fill(fill)
                    result.orders.append(fill.order)
                    result.fills.append(fill)

                    if fill.order.intent == "BUY":
                        open_long_fills[symbol] = fill
                    elif fill.order.intent == "SELL":
                        buy_fill = open_long_fills.pop(symbol, None)
                        if buy_fill:
                            result.trades.append(
                                CompletedTrade(
                                    symbol=symbol,
                                    entry_date=buy_fill.fill_timestamp,
                                    exit_date=fill.fill_timestamp,
                                    entry_price=buy_fill.fill_price,
                                    exit_price=fill.fill_price,
                                    quantity=buy_fill.fill_quantity,
                                    side=OrderSide.BUY,
                                    entry_bar_index=buy_fill.bar_index,
                                    exit_bar_index=fill.bar_index,
                                    entry_commission=buy_fill.commission,
                                    exit_commission=fill.commission,
                                    entry_slippage_cost=buy_fill.slippage_cost,
                                    exit_slippage_cost=fill.slippage_cost,
                                )
                            )
                            result.total_trades += 1
                    elif fill.order.intent == "SHORT":
                        open_short_fills[symbol] = fill
                    elif fill.order.intent == "COVER":
                        short_fill = open_short_fills.pop(symbol, None)
                        if short_fill:
                            result.trades.append(
                                CompletedTrade(
                                    symbol=symbol,
                                    entry_date=short_fill.fill_timestamp,
                                    exit_date=fill.fill_timestamp,
                                    entry_price=short_fill.fill_price,
                                    exit_price=fill.fill_price,
                                    quantity=short_fill.fill_quantity,
                                    side=OrderSide.SELL,
                                    entry_bar_index=short_fill.bar_index,
                                    exit_bar_index=fill.bar_index,
                                    entry_commission=short_fill.commission,
                                    exit_commission=fill.commission,
                                    entry_slippage_cost=short_fill.slippage_cost,
                                    exit_slippage_cost=fill.slippage_cost,
                                )
                            )
                            result.total_trades += 1

                pending_intent = "HOLD"
                pending_reason = ""

            if i < self.config.warm_up_bars:
                intent = "HOLD"
            else:
                intent = self._normalize_intent(intent_func(data, i, portfolio))

            if intent == "CONFLICT":
                result.warnings.append(
                    QualityWarning(
                        code="CONFLICTING_SIGNALS",
                        severity="medium",
                        message=f"Bar {i}: Long ve short giriş sinyali aynı anda geldi; işlem reddedildi."
                    )
                )
                intent = "HOLD"

            if i < len(data) - 1:
                pending_intent = intent
                pending_signal_bar = i
                pending_reason = str(getattr(intent_func, "last_reason", ""))
            elif intent != "HOLD":
                result.warnings.append(
                    QualityWarning(
                        code="ORPHAN_SIGNAL",
                        severity="low",
                        message=f"Son barda sinyal ({intent}) üretildi ama execute edilemedi (sonraki bar yok)."
                    )
                )

            equity = portfolio.total_equity(prices)
            pos_value = portfolio.total_position_value(prices)
            expected = portfolio.cash + pos_value
            if abs(equity - expected) > 0.01:
                raise RuntimeError(
                    f"Bar {i}: Portfolio invariant kırıldı! "
                    f"equity={equity:.2f} != cash+pos={expected:.2f}"
                )

            if portfolio.cash < -0.01:
                result.warnings.append(
                    QualityWarning(
                        code="NEGATIVE_CASH",
                        severity="high",
                        message=f"Bar {i}: Negatif nakit! cash={portfolio.cash:.2f}"
                    )
                )

            peak_equity = max(peak_equity, equity)
            drawdown = peak_equity - equity
            dd_pct = (drawdown / peak_equity * 100) if peak_equity > 0 else 0.0
            result.equity_curve.append(
                EquityPoint(
                    timestamp=bar_date.to_pydatetime(),
                    bar_index=i,
                    cash=portfolio.cash,
                    position_value=pos_value,
                    total_equity=equity,
                    drawdown=drawdown,
                    drawdown_pct=dd_pct,
                )
            )

        final_prices = {symbol: float(data.iloc[-1]["close"])}
        result.final_equity = portfolio.total_equity(final_prices)
        result.total_return_pct = (
            (result.final_equity / self.config.initial_capital - 1) * 100
        )
        result.max_drawdown_pct = (
            max(ep.drawdown_pct for ep in result.equity_curve)
            if result.equity_curve
            else 0.0
        )
        result.total_commission = portfolio.total_commission
        result.total_slippage = sum(f.slippage_cost for f in result.fills)

        position = portfolio.get_or_create_position(symbol)
        if position.is_open:
            result.has_open_position = True
            side = "short" if position.quantity < 0 else "long"
            result.warnings.append(
                QualityWarning(
                    code="OPEN_POSITION",
                    severity="low",
                    message=(
                        f"Açık {side} pozisyon kaldı: {position.quantity}x {symbol} @ "
                        f"avg_entry={position.avg_entry_price:.2f} — final equity'de "
                        "piyasa değeriyle değerlendi."
                    )
                )
            )

        if len(result.equity_curve) > 1:
            equities = [ep.total_equity for ep in result.equity_curve]
            returns = pd.Series(equities).pct_change().dropna()
            if returns.std() > 0:
                result.sharpe_ratio = (returns.mean() / returns.std()) * (252**0.5)

        if result.trades:
            winners = sum(1 for t in result.trades if t.is_winner)
            result.win_rate = winners / len(result.trades)

        if self.config.allow_short and symbol.endswith(".IS"):
            result.warnings.append(
                QualityWarning(
                    code="BIST_SHORT_SIMULATION",
                    severity="medium",
                    message="BIST short işlemleri yalnızca simülasyon etiketiyle raporlanır; gerçek piyasa uygunluğu garanti edilmez."
                )
            )

        self._finalize_quality(result, len(data))

        logger.success(
            f"✅ Intent backtest tamamlandı: ₺{result.final_equity:,.0f} "
            f"({result.total_return_pct:+.2f}%) | "
            f"Max DD: {result.max_drawdown_pct:.2f}%"
        )

        return result

    def _normalize_intent(self, value) -> str:
        if isinstance(value, str):
            upper = value.upper()
            if upper in {"BUY", "SELL", "SHORT", "COVER", "HOLD", "CONFLICT"}:
                if upper == "SHORT" and not self.config.allow_short:
                    return "HOLD"
                return upper
            return "HOLD"
        try:
            ivalue = int(value)
        except (TypeError, ValueError):
            return "HOLD"
        if ivalue > 0:
            return "BUY"
        if ivalue < 0:
            return "SELL"
        return "HOLD"

    def _execute_intent(
        self,
        intent: str,
        symbol: str,
        open_price: float,
        portfolio: Portfolio,
        prices: dict[str, float],
        bar_index: int,
        signal_bar_index: int,
        signal_date: pd.Timestamp,
        execution_date: pd.Timestamp,
        reason: str = "",
        max_qty_by_vol: int = -1,
    ) -> Fill | None:
        """Trade intent'i market fill'e çevir."""
        position = portfolio.get_or_create_position(symbol)
        actual_intent = intent

        if intent == "BUY":
            if position.quantity < 0:
                side = OrderSide.BUY
                quantity = abs(position.quantity)
                # Kapanışlarda hacim kısıtına takılmayalım (opsiyonel ama genelde exitler force edilir),
                # fakat eğer istersen kapatırken de limitli yapabiliriz. Şimdilik exit'leri sınırlandırmıyoruz.
                actual_intent = "COVER"
            elif not position.is_open:
                side = OrderSide.BUY
                fill_price = self._calculate_slippage(open_price, side)
                quantity = self._calculate_position_size(
                    portfolio, fill_price, prices, max_qty_by_volume=max_qty_by_vol
                )
                if quantity <= 0:
                    return None
            else:
                return None
        elif intent == "SELL":
            if position.quantity > 0:
                side = OrderSide.SELL
                quantity = position.quantity
            else:
                return None
        elif intent == "SHORT":
            if not self.config.allow_short:
                return None
            if position.quantity > 0:
                side = OrderSide.SELL
                quantity = position.quantity
                actual_intent = "SELL"
            elif not position.is_open:
                side = OrderSide.SELL
                fill_price = self._calculate_slippage(open_price, side)
                quantity = self._calculate_position_size(
                    portfolio, fill_price, prices, max_qty_by_volume=max_qty_by_vol
                )
                if quantity <= 0:
                    return None
            else:
                return None
        elif intent == "COVER":
            if position.quantity < 0:
                side = OrderSide.BUY
                quantity = abs(position.quantity)
            else:
                return None
        else:
            return None

        fill_price = self._calculate_slippage(open_price, side)
        commission = self._calculate_commission(fill_price, quantity)
        per_unit_slippage = abs(fill_price - open_price)
        slippage_cost = per_unit_slippage * quantity

        order = Order(
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_type=OrderType.MARKET,
            signal_bar_index=signal_bar_index,
            signal_timestamp=signal_date.to_pydatetime(),
            execution_bar_index=bar_index,
            execution_timestamp=execution_date.to_pydatetime(),
            status=OrderStatus.FILLED,
            order_id=f"{symbol}_{bar_index}_{actual_intent}",
            intent=actual_intent,
        )

        fill = Fill(
            order=order,
            fill_price=fill_price,
            fill_quantity=quantity,
            commission=commission,
            slippage=per_unit_slippage,
            slippage_cost=slippage_cost,
            fill_timestamp=execution_date.to_pydatetime(),
            bar_index=bar_index,
        )

        logger.debug(
            f"📊 {execution_date:%Y-%m-%d} | {actual_intent} {quantity}x "
            f"{symbol} @ {fill_price:.2f} | Komisyon: ₺{commission:.2f} | "
            f"Sinyal: {signal_date:%Y-%m-%d} | {reason}"
        )

        return fill

    def _execute_signal(
        self,
        signal: int,
        symbol: str,
        open_price: float,
        portfolio: Portfolio,
        prices: dict[str, float],
        bar_index: int,
        signal_bar_index: int,
        signal_date: pd.Timestamp,
        execution_date: pd.Timestamp,
        max_qty_by_vol: int = -1,
    ) -> Fill | None:
        """Sinyali execute et."""
        position = portfolio.get_or_create_position(symbol)

        if signal > 0 and not position.is_open:
            # AL sinyali — pozisyon yok
            side = OrderSide.BUY
            fill_price = self._calculate_slippage(
                open_price, side
            )
            quantity = self._calculate_position_size(
                portfolio, fill_price, prices, max_qty_by_volume=max_qty_by_vol
            )
            if quantity <= 0:
                return None

        elif signal < 0 and position.is_open:
            # SAT sinyali — pozisyon var
            side = OrderSide.SELL
            fill_price = self._calculate_slippage(
                open_price, side
            )
            quantity = position.quantity

        else:
            return None

        commission = self._calculate_commission(
            fill_price, quantity
        )

        # Slippage maliyet etkisi = per-unit slippage * adet
        per_unit_slippage = abs(fill_price - open_price)
        slippage_cost = per_unit_slippage * quantity

        order = Order(
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_type=OrderType.MARKET,
            signal_bar_index=signal_bar_index,
            signal_timestamp=(
                signal_date.to_pydatetime()
            ),
            execution_bar_index=bar_index,
            execution_timestamp=(
                execution_date.to_pydatetime()
            ),
            status=OrderStatus.FILLED,
            order_id=(
                f"{symbol}_{bar_index}_{side.value}"
            ),
        )

        fill = Fill(
            order=order,
            fill_price=fill_price,
            fill_quantity=quantity,
            commission=commission,
            slippage=per_unit_slippage,
            slippage_cost=slippage_cost,
            fill_timestamp=(
                execution_date.to_pydatetime()
            ),
            bar_index=bar_index,
        )

        logger.debug(
            f"📊 {execution_date:%Y-%m-%d} | "
            f"{side.value.upper()} {quantity}x "
            f"{symbol} @ {fill_price:.2f} | "
            f"Komisyon: ₺{commission:.2f} | "
            f"Sinyal: {signal_date:%Y-%m-%d}"
        )

        return fill


    def _finalize_quality(self, result: BacktestResult, bar_count: int) -> None:
        """Sonuçları analiz edip kalite skorunu ve uyarıları hesaplar."""
        score = 100

        # Bar sayısı kontrolü
        if bar_count < 250:
            score -= 30
            result.warnings.append(
                QualityWarning(
                    code="LOW_DATA_POINTS",
                    severity="high",
                    message=f"Çok az veri {bar_count} bar ile test edildi (Önerilen > 250)."
                )
            )

        # İşlem maliyeti varsayımları
        if self.config.commission_rate == 0 and self.config.slippage_bps == 0:
            score -= 40
            result.warnings.append(
                QualityWarning(
                    code="ZERO_COST_ASSUMPTION",
                    severity="high",
                    message="Sıfır işlem maliyeti ve slippage ile test edildi (Gerçek dışı)."
                )
            )
        elif result.total_trades > 0:
            gross_profit = sum(max(0, t.exit_price - t.entry_price) * t.quantity for t in result.trades if t.exit_price > t.entry_price)
            costs = result.total_commission + result.total_slippage
            if gross_profit > 0 and (costs / gross_profit) > 0.5:
                score -= 20
                result.warnings.append(
                    QualityWarning(
                        code="HIGH_FRICTION",
                        severity="medium",
                        message=f"Brüt karın yarısından fazlası (%{(costs/gross_profit)*100:.1f}) komisyon/slippage'a gidiyor."
                    )
                )

        # İşlem Sayısı kontrolü
        if result.total_trades < 10:
            score -= 50
            result.warnings.append(
                QualityWarning(
                    code="VERY_LOW_TRADE_COUNT",
                    severity="high",
                    message=f"İşlem sayısı çok düşük ({result.total_trades}). Sonuçlar şans eseri olabilir."
                )
            )
        elif result.total_trades < 30:
            score -= 20
            result.warnings.append(
                QualityWarning(
                    code="LOW_TRADE_COUNT",
                    severity="medium",
                    message=f"İşlem sayısı sınırda ({result.total_trades}). İstatistiksel olarak zayıf."
                )
            )
        elif result.total_trades > bar_count * 0.1:
             score -= 10
             result.warnings.append(
                QualityWarning(
                    code="OVERTRADING_RISK",
                    severity="medium",
                    message="Sinyal frekansı çok yüksek (Overtrading)."
                )
            )

        # Drawdown kontrolü
        if result.max_drawdown_pct > 60:
            score -= 50
            result.warnings.append(
                QualityWarning(
                    code="EXTREME_DRAWDOWN",
                    severity="high",
                    message=f"Aşırı yüksek Max Drawdown (%{result.max_drawdown_pct:.1f}). Hesap batma riski."
                )
            )
        elif result.max_drawdown_pct > 40:
            score -= 30
            result.warnings.append(
                QualityWarning(
                    code="HIGH_DRAWDOWN",
                    severity="high",
                    message=f"Yüksek drawdown (%{result.max_drawdown_pct:.1f}). Beklentinin üzerinde risk."
                )
            )
        elif result.max_drawdown_pct > 30:
            score -= 15
            result.warnings.append(
                QualityWarning(
                    code="MODERATE_DRAWDOWN",
                    severity="medium",
                    message=f"Orta karar drawdown (%{result.max_drawdown_pct:.1f})."
                )
            )

        # Win rate kontrolü
        if result.total_trades >= 10:
            if result.win_rate > 0.85:
                score -= 20
                result.warnings.append(
                    QualityWarning(
                        code="OVERFIT_SUSPICION",
                        severity="medium",
                        message=f"Çok yüksek win rate (%{result.win_rate*100:.1f}). Overfitting veya lookahead bias şüphesi."
                    )
                )
            elif result.win_rate < 0.25:
                score -= 20
                result.warnings.append(
                    QualityWarning(
                        code="LOW_WIN_RATE",
                        severity="medium",
                        message=f"Düşük win rate (%{result.win_rate*100:.1f}). Zarar kesmek için çok fazla stop tetiklenmiş olabilir."
                    )
                )

        result.quality_score = max(0, min(100, int(score)))


def buy_and_hold_signal(
    data: pd.DataFrame,
    bar_index: int,
    portfolio: Portfolio,
) -> int:
    """
    Buy & Hold baseline stratejisi.

    İlk barda al, son bara kadar tut.
    """
    position = portfolio.get_or_create_position(
        data.iloc[bar_index].get("symbol", "UNKNOWN")
    )
    if bar_index == 0 and not position.is_open:
        return 1  # AL
    return 0  # BEKLE
