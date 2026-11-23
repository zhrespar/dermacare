import 'package:flutter/material.dart';

import '../../app/routes.dart';
import '../../widgets/step_scaffold.dart';

class AuthScreen extends StatelessWidget {
  const AuthScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const StepScaffold(
      title: 'Sign in',
      description: 'TODO: email/password sign-up and sign-in, consent to privacy notice (KVKK/GDPR).',
      nextRoute: Routes.profile,
    );
  }
}
