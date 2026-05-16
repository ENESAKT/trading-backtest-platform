import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class OnboardingScreen extends StatelessWidget {
  const OnboardingScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('PiyasaPilot', style: Theme.of(context).textTheme.displaySmall),
              const SizedBox(height: 12),
              const Text('Mobil terminal, paper portföy ve plan yönetimi için native başlangıç.'),
              const Spacer(),
              FilledButton(onPressed: () => context.go('/login'), child: const Text('Başla')),
            ],
          ),
        ),
      ),
    );
  }
}
