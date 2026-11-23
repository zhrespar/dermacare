import 'package:flutter/material.dart';

import '../../app/routes.dart';
import '../../widgets/step_scaffold.dart';

class QualityCheckScreen extends StatelessWidget {
  const QualityCheckScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const StepScaffold(
      title: 'Quality check',
      description: 'TODO: show blur / lighting / face size / region visibility results; offer retake when the photo is not usable.',
      nextRoute: Routes.analysis,
    );
  }
}
