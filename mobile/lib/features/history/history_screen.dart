import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../app/routes.dart';
import '../../app/state.dart';
import '../../core/labels.dart' as l;
import '../../core/models.dart';
import '../../widgets/common.dart';

class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  Future<List<AnalysisSummary>>? _items;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    _items ??= AppScope.of(context).api.history();
  }

  Future<void> _delete() async {
    final app = AppScope.of(context);
    final ok = await showDialog<bool>(
      context: context,
      builder: (c) => AlertDialog(
        title: const Text('Hesabımı sil'),
        content: const Text('Profiliniz, analizleriniz ve önerileriniz kalıcı olarak silinecek. Bu işlem geri alınamaz.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(c, false), child: const Text('Vazgeç')),
          FilledButton(key: const Key('confirm-delete'), onPressed: () => Navigator.pop(c, true), child: const Text('Sil')),
        ],
      ),
    );
    if (ok != true || !mounted) return;
    try {
      await app.api.deleteAccount();
      app.signOut();
      if (mounted) context.go(Routes.welcome);
    } catch (e) {
      if (mounted) showError(context, e);
    }
  }

  @override
  Widget build(BuildContext context) {
    final app = AppScope.of(context);
    return PageScaffold(
      title: 'Geçmiş',
      action: () {
        app.photo = null;
        app.analysis = null;
        app.recommendation = null;
        app.explanation = null;
        app.update();
        context.go(Routes.capture);
      },
      actionLabel: 'Yeni analiz',
      actionKey: const Key('new-analysis'),
      children: [
        FutureBuilder<List<AnalysisSummary>>(
          future: _items,
          builder: (context, snap) {
            if (snap.hasError) return Text(errorText(snap.error!));
            if (!snap.hasData) return const Center(child: CircularProgressIndicator());
            if (snap.data!.isEmpty) return const Text('Henüz kayıtlı analiz yok.');
            return Column(children: [
              for (final a in snap.data!)
                ListTile(
                  leading: const Icon(Icons.history),
                  title: Text(
                    '${a.createdAt.toLocal().day.toString().padLeft(2, '0')}.'
                    '${a.createdAt.toLocal().month.toString().padLeft(2, '0')}.${a.createdAt.toLocal().year}',
                  ),
                  subtitle: Text(l.label(l.triageTitles, a.triageAction) + (a.isMock ? ' · deneme verisi' : '')),
                ),
            ]);
          },
        ),
        const SectionTitle('Hesap'),
        OutlinedButton(onPressed: () => context.push(Routes.profile), child: const Text('Profilimi düzenle')),
        const SizedBox(height: 8),
        TextButton(
          key: const Key('delete-account'),
          onPressed: _delete,
          style: TextButton.styleFrom(foregroundColor: Theme.of(context).colorScheme.error),
          child: const Text('Hesabımı ve tüm verilerimi sil'),
        ),
      ],
    );
  }
}
