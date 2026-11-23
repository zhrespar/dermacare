import 'package:flutter/material.dart';

import '../core/api_client.dart';
import '../core/config.dart';

/// Page layout with an optional bottom action button.
class PageScaffold extends StatelessWidget {
  const PageScaffold({
    super.key,
    required this.title,
    required this.children,
    this.action,
    this.actionLabel = 'Devam',
    this.actionKey = const Key('next'),
    this.busy = false,
    this.showDisabledAction = false,
  });

  final String title;
  final List<Widget> children;
  final VoidCallback? action;
  final String actionLabel;
  final Key actionKey;
  final bool busy;

  /// Keep the button visible (disabled) while [action] is null, e.g. until a form is valid.
  final bool showDisabledAction;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(title)),
      body: SafeArea(
        child: ListView(padding: const EdgeInsets.fromLTRB(20, 12, 20, 24), children: children),
      ),
      bottomNavigationBar: action == null && !showDisabledAction
          ? null
          : SafeArea(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: FilledButton(
                  key: actionKey,
                  onPressed: busy ? null : action,
                  child: busy
                      ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2))
                      : Text(actionLabel),
                ),
              ),
            ),
    );
  }
}

class SectionTitle extends StatelessWidget {
  const SectionTitle(this.text, {super.key});
  final String text;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(top: 20, bottom: 8),
        child: Text(text, style: Theme.of(context).textTheme.titleMedium),
      );
}

class InfoCard extends StatelessWidget {
  const InfoCard({super.key, required this.title, required this.body, this.tone = InfoTone.neutral});
  final String title;
  final String body;
  final InfoTone tone;

  @override
  Widget build(BuildContext context) {
    final c = Theme.of(context).colorScheme;
    final bg = switch (tone) {
      InfoTone.good => c.primaryContainer,
      InfoTone.warn => c.tertiaryContainer,
      InfoTone.stop => c.errorContainer,
      InfoTone.neutral => c.surfaceContainerHighest,
    };
    return Card(
      color: bg,
      margin: const EdgeInsets.symmetric(vertical: 6),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(title, style: Theme.of(context).textTheme.titleSmall),
          const SizedBox(height: 4),
          Text(body),
        ]),
      ),
    );
  }
}

enum InfoTone { neutral, good, warn, stop }

class Disclaimer extends StatelessWidget {
  const Disclaimer({super.key});

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(top: 24),
        child: Text(disclaimer, style: Theme.of(context).textTheme.bodySmall),
      );
}

String errorText(Object e) {
  if (e is ApiException) {
    return switch (e.code) {
      'invalid_credentials' => 'E-posta veya şifre hatalı.',
      'email_already_registered' => 'Bu e-posta zaten kayıtlı.',
      'image_too_large' => 'Fotoğraf çok büyük.',
      'model_backend_not_available' => 'Analiz servisi şu an kullanılamıyor.',
      _ => 'Sunucu hatası (${e.statusCode}).',
    };
  }
  return 'Sunucuya bağlanılamadı. İnternet bağlantınızı kontrol edin.';
}

void showError(BuildContext context, Object e) =>
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(errorText(e))));
