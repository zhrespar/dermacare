import 'package:flutter/material.dart';

import '../../widgets/step_scaffold.dart';

class HistoryScreen extends StatelessWidget {
  const HistoryScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const StepScaffold(
      title: 'History',
      description: 'TODO: past analyses and recommendations; delete my data.',
      nextRoute: null,
    );
  }
}
