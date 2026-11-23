import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../app/routes.dart';
import '../../core/config.dart';

class WelcomeScreen extends StatelessWidget {
  const WelcomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Spacer(),
              Text('DermaCare', style: text.displaySmall),
              const SizedBox(height: 12),
              Text(
                'Explainable skin analysis and a personalised morning/evening routine.',
                style: text.titleMedium,
              ),
              const SizedBox(height: 16),
              Text(disclaimer, style: text.bodySmall),
              const Spacer(),
              FilledButton(
                key: const Key('get-started'),
                onPressed: () => context.push(Routes.auth),
                child: const Text('Get started'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
