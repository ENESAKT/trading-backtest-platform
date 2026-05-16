import 'package:flutter/material.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Ayarlar')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: const [
          ListTile(title: Text('Plan'), subtitle: Text('Free / Pro / Ultra bilgisi /api/auth/me ile senkronize edilir.')),
          ListTile(title: Text('API'), subtitle: Text(String.fromEnvironment('API_BASE_URL', defaultValue: 'http://10.0.2.2:8000'))),
          ListTile(title: Text('Risk'), subtitle: Text('PiyasaPilot yatırım tavsiyesi vermez; mobil uygulama gerçek emir göndermez.')),
        ],
      ),
    );
  }
}
