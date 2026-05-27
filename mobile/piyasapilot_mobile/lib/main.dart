/// PiyasaPilot Mobil — Ana Giriş Noktası
///
/// Uygulama başlarken SharedPreferences'tan token kontrol eder:
///   - Token varsa → HomeShell (ana ekran)
///   - Token yoksa  → LoginScreen
library;

import 'package:flutter/material.dart';

import 'screens/home_shell.dart';
import 'screens/login_screen.dart';
import 'services/api_service.dart';
import 'services/auth_store.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const PiyasaPilotApp());
}

class PiyasaPilotApp extends StatelessWidget {
  const PiyasaPilotApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'PiyasaPilot',
      debugShowCheckedModeBanner: false,
      theme: _buildTheme(Brightness.dark),
      darkTheme: _buildTheme(Brightness.dark),
      themeMode: ThemeMode.dark,
      home: const _AuthGate(),
      // Named route tablosu — NavigatorKey ile de kullanılabilir
      routes: {
        '/login': (_) => const _AuthGate(),
        '/home':  (_) => const _AuthGate(),
      },
    );
  }

  ThemeData _buildTheme(Brightness brightness) {
    final base = brightness == Brightness.dark
        ? ThemeData.dark(useMaterial3: true)
        : ThemeData.light(useMaterial3: true);

    return base.copyWith(
      colorScheme: ColorScheme.fromSeed(
        seedColor: const Color(0xFF1565C0),
        brightness: brightness,
      ),
      cardTheme: const CardThemeData(
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.all(Radius.circular(12)),
        ),
      ),
      appBarTheme: const AppBarTheme(
        centerTitle: false,
        elevation: 0,
        scrolledUnderElevation: 1,
      ),
      navigationBarTheme: const NavigationBarThemeData(
        labelBehavior: NavigationDestinationLabelBehavior.alwaysShow,
      ),
    );
  }
}

/// Token kontrolü yapan yönlendirici widget.
/// FutureBuilder ile async token okuma tamamlanana kadar loading gösterir.
class _AuthGate extends StatelessWidget {
  const _AuthGate();

  Future<_AuthResult> _resolve() async {
    final baseUrl = await AuthStore.loadBaseUrl();
    final token   = await AuthStore.loadToken();
    return _AuthResult(baseUrl: baseUrl, token: token);
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<_AuthResult>(
      future: _resolve(),
      builder: (ctx, snap) {
        if (snap.connectionState != ConnectionState.done) {
          return const Scaffold(
            body: Center(child: CircularProgressIndicator()),
          );
        }

        final result = snap.data!;
        final api    = ApiService(
          baseUrl:   result.baseUrl,
          authToken: result.token,
        );

        if (result.token != null) {
          return HomeShell(api: api);
        }
        return LoginScreen(api: api);
      },
    );
  }
}

class _AuthResult {
  final String  baseUrl;
  final String? token;
  const _AuthResult({required this.baseUrl, this.token});
}
