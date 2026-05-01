"""Güvenli ``strategy_spec`` formül dili.

Bu modül kullanıcı tarafından yazılan strateji formüllerini Python kodu
çalıştırmadan, küçük bir allowlist grameriyle değerlendirir. Çıktı pandas
serileri olduğu için aynı şema hem görsel kurucudan hem formül editöründen
beslenebilir.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

import numpy as np
import pandas as pd

from quant_engine.strategy.indicators import atr, bollinger_bands, ema, macd, rsi, sma

RuleName = Literal["long_entry", "long_exit", "short_entry", "short_exit"]
Intent = Literal["BUY", "SELL", "SHORT", "COVER", "HOLD", "CONFLICT"]

RULE_NAMES: tuple[RuleName, ...] = (
    "long_entry",
    "long_exit",
    "short_entry",
    "short_exit",
)


@dataclass(frozen=True)
class FormulaError(Exception):
    """Kullanıcıya gösterilebilir formül hatası."""

    message: str
    column: int = 1

    def __str__(self) -> str:
        return f"{self.message} (kolon {self.column})"


@dataclass(frozen=True)
class Token:
    kind: str
    value: str
    column: int


@dataclass(frozen=True)
class NumberNode:
    value: float


@dataclass(frozen=True)
class NameNode:
    value: str


@dataclass(frozen=True)
class CallNode:
    name: str
    args: tuple["Node", ...]


@dataclass(frozen=True)
class BinaryNode:
    op: str
    left: "Node"
    right: "Node"


Node = NumberNode | NameNode | CallNode | BinaryNode

FIELDS = {"O", "H", "L", "C", "V", "HL2", "HLC3"}
FUNCTIONS = {
    "SMA",
    "EMA",
    "RSI",
    "MACD_LINE",
    "MACD_SIGNAL",
    "MACD_HIST",
    "BB_UPPER",
    "BB_MID",
    "BB_LOWER",
    "ATR",
    "VWAP",
    "HIGHEST",
    "LOWEST",
    "CROSS_UP",
    "CROSS_DOWN",
    "BARS_SINCE",
}
LOGICAL = {"AND", "OR"}
COMPARE = {">", "<", ">=", "<=", "=="}


def normalize_strategy_spec(spec: dict[str, Any] | None) -> dict[str, Any]:
    """API'den gelen spec'i tek biçime indir."""
    if not spec:
        return {"name": "Kural Stratejisi", "rules": {}, "risk": {}}

    rules = spec.get("rules") if isinstance(spec.get("rules"), dict) else {}
    normalized_rules = dict(rules)
    for name in RULE_NAMES:
        if name in spec and name not in normalized_rules:
            normalized_rules[name] = spec[name]

    risk = spec.get("risk") if isinstance(spec.get("risk"), dict) else {}
    normalized_risk = dict(risk)
    for key in ("stop_loss_pct", "take_profit_pct", "trailing_stop_pct"):
        if key in spec and key not in normalized_risk:
            normalized_risk[key] = spec[key]

    return {
        "name": str(spec.get("name") or spec.get("label") or "Kural Stratejisi"),
        "note": str(spec.get("note") or ""),
        "rules": {
            name: str(normalized_rules.get(name) or "").strip()
            for name in RULE_NAMES
        },
        "risk": normalized_risk,
    }


def validate_strategy_spec(spec: dict[str, Any] | None) -> dict[str, Any]:
    """Formülleri parse ederek güvenli/çalışabilir olduklarını doğrula."""
    normalized = normalize_strategy_spec(spec)
    rules = normalized["rules"]
    if not any(rules.values()):
        raise FormulaError("En az bir strateji kuralı yazılmalı", 1)
    for name, formula in rules.items():
        if formula:
            parse_formula(formula)
    return normalized


def parse_formula(source: str) -> Node:
    """Formülü AST'ye çevir."""
    tokens = _tokenize(source)
    parser = _Parser(tokens)
    node = parser.parse()
    return node


def evaluate_formula(source: str, data: pd.DataFrame) -> pd.Series:
    """Tek bir formülü tüm barlar için değerlendir."""
    node = parse_formula(source)
    env = _field_env(data)
    value = _eval_node(node, env, len(data))
    if not isinstance(value, pd.Series):
        return pd.Series([bool(value)] * len(data), index=data.index)
    return value


def evaluate_strategy_rules(spec: dict[str, Any], data: pd.DataFrame) -> dict[RuleName, pd.Series]:
    """Spec içindeki tüm dolu kuralları boolean seri olarak üret."""
    normalized = validate_strategy_spec(spec)
    out: dict[RuleName, pd.Series] = {}
    for name in RULE_NAMES:
        formula = normalized["rules"].get(name, "")
        if not formula:
            out[name] = pd.Series([False] * len(data), index=data.index)
            continue
        series = evaluate_formula(formula, data)
        out[name] = _as_bool_series(series, len(data), data.index)
    return out


class StrategySpecSignal:
    """``BacktestEngine.run_intents`` için stateful sinyal fonksiyonu."""

    def __init__(
        self,
        spec: dict[str, Any],
        data: pd.DataFrame,
        *,
        allow_short: bool = False,
    ) -> None:
        self.spec = validate_strategy_spec(spec)
        self.rules = evaluate_strategy_rules(self.spec, data)
        self.allow_short = allow_short
        risk = self.spec.get("risk", {})
        self.stop_loss_pct = _pct(risk.get("stop_loss_pct"))
        self.take_profit_pct = _pct(risk.get("take_profit_pct"))
        self.trailing_stop_pct = _pct(risk.get("trailing_stop_pct"))
        self._best_price: float | None = None
        self.last_reason = ""

    def __call__(self, data: pd.DataFrame, bar_index: int, portfolio: Any) -> Intent:
        symbol = str(data.iloc[bar_index].get("symbol", "UNKNOWN"))
        close = float(data.iloc[bar_index]["close"])
        position = portfolio.get_or_create_position(symbol)

        risk_intent = self._risk_intent(position.quantity, position.avg_entry_price, close)
        if risk_intent != "HOLD":
            self.last_reason = "risk"
            return risk_intent

        long_entry = bool(self.rules["long_entry"].iloc[bar_index])
        long_exit = bool(self.rules["long_exit"].iloc[bar_index])
        short_entry = bool(self.rules["short_entry"].iloc[bar_index])
        short_exit = bool(self.rules["short_exit"].iloc[bar_index])

        if position.quantity > 0:
            if long_exit or short_entry:
                self.last_reason = "long_exit" if long_exit else "short_entry"
                return "SELL"
            return "HOLD"

        if position.quantity < 0:
            if short_exit or long_entry:
                self.last_reason = "short_exit" if short_exit else "long_entry"
                return "COVER"
            return "HOLD"

        self._best_price = None
        if long_entry and short_entry and self.allow_short:
            self.last_reason = "long_entry+short_entry"
            return "CONFLICT"
        if long_entry:
            self.last_reason = "long_entry"
            return "BUY"
        if short_entry and self.allow_short:
            self.last_reason = "short_entry"
            return "SHORT"
        return "HOLD"

    def _risk_intent(self, quantity: int, entry: float, close: float) -> Intent:
        if quantity == 0 or entry <= 0:
            self._best_price = None
            return "HOLD"

        if quantity > 0:
            self._best_price = max(close, self._best_price or close)
            if self.stop_loss_pct and close <= entry * (1 - self.stop_loss_pct):
                return "SELL"
            if self.take_profit_pct and close >= entry * (1 + self.take_profit_pct):
                return "SELL"
            if self.trailing_stop_pct and close <= self._best_price * (1 - self.trailing_stop_pct):
                return "SELL"
            return "HOLD"

        self._best_price = min(close, self._best_price or close)
        if self.stop_loss_pct and close >= entry * (1 + self.stop_loss_pct):
            return "COVER"
        if self.take_profit_pct and close <= entry * (1 - self.take_profit_pct):
            return "COVER"
        if self.trailing_stop_pct and close >= self._best_price * (1 + self.trailing_stop_pct):
            return "COVER"
        return "HOLD"


def _pct(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    out = float(value)
    if out > 1:
        out = out / 100.0
    return max(0.0, out)


def _tokenize(source: str) -> list[Token]:
    tokens: list[Token] = []
    i = 0
    while i < len(source):
        ch = source[i]
        col = i + 1
        if ch.isspace():
            i += 1
            continue
        if ch.isdigit() or ch == ".":
            start = i
            dot_count = 0
            while i < len(source) and (source[i].isdigit() or source[i] == "."):
                if source[i] == ".":
                    dot_count += 1
                i += 1
            value = source[start:i]
            if dot_count > 1 or value == ".":
                raise FormulaError("Geçersiz sayı", col)
            tokens.append(Token("NUMBER", value, col))
            continue
        if ch.isalpha() or ch == "_":
            start = i
            while i < len(source) and (source[i].isalnum() or source[i] == "_"):
                i += 1
            tokens.append(Token("NAME", source[start:i].upper(), col))
            continue
        two = source[i : i + 2]
        if two in {">=", "<=", "=="}:
            tokens.append(Token("OP", two, col))
            i += 2
            continue
        if ch in "><(),":
            kind = {"(": "LPAREN", ")": "RPAREN", ",": "COMMA"}.get(ch, "OP")
            tokens.append(Token(kind, ch, col))
            i += 1
            continue
        raise FormulaError("İzin verilmeyen karakter", col)
    tokens.append(Token("EOF", "", len(source) + 1))
    return tokens


class _Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.pos = 0

    @property
    def current(self) -> Token:
        return self.tokens[self.pos]

    def parse(self) -> Node:
        if self.current.kind == "EOF":
            raise FormulaError("Boş formül", self.current.column)
        node = self._or()
        if self.current.kind != "EOF":
            raise FormulaError("Beklenmeyen ifade", self.current.column)
        return node

    def _or(self) -> Node:
        node = self._and()
        while self._match_name("OR"):
            node = BinaryNode("OR", node, self._and())
        return node

    def _and(self) -> Node:
        node = self._compare()
        while self._match_name("AND"):
            node = BinaryNode("AND", node, self._compare())
        return node

    def _compare(self) -> Node:
        node = self._primary()
        if self.current.kind == "OP" and self.current.value in COMPARE:
            op = self.current.value
            self.pos += 1
            node = BinaryNode(op, node, self._primary())
        return node

    def _primary(self) -> Node:
        tok = self.current
        if tok.kind == "NUMBER":
            self.pos += 1
            return NumberNode(float(tok.value))
        if tok.kind == "NAME":
            self.pos += 1
            name = tok.value
            if name in LOGICAL:
                raise FormulaError(f"{name} operatörü burada kullanılamaz", tok.column)
            if self.current.kind == "LPAREN":
                if name not in FUNCTIONS:
                    raise FormulaError(f"Bilinmeyen fonksiyon: {name}", tok.column)
                return self._call(name, tok.column)
            if name not in FIELDS:
                raise FormulaError(f"Bilinmeyen alan: {name}", tok.column)
            return NameNode(name)
        if tok.kind == "LPAREN":
            self.pos += 1
            node = self._or()
            self._expect("RPAREN", "Eksik kapama parantezi")
            return node
        raise FormulaError("Beklenen alan, sayı veya fonksiyon", tok.column)

    def _call(self, name: str, column: int) -> Node:
        self._expect("LPAREN", "Eksik açma parantezi")
        args: list[Node] = []
        if self.current.kind != "RPAREN":
            while True:
                args.append(self._or())
                if self.current.kind != "COMMA":
                    break
                self.pos += 1
        self._expect("RPAREN", "Eksik kapama parantezi")
        _validate_arity(name, len(args), column)
        return CallNode(name, tuple(args))

    def _match_name(self, name: str) -> bool:
        if self.current.kind == "NAME" and self.current.value == name:
            self.pos += 1
            return True
        return False

    def _expect(self, kind: str, message: str) -> None:
        if self.current.kind != kind:
            raise FormulaError(message, self.current.column)
        self.pos += 1


def _validate_arity(name: str, n: int, column: int) -> None:
    arity = {
        "SMA": 2,
        "EMA": 2,
        "RSI": 2,
        "MACD_LINE": 4,
        "MACD_SIGNAL": 4,
        "MACD_HIST": 4,
        "BB_UPPER": 3,
        "BB_MID": 3,
        "BB_LOWER": 3,
        "ATR": 1,
        "VWAP": 0,
        "HIGHEST": 2,
        "LOWEST": 2,
        "CROSS_UP": 2,
        "CROSS_DOWN": 2,
        "BARS_SINCE": 1,
    }
    expected = arity[name]
    if n != expected:
        raise FormulaError(f"{name} {expected} parametre bekler, {n} verildi", column)


def _field_env(data: pd.DataFrame) -> dict[str, pd.Series]:
    close = _series(data, "close")
    high = _series(data, "high")
    low = _series(data, "low")
    volume = _series(data, "volume")
    return {
        "O": _series(data, "open"),
        "H": high,
        "L": low,
        "C": close,
        "V": volume,
        "HL2": (high + low) / 2,
        "HLC3": (high + low + close) / 3,
    }


def _series(data: pd.DataFrame, name: str) -> pd.Series:
    return pd.to_numeric(data[name], errors="coerce")


def _eval_node(node: Node, env: dict[str, pd.Series], length: int) -> pd.Series | float:
    if isinstance(node, NumberNode):
        return node.value
    if isinstance(node, NameNode):
        return env[node.value]
    if isinstance(node, BinaryNode):
        left = _eval_node(node.left, env, length)
        right = _eval_node(node.right, env, length)
        return _eval_binary(node.op, left, right, length)
    if isinstance(node, CallNode):
        args = [_eval_node(arg, env, length) for arg in node.args]
        return _eval_call(node.name, args, env, length)
    raise FormulaError("Geçersiz ifade", 1)


def _eval_binary(
    op: str,
    left: pd.Series | float,
    right: pd.Series | float,
    length: int,
) -> pd.Series:
    l_series = _ensure_series(left, length)
    r_series = _ensure_series(right, length)
    if op == "AND":
        return _as_bool_series(l_series, length, l_series.index) & _as_bool_series(
            r_series, length, r_series.index
        )
    if op == "OR":
        return _as_bool_series(l_series, length, l_series.index) | _as_bool_series(
            r_series, length, r_series.index
        )
    if op == ">":
        return l_series > r_series
    if op == "<":
        return l_series < r_series
    if op == ">=":
        return l_series >= r_series
    if op == "<=":
        return l_series <= r_series
    if op == "==":
        return l_series == r_series
    raise FormulaError(f"Bilinmeyen operatör: {op}", 1)


def _eval_call(
    name: str,
    args: list[pd.Series | float],
    env: dict[str, pd.Series],
    length: int,
) -> pd.Series:
    if name == "SMA":
        return sma(_ensure_series(args[0], length), _period(args[1]))
    if name == "EMA":
        return ema(_ensure_series(args[0], length), _period(args[1]))
    if name == "RSI":
        return rsi(_ensure_series(args[0], length), _period(args[1]))
    if name.startswith("MACD_"):
        line, signal, hist = macd(
            _ensure_series(args[0], length),
            _period(args[1]),
            _period(args[2]),
            _period(args[3]),
        )
        return {"MACD_LINE": line, "MACD_SIGNAL": signal, "MACD_HIST": hist}[name]
    if name.startswith("BB_"):
        upper, mid, lower = bollinger_bands(
            _ensure_series(args[0], length),
            _period(args[1]),
            float(args[2]),
        )
        return {"BB_UPPER": upper, "BB_MID": mid, "BB_LOWER": lower}[name]
    if name == "ATR":
        return atr(env["H"], env["L"], env["C"], _period(args[0]))
    if name == "VWAP":
        typical = env["HLC3"]
        volume = env["V"].replace(0, np.nan)
        return (typical * volume).cumsum() / volume.cumsum()
    if name == "HIGHEST":
        period = _period(args[1])
        return _ensure_series(args[0], length).rolling(
            period, min_periods=period
        ).max()
    if name == "LOWEST":
        period = _period(args[1])
        return _ensure_series(args[0], length).rolling(
            period, min_periods=period
        ).min()
    if name == "CROSS_UP":
        left = _ensure_series(args[0], length)
        right = _ensure_series(args[1], length)
        return (left.shift(1) <= right.shift(1)) & (left > right)
    if name == "CROSS_DOWN":
        left = _ensure_series(args[0], length)
        right = _ensure_series(args[1], length)
        return (left.shift(1) >= right.shift(1)) & (left < right)
    if name == "BARS_SINCE":
        cond = _as_bool_series(_ensure_series(args[0], length), length, env["C"].index)
        count = []
        last_seen: int | None = None
        for i, flag in enumerate(cond.fillna(False)):
            if bool(flag):
                last_seen = i
                count.append(0)
            else:
                count.append(np.nan if last_seen is None else i - last_seen)
        return pd.Series(count, index=env["C"].index)
    raise FormulaError(f"Bilinmeyen fonksiyon: {name}", 1)


def _ensure_series(value: pd.Series | float, length: int) -> pd.Series:
    if isinstance(value, pd.Series):
        return value
    return pd.Series([float(value)] * length)


def _as_bool_series(value: pd.Series | float, length: int, index: Any) -> pd.Series:
    if not isinstance(value, pd.Series):
        return pd.Series([bool(value)] * length, index=index)
    return value.fillna(False).astype(bool)


def _period(value: pd.Series | float) -> int:
    if isinstance(value, pd.Series):
        raise FormulaError("Periyot parametresi sabit sayı olmalı", 1)
    period = int(value)
    if period < 1:
        raise FormulaError("Periyot 1 veya daha büyük olmalı", 1)
    return period
