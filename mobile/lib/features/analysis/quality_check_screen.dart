import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../app/routes.dart';
import '../../app/state.dart';
import '../../core/labels.dart' as l;
import '../../widgets/common.dart';

/// Uploads the photo, runs quality check + analysis, and gates the flow on the result.
class QualityCheckScreen extends StatefulWidget {
  const QualityCheckScreen({super.key});

  @override
  State<QualityCheckScreen> createState() => _QualityCheckScreenState();
}

class _QualityCheckScreenState extends State<QualityCheckScreen> {
  Object? _error;
  bool _started = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_started) return;
    _started = true;
    _run();
  }

  Future<void> _run() async {
    final app = AppScope.of(context);
    if (app.photo == null || app.analysis != null) return;
    setState(() => _error = null);
    try {
      app.analysis = await app.api.analyze(app.photo!, filename: app.photoName);
      app.update();
    } catch (e) {
      if (mounted) setState(() => _error = e);
    }
  }

  @override
  Widget build(BuildContext context) {
    final app = AppScope.of(context);
    final a = app.analysis;
    if (_error != null) {
      return PageScaffold(
        title: 'Kalite kontrolü',
        action: _run,
        actionLabel: 'Tekrar dene',
        children: [InfoCard(title: 'Analiz yapılamadı', body: errorText(_error!), tone: InfoTone.stop)],
      );
    }
    if (a == null) {
      return const PageScaffold(title: 'Kalite kontrolü', children: [
        SizedBox(height: 80),
        Center(child: CircularProgressIndicator()),
        SizedBox(height: 16),
        Center(child: Text('Fotoğraf kontrol ediliyor ve analiz ediliyor…')),
      ]);
    }
    final ok = a.qualityStatus == 'accepted';
    return PageScaffold(
      title: 'Kalite kontrolü',
      action: ok ? () => context.push(Routes.results) : () => context.pop(),
      actionLabel: ok ? 'Sonuçları gör' : 'Yeni fotoğraf çek',
      children: [
        InfoCard(
          title: ok ? 'Fotoğraf uygun' : 'Fotoğraf analize uygun değil',
          body: ok
              ? 'Fotoğraf kontrolden geçti ve analiz edildi.'
              : a.qualityReasons.map((r) => '• ${l.label(l.qualityReasons, r)}').join('\n'),
          tone: ok ? InfoTone.good : InfoTone.warn,
        ),
      ],
    );
  }
}
