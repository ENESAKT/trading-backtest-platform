/// Ana Kabuk — Bottom Navigation Shell
///
/// Tüm ana sekmeleri barındırır. Her sekme kendi Navigator stack'ine sahiptir
/// böylece geri tuşu sekmeyi kapatmadan çalışır.
library;

import 'package:flutter/material.dart';

import '../services/api_service.dart';
import '../services/auth_store.dart';
import 'watchlist_screen.dart';
import 'signals_screen.dart';
import 'paper_portfolio_screen.dart';
import 'screener_screen.dart';
import 'settings_screen.dart';

class HomeShell extends StatefulWidget {
  final ApiService api;
  const HomeShell({super.key, required this.api});

  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> {
  int _selectedIndex = 0;

  static const _tabLabels = ['İzleme', 'Sinyaller', 'Portföy', 'Tarayıcı', 'Ayarlar'];
  static const _tabIcons  = [
    Icons.list_alt,
    Icons.notifications_active_outlined,
    Icons.account_balance_wallet_outlined,
    Icons.search,
    Icons.settings_outlined,
  ];
  static const _tabIconsSelected = [
    Icons.list_alt_rounded,
    Icons.notifications_active,
    Icons.account_balance_wallet,
    Icons.search,
    Icons.settings,
  ];

  late final List<Widget> _pages;

  @override
  void initState() {
    super.initState();
    _pages = [
      WatchlistScreen(api: widget.api),
      SignalsScreen(api: widget.api),
      PaperPortfolioScreen(api: widget.api, strategyId: 'default'),
      ScreenerScreen(api: widget.api),
      SettingsScreen(api: widget.api),
    ];
  }

  Future<void> _logout() async {
    await AuthStore.clearToken();
    if (!mounted) return;
    Navigator.of(context).pushReplacementNamed('/login');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _selectedIndex,
        children: _pages,
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _selectedIndex,
        onDestinationSelected: (i) => setState(() => _selectedIndex = i),
        destinations: List.generate(_tabLabels.length, (i) => NavigationDestination(
          icon:         Icon(_tabIcons[i]),
          selectedIcon: Icon(_tabIconsSelected[i]),
          label: _tabLabels[i],
        )),
      ),
    );
  }
}
