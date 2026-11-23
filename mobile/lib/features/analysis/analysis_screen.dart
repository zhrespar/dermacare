import 'package:flutter/material.dart';

import '../../app/routes.dart';
import '../../widgets/mock_banner.dart';
import '../../widgets/step_scaffold.dart';

class AnalysisScreen extends StatelessWidget {
  const AnalysisScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const StepScaffold(
      title: 'Skin analysis',
      description: 'TODO: upload photo and run analysis (acne, wrinkles, under-eye bags).',
      nextRoute: Routes.results,
      children: [MockBanner()],
    );
  }
}
