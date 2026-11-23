import 'package:flutter/material.dart';

import '../../app/routes.dart';
import '../../widgets/step_scaffold.dart';

class RoutineScreen extends StatelessWidget {
  const RoutineScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const StepScaffold(
      title: 'Your routine',
      description: 'TODO: morning and evening routine steps built from recommended product categories.',
      nextRoute: Routes.products,
    );
  }
}
