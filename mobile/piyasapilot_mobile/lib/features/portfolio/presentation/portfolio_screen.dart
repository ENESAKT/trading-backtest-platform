import 'package:flutter/material.dart';

import '../../../shared/widgets/app_state_panel.dart';

class PortfolioScreen extends StatelessWidget {
  const PortfolioScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      body: AppStatePanel(
        title: 'Paper Portföy',
        message: 'Sanal cüzdan, açık pozisyon ve PnL kartları backend paper endpointleri bağlandığında dolacak.',
      ),
    );
  }
}
