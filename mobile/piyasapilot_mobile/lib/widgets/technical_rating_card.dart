/// Teknik Analiz Derecelendirme Kartı
///
/// AL / SAT / NÖTR özetini büyük renkli bir kartla gösterir.
/// TechnicalSummary verilerindeki overallRating, oscillatorRating,
/// movingAverageRating alanları ile kullanılır.
library;

import 'package:flutter/material.dart';

import '../models/models.dart';

class TechnicalRatingCard extends StatelessWidget {
  /// TechnicalRating enum değeri.
  final TechnicalRating rating;

  /// Kartın üstüne yazılacak başlık (örn. "Genel", "Osilatörler").
  final String label;

  const TechnicalRatingCard({
    super.key,
    required this.rating,
    required this.label,
  });

  @override
  Widget build(BuildContext context) {
    final (color, icon, text) = _resolve();
    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: BorderSide(color: color.withOpacity(0.4)),
      ),
      color: color.withOpacity(0.06),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          Text(
            label,
            style: const TextStyle(fontSize: 11, color: Colors.grey, letterSpacing: 0.8),
          ),
          const SizedBox(height: 6),
          Icon(icon, color: color, size: 22),
          const SizedBox(height: 4),
          Text(
            text,
            style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
        ]),
      ),
    );
  }

  (Color, IconData, String) _resolve() => switch (rating) {
        TechnicalRating.strongBuy  => (Colors.green[700]!,   Icons.trending_up,   'GÜÇLÜ AL'),
        TechnicalRating.buy        => (Colors.green,          Icons.arrow_upward,  'AL'),
        TechnicalRating.strongSell => (Colors.red[700]!,      Icons.trending_down, 'GÜÇLÜ SAT'),
        TechnicalRating.sell       => (Colors.red,            Icons.arrow_downward,'SAT'),
        _                          => (Colors.grey,           Icons.remove,        'NÖTR'),
      };
}
