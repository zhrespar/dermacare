import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

/// Shared placeholder layout for each step of the journey.
class StepScaffold extends StatelessWidget {
  const StepScaffold({
    super.key,
    required this.title,
    required this.description,
    this.nextRoute,
    this.nextLabel = 'Continue',
    this.children = const [],
  });

  final String title;
  final String description;
  final String? nextRoute;
  final String nextLabel;
  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(title)),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(24),
          children: [
            Text(description, style: Theme.of(context).textTheme.bodyLarge),
            const SizedBox(height: 16),
            ...children,
          ],
        ),
      ),
      bottomNavigationBar: nextRoute == null
          ? null
          : SafeArea(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: FilledButton(
                  key: const Key('next'),
                  onPressed: () => context.push(nextRoute!),
                  child: Text(nextLabel),
                ),
              ),
            ),
    );
  }
}
