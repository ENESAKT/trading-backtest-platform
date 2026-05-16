import 'package:flutter_test/flutter_test.dart';
import 'package:piyasapilot_mobile/main.dart';

void main() {
  testWidgets('renders onboarding entry screen', (tester) async {
    await tester.pumpWidget(const PiyasaPilotMobileApp());

    expect(find.text('PiyasaPilot'), findsOneWidget);
    expect(find.text('Başla'), findsOneWidget);
  });
}
