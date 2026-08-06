/// Fiyat Alarmı Ekranı
///
/// Backend /api/alerts/price endpoint'i ile senkronize alarm yönetimi.
library;

import 'package:flutter/material.dart';

import '../services/api_service.dart';

class PriceAlertScreen extends StatefulWidget {
  final ApiService api;
  const PriceAlertScreen({super.key, required this.api});

  @override
  State<PriceAlertScreen> createState() => _PriceAlertScreenState();
}

class _PriceAlertScreenState extends State<PriceAlertScreen> {
  List<Map<String, dynamic>> _alerts = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; });
    try {
      final list = await widget.api.getAlerts();
      setState(() { _alerts = list; _loading = false; });
    } on ApiException catch (e) {
      setState(() {
        _loading = false;
        _error = e.statusCode == 401
            ? 'Alarmları görmek için giriş yapın.'
            : 'Alarmlar yüklenemedi (${e.statusCode})';
      });
    } catch (e) {
      setState(() { _loading = false; _error = 'Bağlantı hatası'; });
    }
  }

  Future<void> _addAlert() async {
    final result = await showModalBottomSheet<Map<String, dynamic>>(
      context: context,
      isScrollControlled: true,
      builder: (_) => const _AddAlertSheet(),
    );
    if (result == null) return;
    try {
      await widget.api.createAlert(
        symbol:    result['symbol'] as String,
        target:    result['target'] as double,
        direction: result['direction'] as String,
      );
      _load();
    } on ApiException catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Alarm eklenemedi: ${e.message}')),
        );
      }
    }
  }

  Future<void> _deleteAlert(int id) async {
    try {
      await widget.api.deleteAlert(id);
      setState(() => _alerts.removeWhere((a) => a['id'] == id));
    } on ApiException catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Alarm silinemedi: ${e.message}')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Fiyat Alarmları'),
        actions: [IconButton(icon: const Icon(Icons.refresh), onPressed: _load)],
      ),
      body: _buildBody(),
      floatingActionButton: FloatingActionButton(
        onPressed: _addAlert,
        child: const Icon(Icons.add),
      ),
      bottomNavigationBar: Container(
        color: Colors.blue.withValues(alpha: 0.08),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        child: const Text(
          '🔔 Push bildirimler yayın sürümünde aktif olur.',
          style: TextStyle(fontSize: 11, color: Colors.blueGrey),
          textAlign: TextAlign.center,
        ),
      ),
    );
  }

  Widget _buildBody() {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) {
      return Center(child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          const Icon(Icons.warning_amber, size: 40, color: Colors.orange),
          const SizedBox(height: 8),
          Text(_error!, textAlign: TextAlign.center),
          const SizedBox(height: 16),
          ElevatedButton(onPressed: _load, child: const Text('Tekrar Dene')),
        ]),
      ));
    }
    if (_alerts.isEmpty) {
      return Center(child: Column(mainAxisSize: MainAxisSize.min, children: [
        Icon(Icons.notifications_none, size: 48, color: Colors.grey[400]),
        const SizedBox(height: 12),
        const Text('Henüz alarm eklenmedi.', style: TextStyle(color: Colors.grey)),
        const SizedBox(height: 4),
        const Text('+ butonuna basarak alarm ekleyin.', style: TextStyle(fontSize: 12, color: Colors.grey)),
      ]));
    }
    return ListView.separated(
      itemCount: _alerts.length,
      separatorBuilder: (_, __) => const Divider(height: 1),
      itemBuilder: (ctx, i) {
        final a         = _alerts[i];
        final id        = a['id'] as int? ?? 0;
        final symbol    = a['symbol'] as String? ?? '';
        final target    = (a['target'] as num?)?.toDouble() ?? 0;
        final direction = a['direction'] as String? ?? 'above';
        final createdAt = a['created_at'] as String? ?? '';
        final isAbove   = direction == 'above';
        return ListTile(
          leading: CircleAvatar(
            backgroundColor: (isAbove ? Colors.green : Colors.red).withValues(alpha: 0.12),
            child: Icon(
              isAbove ? Icons.arrow_upward : Icons.arrow_downward,
              color: isAbove ? Colors.green : Colors.red,
              size: 20,
            ),
          ),
          title: Text(symbol, style: const TextStyle(fontWeight: FontWeight.bold)),
          subtitle: Text('${isAbove ? "Üstünde" : "Altında"}: ₺${target.toStringAsFixed(2)}'),
          trailing: Row(mainAxisSize: MainAxisSize.min, children: [
            Text(
              createdAt.length >= 10 ? createdAt.substring(0, 10) : createdAt,
              style: const TextStyle(fontSize: 11, color: Colors.grey),
            ),
            IconButton(
              icon: const Icon(Icons.delete_outline, color: Colors.red, size: 20),
              onPressed: () => _deleteAlert(id),
            ),
          ]),
        );
      },
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
    Navigator.pop(context, {
      'symbol':    _symbolCtrl.text.trim().toUpperCase(),
      'target':    double.parse(_priceCtrl.text.trim()),
      'direction': _direction,
    });
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
          const Text('Yeni Fiyat Alarmı', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
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
