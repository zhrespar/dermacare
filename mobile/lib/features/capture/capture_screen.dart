import 'package:flutter/material.dart';

import '../../app/routes.dart';
import '../../widgets/step_scaffold.dart';

class CaptureScreen extends StatelessWidget {
  const CaptureScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const StepScaffold(
      title: 'Frontal photo',
      description: 'TODO: guided single frontal capture — even lighting, neutral expression, no filters or makeup, face inside the oval.',
      nextRoute: Routes.quality,
    );
  }
}
