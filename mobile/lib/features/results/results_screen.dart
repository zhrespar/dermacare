import 'package:flutter/material.dart';

import '../../app/routes.dart';
import '../../widgets/mock_banner.dart';
import '../../widgets/step_scaffold.dart';

class ResultsScreen extends StatelessWidget {
  const ResultsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const StepScaffold(
      title: 'Your results',
      description: 'TODO: acne lesion boxes + severity, wrinkle mask overlay, under-eye result with Grad-CAM, confidence and plain-language explanations.',
      nextRoute: Routes.routine,
      children: [MockBanner()],
    );
  }
}
