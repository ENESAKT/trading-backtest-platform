import 'package:flutter/material.dart';

class RegisterScreen extends StatelessWidget {
  const RegisterScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Kayıt Ol')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: const [
          TextField(decoration: InputDecoration(labelText: 'Ad Soyad')),
          SizedBox(height: 12),
          TextField(decoration: InputDecoration(labelText: 'E-posta')),
          SizedBox(height: 12),
          TextField(obscureText: true, decoration: InputDecoration(labelText: 'Şifre')),
          SizedBox(height: 20),
          FilledButton(onPressed: null, child: Text('Backend bağlantısı bekleniyor')),
        ],
      ),
    );
  }
}
