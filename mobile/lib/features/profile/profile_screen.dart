import 'package:flutter/material.dart';

import '../../app/routes.dart';
import '../../widgets/step_scaffold.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const StepScaffold(
      title: 'Skin profile',
      description: 'TODO: skin type, sensitivity, known allergies / ingredients to avoid, current routine, goals, budget and preferences. Unanswered items stay unknown, never assumed.',
      nextRoute: Routes.capture,
    );
  }
}
