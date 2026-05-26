/// Veri Kalitesi Rozeti
///
/// DataTruth nesnesinin kalite durumunu küçük, renkli bir rozet olarak gösterir.
/// Gerçek olmayan veya gecikmeli verilerde uyarı ikonu eklenir.
library;

import 'package:flutter/material.dart';

import '../models/models.dart';

class DataQualityBadge extends StatelessWidget {
  final DataTruth? truth;

  const DataQualityBadge({super.key, required this.truth});

  @override
  Widget build(BuildContext context) {
    if (truth == null) {
      return const SizedBox.shrink();
    }
    final (color, icon, label) = _resolve();
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: color.withOpacity(0.12),
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: color.withOpacity(0.4), width: 0.8),
      ),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        Icon(icon, size: 10, color: color),
        const SizedBox(width: 3),
        Text(
          label,
          style: TextStyle(
            fontSize: 10,
            color: color,
            fontWeight: FontWeight.bold,
            letterSpacing: 0.4,
          ),
        ),
      ]),
    );
  }

  (Color, IconData, String) _resolve() {
    final t = truth!;
    if (!t.isReal) {
      return (Colors.deepOrange, Icons.warning_amber, 'MOCK');
    }
    if (t.isDelayed && t.delayMinutes > 0) {
      return (Colors.orange, Icons.access_time, '${t.delayMinutes}dk');
    }
    return switch (t.qualityStatus) {
      DataQualityStatus.ok      => (Colors.green,  Icons.verified,       'CANLI'),
      DataQualityStatus.warning => (Colors.orange, Icons.info_outline,   'UYARI'),
      DataQualityStatus.blocked => (Colors.red,    Icons.error_outline,  'ZAYIF'),
      DataQualityStatus.unknown => (Colors.grey,   Icons.help_outline,   '?'),
    };
  }
}
