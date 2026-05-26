/// Fiyat Değişim Chip'i
///
/// Yüzde değişimi yeşil/kırmızı arka planla gösterir.
/// null veya sıfır değeri için nötr gri gösterim kullanılır.
library;

import 'package:flutter/material.dart';

class PriceChangeChip extends StatelessWidget {
  /// Günlük değişim yüzdesi (örn. 2.5 = %+2.5, -1.3 = %-1.3).
  /// Null ise "—" gösterilir.
  final double? changePct;

  const PriceChangeChip({super.key, this.changePct});

  @override
  Widget build(BuildContext context) {
    if (changePct == null) {
      return _chip(Colors.grey, '—');
    }
    final pct = changePct!;
    if (pct > 0) return _chip(Colors.green, '+%${pct.toStringAsFixed(2)}');
    if (pct < 0) return _chip(Colors.red,   '-%${pct.abs().toStringAsFixed(2)}');
    return _chip(Colors.grey, '%0.00');
  }

  Widget _chip(Color color, String text) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: color.withOpacity(0.12),
        borderRadius: BorderRadius.circular(4),
      ),
      child: Text(
        text,
        style: TextStyle(
          fontSize: 12,
          color: color,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }
}
