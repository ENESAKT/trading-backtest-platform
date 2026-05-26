/// Paper Trading modelleri — emir, pozisyon ve portföy özeti.
///
/// Backend PaperOrder / PaperPosition / PaperPortfolioSummary ile
/// birebir alan uyumu sağlar (Bölüm 18.14).
library;

enum PaperOrderSide { buy, sell, short, cover;
  static PaperOrderSide fromJson(String? v) => switch (v) {
    'buy' => buy, 'sell' => sell, 'short' => short, 'cover' => cover,
    _ => buy,
  };
}

enum PaperOrderType { market, limit, stop;
  static PaperOrderType fromJson(String? v) => switch (v) {
    'market' => market, 'limit' => limit, 'stop' => stop, _ => market,
  };
}

enum PaperOrderStatus { pending, filled, cancelled, rejected;
  static PaperOrderStatus fromJson(String? v) => switch (v) {
    'pending' => pending, 'filled' => filled,
    'cancelled' => cancelled, 'rejected' => rejected, _ => filled,
  };
}

class PaperOrder {
  final int id;
  final String strategyId;
  final String symbol;
  final PaperOrderSide side;
  final PaperOrderType orderType;
  final PaperOrderStatus status;
  final double quantity;
  final double? requestedPrice;
  final double? filledPrice;
  final DateTime createdAt;
  final DateTime? filledAt;
  final String reason;

  const PaperOrder({
    required this.id,
    required this.strategyId,
    required this.symbol,
    required this.side,
    this.orderType = PaperOrderType.market,
    this.status = PaperOrderStatus.filled,
    required this.quantity,
    this.requestedPrice,
    this.filledPrice,
    required this.createdAt,
    this.filledAt,
    this.reason = '',
  });

  factory PaperOrder.fromJson(Map<String, dynamic> j) => PaperOrder(
        id:             j['id'] as int,
        strategyId:     j['strategy_id'] as String,
        symbol:         j['symbol'] as String,
        side:           PaperOrderSide.fromJson(j['side'] as String?),
        orderType:      PaperOrderType.fromJson(j['order_type'] as String?),
        status:         PaperOrderStatus.fromJson(j['status'] as String?),
        quantity:       (j['quantity'] as num).toDouble(),
        requestedPrice: (j['requested_price'] as num?)?.toDouble(),
        filledPrice:    (j['filled_price']    as num?)?.toDouble(),
        createdAt:      DateTime.parse(j['created_at'] as String),
        filledAt:       j['filled_at'] != null
            ? DateTime.tryParse(j['filled_at'] as String)
            : null,
        reason: j['reason'] as String? ?? '',
      );
}

class PaperPosition {
  final String strategyId;
  final String symbol;
  final String side; // 'long' | 'short'
  final double quantity;
  final double entryPrice;
  final double? currentPrice;

  final double? unrealizedPnl;
  final double? unrealizedPnlPct;
  final double realizedPnl;

  final DateTime openedAt;
  final int tradeId;

  const PaperPosition({
    required this.strategyId,
    required this.symbol,
    this.side = 'long',
    required this.quantity,
    required this.entryPrice,
    this.currentPrice,
    this.unrealizedPnl,
    this.unrealizedPnlPct,
    this.realizedPnl = 0.0,
    required this.openedAt,
    required this.tradeId,
  });

  factory PaperPosition.fromJson(Map<String, dynamic> j) => PaperPosition(
        strategyId:       j['strategy_id'] as String,
        symbol:           j['symbol'] as String,
        side:             j['side'] as String? ?? 'long',
        quantity:         (j['quantity']    as num).toDouble(),
        entryPrice:       (j['entry_price'] as num).toDouble(),
        currentPrice:     (j['current_price']      as num?)?.toDouble(),
        unrealizedPnl:    (j['unrealized_pnl']     as num?)?.toDouble(),
        unrealizedPnlPct: (j['unrealized_pnl_pct'] as num?)?.toDouble(),
        realizedPnl:      (j['realized_pnl']       as num?)?.toDouble() ?? 0.0,
        openedAt: DateTime.parse(j['opened_at'] as String),
        tradeId:  j['trade_id'] as int,
      );
}

class PaperPortfolioSummary {
  final String strategyId;
  final double initialCapital;
  final double cash;
  final double positionsValue;
  final double totalEquity;
  final double unrealizedPnl;
  final double realizedPnl;
  final double dailyPnl;
  final double dailyPnlPct;
  final bool isHalted;

  final List<PaperPosition> positions;
  final List<PaperOrder> openOrders;
  final DateTime? asOf;

  const PaperPortfolioSummary({
    required this.strategyId,
    required this.initialCapital,
    required this.cash,
    required this.positionsValue,
    required this.totalEquity,
    required this.unrealizedPnl,
    required this.realizedPnl,
    required this.dailyPnl,
    required this.dailyPnlPct,
    required this.isHalted,
    this.positions = const [],
    this.openOrders = const [],
    this.asOf,
  });

  factory PaperPortfolioSummary.fromJson(Map<String, dynamic> j) =>
      PaperPortfolioSummary(
        strategyId:      j['strategy_id']     as String,
        initialCapital:  (j['initial_capital'] as num).toDouble(),
        cash:            (j['cash']            as num).toDouble(),
        positionsValue:  (j['positions_value'] as num).toDouble(),
        totalEquity:     (j['total_equity']    as num).toDouble(),
        unrealizedPnl:   (j['unrealized_pnl']  as num).toDouble(),
        realizedPnl:     (j['realized_pnl']    as num).toDouble(),
        dailyPnl:        (j['daily_pnl']       as num).toDouble(),
        dailyPnlPct:     (j['daily_pnl_pct']   as num).toDouble(),
        isHalted:        j['is_halted'] as bool? ?? false,
        positions: (j['positions'] as List<dynamic>?)
                ?.map((e) => PaperPosition.fromJson(e as Map<String, dynamic>))
                .toList() ??
            [],
        openOrders: (j['open_orders'] as List<dynamic>?)
                ?.map((e) => PaperOrder.fromJson(e as Map<String, dynamic>))
                .toList() ??
            [],
        asOf: j['as_of'] != null ? DateTime.tryParse(j['as_of'] as String) : null,
      );
}
