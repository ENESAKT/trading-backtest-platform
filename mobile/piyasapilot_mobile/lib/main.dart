import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'core/theme/app_theme.dart';
import 'features/auth/presentation/login_screen.dart';
import 'features/auth/presentation/register_screen.dart';
import 'features/onboarding/presentation/onboarding_screen.dart';
import 'features/portfolio/presentation/portfolio_screen.dart';
import 'features/settings/presentation/settings_screen.dart';
import 'features/terminal/presentation/terminal_shell.dart';

void main() {
  runApp(const ProviderScope(child: PiyasaPilotMobileApp()));
}

class PiyasaPilotMobileApp extends StatelessWidget {
  const PiyasaPilotMobileApp({super.key});

  static final _router = GoRouter(
    initialLocation: '/onboarding',
    routes: [
      GoRoute(path: '/onboarding', builder: (_, __) => const OnboardingScreen()),
      GoRoute(path: '/login', builder: (_, __) => const LoginScreen()),
      GoRoute(path: '/register', builder: (_, __) => const RegisterScreen()),
      GoRoute(
        path: '/app',
        builder: (_, __) => const TerminalShell(),
        routes: [
          GoRoute(path: 'portfolio', builder: (_, __) => const PortfolioScreen()),
          GoRoute(path: 'settings', builder: (_, __) => const SettingsScreen()),
        ],
      ),
    ],
  );

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'PiyasaPilot',
      theme: buildAppTheme(),
      routerConfig: _router,
      debugShowCheckedModeBanner: false,
    );
  }
}
