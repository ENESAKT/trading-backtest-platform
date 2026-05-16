import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:piyasapilot_mobile/main.dart';
import 'package:piyasapilot_mobile/shared/widgets/app_state_panel.dart';
import 'package:piyasapilot_mobile/shared/widgets/plan_gate_widget.dart';

void main() {
  testWidgets('renders onboarding entry screen', (tester) async {
    await tester.pumpWidget(const PiyasaPilotMobileApp());

    expect(find.text('PiyasaPilot'), findsOneWidget);
    expect(find.text('Başla'), findsOneWidget);
  });

  testWidgets('plan gate locks pro features for free users', (tester) async {
    await tester.pumpWidget(const MaterialApp(
      home: PlanGateWidget(
        userPlan: 'free',
        requiredPlan: 'pro',
        featureName: 'Sinyaller',
        child: AppStatePanel(title: 'Sinyaller', message: 'Locked child'),
      ),
    ));

    expect(find.text('Sinyaller için PRO planı gerekli'), findsOneWidget);
  });
}
