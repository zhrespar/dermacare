import 'package:flutter/material.dart';

/// Shown on every screen that displays analysis output while models are mocked.
class MockBanner extends StatelessWidget {
  const MockBanner({super.key});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Card(
      color: scheme.tertiaryContainer,
      child: const Padding(
        padding: EdgeInsets.all(12),
        child: Text('MOCK DATA — placeholder models, not a real analysis.'),
      ),
    );
  }
}
