/// PiyasaPilot widget testi — smoke test
///
/// Uygulama MaterialApp ile başlatılabilir mi kontrol eder.
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:piyasapilot_mobile/main.dart';

void main() {
  testWidgets('Uygulama başarılı şekilde yüklenir', (tester) async {
    await tester.pumpWidget(const PiyasaPilotApp());
    // MaterialApp'ın render edildiğini doğrula
    expect(find.byType(MaterialApp), findsOneWidget);
  });
}
