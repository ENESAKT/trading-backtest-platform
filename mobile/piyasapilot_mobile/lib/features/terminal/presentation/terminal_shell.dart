import 'package:flutter/material.dart';

import '../../../shared/widgets/app_state_panel.dart';
import '../../../shared/widgets/plan_gate_widget.dart';

class TerminalShell extends StatefulWidget {
  const TerminalShell({super.key});

  @override
  State<TerminalShell> createState() => _TerminalShellState();
}

class _TerminalShellState extends State<TerminalShell> {
  int _index = 0;

  @override
  Widget build(BuildContext context) {
    const userPlan = String.fromEnvironment('DEMO_PLAN', defaultValue: 'free');
    final pages = [
      const AppStatePanel(
        title: 'Grafik',
        message: 'BTCUSDT / 1s mum grafiği için API client hazır. Gerçek barlar backend /api/v2/candles üzerinden yüklenecek.',
      ),
      const PlanGateWidget(
        userPlan: userPlan,
        requiredPlan: 'pro',
        featureName: 'Sinyaller',
        child: AppStatePanel(
          title: 'Sinyaller',
          message: 'Pro+ sinyal ekranı plan gate ve güvenilir veri durumu ile bağlanacak.',
        ),
      ),
      const AppStatePanel(
        title: 'Portföy',
        message: 'Paper mode gerçek emir göndermez; yalnızca eğitim ve simülasyon amaçlıdır.',
      ),
      const AppStatePanel(
        title: 'Ayarlar',
        message: 'Profil, plan ve dil ayarları /api/auth/me kontratıyla eşlenecek.',
      ),
    ];
    return Scaffold(
      appBar: AppBar(title: const Text('PiyasaPilot')),
      body: pages[_index],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: (value) => setState(() => _index = value),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.candlestick_chart), label: 'Grafik'),
          NavigationDestination(icon: Icon(Icons.notifications_active), label: 'Sinyal'),
          NavigationDestination(icon: Icon(Icons.account_balance_wallet), label: 'Portföy'),
          NavigationDestination(icon: Icon(Icons.settings), label: 'Ayarlar'),
        ],
      ),
    );
  }
}
