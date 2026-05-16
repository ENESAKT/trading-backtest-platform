import 'package:flutter/material.dart';

class PlanGateWidget extends StatelessWidget {
  const PlanGateWidget({
    required this.userPlan,
    required this.requiredPlan,
    required this.featureName,
    required this.child,
    super.key,
  });

  final String userPlan;
  final String requiredPlan;
  final String featureName;
  final Widget child;

  static const _rank = {
    'free': 0,
    'pro': 1,
    'ultra': 2,
    'admin': 3,
  };

  bool get _hasAccess => (_rank[userPlan] ?? 0) >= (_rank[requiredPlan] ?? 0);

  @override
  Widget build(BuildContext context) {
    if (_hasAccess) return child;
    return Stack(
      fit: StackFit.expand,
      children: [
        Opacity(opacity: 0.28, child: IgnorePointer(child: child)),
        DecoratedBox(
          decoration: BoxDecoration(color: Theme.of(context).colorScheme.surface.withValues(alpha: 0.82)),
          child: Center(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.lock, size: 40),
                  const SizedBox(height: 12),
                  Text('$featureName için ${requiredPlan.toUpperCase()} planı gerekli'),
                  const SizedBox(height: 12),
                  const FilledButton(onPressed: null, child: Text('Plan yükseltme web ödeme ile açılır')),
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }
}
