import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  bool _loading = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Giriş')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          const TextField(decoration: InputDecoration(labelText: 'E-posta')),
          const SizedBox(height: 12),
          const TextField(obscureText: true, decoration: InputDecoration(labelText: 'Şifre')),
          const SizedBox(height: 20),
          FilledButton(
            onPressed: _loading
                ? null
                : () async {
                    setState(() => _loading = true);
                    await Future<void>.delayed(const Duration(milliseconds: 250));
                    if (context.mounted) context.go('/app');
                  },
            child: Text(_loading ? 'Bağlanıyor...' : 'Giriş Yap'),
          ),
          TextButton(onPressed: () => context.go('/register'), child: const Text('Hesap oluştur')),
        ],
      ),
    );
  }
}
