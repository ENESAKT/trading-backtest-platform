/// Ayarlar Ekranı
///
/// Kullanıcı bilgisi, plan durumu, API URL değiştirme ve çıkış.
library;

import 'package:flutter/material.dart';

import '../services/api_service.dart';
import '../services/auth_store.dart';

class SettingsScreen extends StatefulWidget {
  final ApiService api;
  const SettingsScreen({super.key, required this.api});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  Map<String, dynamic>? _me;
  Map<String, dynamic>? _limits;
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
      final me     = await widget.api.getMe();
      final limits = await widget.api.getLimits();
      setState(() { _me = me; _limits = limits; _loading = false; });
    } on ApiException catch (e) {
      setState(() {
        _loading = false;
        _error = e.statusCode == 401 ? 'Oturum süresi dolmuş.' : 'Profil yüklenemedi (${e.statusCode})';
      });
    } catch (_) {
      setState(() { _loading = false; _error = 'Bağlantı hatası'; });
    }
  }

  Future<void> _logout() async {
    await AuthStore.clearToken();
    if (!mounted) return;
    Navigator.of(context).pushReplacementNamed('/login');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Ayarlar'),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _load),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? _ErrorView(message: _error!, onRetry: _load)
              : _buildBody(),
    );
  }

  Widget _buildBody() {
    final me     = _me     ?? {};
    final limits = _limits ?? {};
    final plan   = me['plan'] as String? ?? 'free';
    final email  = me['email'] as String? ?? '—';

    return ListView(children: [
      // Kullanıcı kartı
      Card(
        margin: const EdgeInsets.all(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(children: [
            CircleAvatar(
              radius: 24,
              backgroundColor: Theme.of(context).colorScheme.primaryContainer,
              child: Text(
                email.isNotEmpty ? email[0].toUpperCase() : '?',
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 20),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(email, style: const TextStyle(fontWeight: FontWeight.bold)),
              const SizedBox(height: 2),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: _planColor(plan).withOpacity(0.15),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(plan.toUpperCase(),
                  style: TextStyle(fontSize: 11, color: _planColor(plan), fontWeight: FontWeight.bold)),
              ),
            ])),
          ]),
        ),
      ),

      // Plan limitleri
      if (limits.isNotEmpty) ...[
        const Padding(
          padding: EdgeInsets.fromLTRB(16, 8, 16, 4),
          child: Text('PLAN LİMİTLERİ',
            style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, letterSpacing: 1, color: Colors.grey)),
        ),
        ...limits.entries.map((e) => ListTile(
          dense: true,
          title: Text(_limitLabel(e.key)),
          trailing: Text('${e.value}', style: const TextStyle(fontWeight: FontWeight.bold)),
        )),
      ],

      const Divider(),

      // Hakkında
      ListTile(
        leading: const Icon(Icons.info_outline),
        title: const Text('Uygulama Hakkında'),
        subtitle: const Text('PiyasaPilot v1.0 — BIST/VİOP Terminal'),
      ),
      ListTile(
        leading: const Icon(Icons.description_outlined),
        title: const Text('Yasal Uyarı'),
        subtitle: const Text('Bu uygulama yatırım tavsiyesi vermez.'),
        onTap: () => _showDisclaimer(),
      ),

      const Divider(),

      // Çıkış
      ListTile(
        leading: const Icon(Icons.logout, color: Colors.red),
        title: const Text('Çıkış Yap', style: TextStyle(color: Colors.red)),
        onTap: () async {
          final ok = await showDialog<bool>(
            context: context,
            builder: (_) => AlertDialog(
              title: const Text('Çıkış Yap'),
              content: const Text('Oturumunuzu kapatmak istediğinizden emin misiniz?'),
              actions: [
                TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('İptal')),
                FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Çıkış')),
              ],
            ),
          );
          if (ok == true) await _logout();
        },
      ),

      const SizedBox(height: 24),
      Center(
        child: Text(
          '⚠️ PiyasaPilot yatırım tavsiyesi vermez.\nGeçmiş performans gelecek sonuçları garanti etmez.',
          textAlign: TextAlign.center,
          style: const TextStyle(fontSize: 10, color: Colors.grey),
        ),
      ),
      const SizedBox(height: 16),
    ]);
  }

  void _showDisclaimer() {
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Yasal Uyarı'),
        content: const SingleChildScrollView(
          child: Text(
            'PiyasaPilot platformundaki tüm veriler, analizler, sinyaller ve '
            'backtest sonuçları yalnızca bilgi amaçlıdır. Yatırım tavsiyesi, '
            'portföy yönetimi veya finansal danışmanlık hizmeti değildir.\n\n'
            'Geçmiş performans gelecekteki sonuçları garanti etmez. '
            'BIST ve VİOP işlemleri sermaye kaybı riski taşır.\n\n'
            'Paper trading (sanal işlem) gerçek para veya emir içermez.',
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Anladım')),
        ],
      ),
    );
  }

  Color _planColor(String plan) => switch (plan.toLowerCase()) {
        'pro'   => Colors.blue,
        'ultra' => Colors.purple,
        _       => Colors.grey,
      };

  String _limitLabel(String key) => switch (key) {
        'backtests_per_day'    => 'Günlük Backtest',
        'watchlist_symbols'    => 'İzleme Listesi',
        'screener_presets'     => 'Screener Preset',
        'paper_strategies'     => 'Paper Strateji',
        'signal_subscriptions' => 'Sinyal Aboneliği',
        _                      => key,
      };
}

class _ErrorView extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;
  const _ErrorView({required this.message, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    return Center(child: Padding(
      padding: const EdgeInsets.all(24),
      child: Column(mainAxisSize: MainAxisSize.min, children: [
        const Icon(Icons.error_outline, size: 40, color: Colors.red),
        const SizedBox(height: 8),
        Text(message, textAlign: TextAlign.center),
        const SizedBox(height: 16),
        ElevatedButton(onPressed: onRetry, child: const Text('Tekrar Dene')),
      ]),
    ));
  }
}
