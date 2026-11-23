import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../app/routes.dart';
import '../../app/state.dart';
import '../../widgets/common.dart';

/// Privacy-notice version the user accepts at registration (stored server-side).
const consentVersion = '2026-11';

class AuthScreen extends StatefulWidget {
  const AuthScreen({super.key});

  @override
  State<AuthScreen> createState() => _AuthScreenState();
}

class _AuthScreenState extends State<AuthScreen> {
  final _email = TextEditingController();
  final _password = TextEditingController();
  bool _register = true;
  bool _consent = false;
  bool _busy = false;

  Future<void> _submit() async {
    final app = AppScope.of(context);
    setState(() => _busy = true);
    try {
      if (_register) {
        await app.api.register(_email.text.trim(), _password.text, consentVersion);
      } else {
        await app.api.login(_email.text.trim(), _password.text);
      }
      app.profile = await app.api.getProfile();
      app.update();
      if (mounted) context.go(Routes.profile);
    } catch (e) {
      if (mounted) showError(context, e);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final valid = _email.text.contains('@') &&
        _password.text.length >= (_register ? 10 : 1) &&
        (!_register || _consent);
    return PageScaffold(
      title: _register ? 'Hesap oluştur' : 'Giriş yap',
      action: valid ? _submit : null,
      actionLabel: _register ? 'Kayıt ol' : 'Giriş yap',
      busy: _busy,
      showDisabledAction: true,
      children: [
        SegmentedButton<bool>(
          segments: const [
            ButtonSegment(value: true, label: Text('Kayıt ol')),
            ButtonSegment(value: false, label: Text('Giriş yap')),
          ],
          selected: {_register},
          onSelectionChanged: (s) => setState(() => _register = s.first),
        ),
        const SizedBox(height: 16),
        TextField(
          key: const Key('email'),
          controller: _email,
          keyboardType: TextInputType.emailAddress,
          autofillHints: const [AutofillHints.email],
          decoration: const InputDecoration(labelText: 'E-posta'),
          onChanged: (_) => setState(() {}),
        ),
        const SizedBox(height: 12),
        TextField(
          key: const Key('password'),
          controller: _password,
          obscureText: true,
          decoration: InputDecoration(
            labelText: 'Şifre',
            helperText: _register ? 'En az 10 karakter' : null,
          ),
          onChanged: (_) => setState(() {}),
        ),
        if (_register) ...[
          const SizedBox(height: 12),
          CheckboxListTile(
            key: const Key('consent'),
            contentPadding: EdgeInsets.zero,
            value: _consent,
            onChanged: (v) => setState(() => _consent = v ?? false),
            title: const Text(
              'Gizlilik bildirimini okudum. Fotoğrafımın yalnızca analiz için işlenmesini ve '
              'sonuçlarımın hesabımda saklanmasını kabul ediyorum. Hesabımı istediğim zaman silebilirim.',
            ),
          ),
        ],
        const Disclaimer(),
      ],
    );
  }
}
