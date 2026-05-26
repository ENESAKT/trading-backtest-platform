/// Fiyat Alarmı Ekranı
///
/// Kullanıcı sembol + hedef fiyat girer. Alarm listesi yerel olarak tutulur.
/// Push notification entegrasyonu (Firebase) yayın aşamasında yapılır;
/// bu ekran UI katmanını tamamlar.
library;

import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';

class PriceAlert {
  final String symbol;
  final double targetPrice;
  final String direction; // 'above' | 'below'
  final DateTime createdAt;

  PriceAlert({
    required this.symbol,
    required this.targetPrice,
    required this.direction,
    required this.createdAt,
  });

  Map<String, dynamic> toJson() => {
    'symbol':      symbol,
    'targetPrice': targetPrice,
    'direction':   direction,
    'createdAt':   createdAt.toIso8601String(),
  };

  factory PriceAlert.fromJson(Map<String, dynamic> j) => PriceAlert(
    symbol:      j['symbol']      as String,
    targetPrice: (j['targetPrice'] as num).toDouble(),
    direction:   j['direction']   as String,
    createdAt:   DateTime.parse(j['createdAt'] as String),
  );
}

class PriceAlertScreen extends StatefulWidget {
  const PriceAlertScreen({super.key});

  @override
  State<PriceAlertScreen> createState() => _PriceAlertScreenState();
}

class _PriceAlertScreenState extends State<PriceAlertScreen> {
  List<PriceAlert> _alerts = [];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final prefs = await SharedPreferences.getInstance();
    final raw   = prefs.getStringList('price_alerts') ?? [];
    setState(() {
      _alerts = raw
          .map((s) => PriceAlert.fromJson(jsonDecode(s) as Map<String, dynamic>))
          .toList();
    });
  }

  Future<void> _save() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setStringList(
      'price_alerts',
      _alerts.map((a) => jsonEncode(a.toJson())).toList(),
    );
  }

  Future<void> _addAlert() async {
    final result = await showModalBottomSheet<PriceAlert>(
      context: context,
      isScrollControlled: true,
      builder: (_) => const _AddAlertSheet(),
    );
    if (result != null) {
      setState(() => _alerts.add(result));
      await _save();
    }
  }

  Future<void> _deleteAlert(int index) async {
    setState(() => _alerts.removeAt(index));
    await _save();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Fiyat Alarmları')),
      body: _alerts.isEmpty
          ? Center(
              child: Column(mainAxisSize: MainAxisSize.min, children: [
                Icon(Icons.notifications_none, size: 48, color: Colors.grey[400]),
                const SizedBox(height: 12),
                const Text('Henüz alarm eklenmedi.',
                  style: TextStyle(color: Colors.grey)),
                const SizedBox(height: 4),
                const Text('+ butonuna basarak alarm ekleyin.',
                  style: TextStyle(fontSize: 12, color: Colors.grey)),
              ]),
            )
          : ListView.separated(
              itemCount: _alerts.length,
              separatorBuilder: (_, __) => const Divider(height: 1),
              itemBuilder: (ctx, i) {
                final a = _alerts[i];
                final isAbove = a.direction == 'above';
                return ListTile(
                  leading: CircleAvatar(
                    backgroundColor: (isAbove ? Colors.green : Colors.red).withOpacity(0.12),
                    child: Icon(
                      isAbove ? Icons.arrow_upward : Icons.arrow_downward,
                      color: isAbove ? Colors.green : Colors.red,
                      size: 20,
                    ),
                  ),
                  title: Text(a.symbol, style: const TextStyle(fontWeight: FontWeight.bold)),
                  subtitle: Text(
                    '${isAbove ? "Üstünde" : "Altında"}: ₺${a.targetPrice.toStringAsFixed(2)}',
                    style: const TextStyle(fontSize: 13),
                  ),
                  trailing: Row(mainAxisSize: MainAxisSize.min, children: [
                    Text(
                      a.createdAt.toLocal().toString().substring(0, 10),
                      style: const TextStyle(fontSize: 11, color: Colors.grey),
                    ),
                    IconButton(
                      icon: const Icon(Icons.delete_outline, color: Colors.red, size: 20),
                      onPressed: () => _deleteAlert(i),
                    ),
                  ]),
                );
              },
            ),
      floatingActionButton: FloatingActionButton(
        onPressed: _addAlert,
        child: const Icon(Icons.add),
      ),
      bottomNavigationBar: Container(
        color: Colors.blue.withOpacity(0.08),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        child: const Text(
          '🔔 Push bildirimler yayın sürümünde aktif olur.',
          style: TextStyle(fontSize: 11, color: Colors.blueGrey),
          textAlign: TextAlign.center,
        ),
      ),
    );
  }
}

class _AddAlertSheet extends StatefulWidget {
  const _AddAlertSheet();

  @override
  State<_AddAlertSheet> createState() => _AddAlertSheetState();
}

class _AddAlertSheetState extends State<_AddAlertSheet> {
  final _formKey    = GlobalKey<FormState>();
  final _symbolCtrl = TextEditingController();
  final _priceCtrl  = TextEditingController();
  String _direction = 'above';

  @override
  void dispose() {
    _symbolCtrl.dispose();
    _priceCtrl.dispose();
    super.dispose();
  }

  void _submit() {
    if (!_formKey.currentState!.validate()) return;
    Navigator.pop(
      context,
      PriceAlert(
        symbol:      _symbolCtrl.text.trim().toUpperCase(),
        targetPrice: double.parse(_priceCtrl.text.trim()),
        direction:   _direction,
        createdAt:   DateTime.now(),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
        left: 16, right: 16, top: 24,
        bottom: MediaQuery.of(context).viewInsets.bottom + 24,
      ),
      child: Form(
        key: _formKey,
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          const Text('Yeni Fiyat Alarmı',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
          const SizedBox(height: 16),
          TextFormField(
            controller: _symbolCtrl,
            textCapitalization: TextCapitalization.characters,
            decoration: const InputDecoration(
              labelText: 'Sembol (örn. THYAO)',
              border: OutlineInputBorder(),
            ),
            validator: (v) => v == null || v.trim().isEmpty ? 'Sembol zorunlu' : null,
          ),
          const SizedBox(height: 12),
          TextFormField(
            controller: _priceCtrl,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            decoration: const InputDecoration(
              labelText: 'Hedef Fiyat (₺)',
              border: OutlineInputBorder(),
            ),
            validator: (v) {
              if (v == null || v.trim().isEmpty) return 'Fiyat zorunlu';
              if (double.tryParse(v.trim()) == null) return 'Geçerli sayı girin';
              return null;
            },
          ),
          const SizedBox(height: 12),
          Row(children: [
            const Text('Yön:', style: TextStyle(fontSize: 14)),
            const SizedBox(width: 12),
            ChoiceChip(
              label: const Text('Üstüne Çıkarsa'),
              selected: _direction == 'above',
              onSelected: (_) => setState(() => _direction = 'above'),
            ),
            const SizedBox(width: 8),
            ChoiceChip(
              label: const Text('Altına Düşerse'),
              selected: _direction == 'below',
              onSelected: (_) => setState(() => _direction = 'below'),
            ),
          ]),
          const SizedBox(height: 16),
          SizedBox(
            width: double.infinity,
            child: FilledButton(onPressed: _submit, child: const Text('Alarm Ekle')),
          ),
        ]),
      ),
    );
  }
}
