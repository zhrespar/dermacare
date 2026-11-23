import 'dart:typed_data';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../app/routes.dart';
import '../../app/state.dart';
import '../../core/labels.dart' as l;
import '../../core/models.dart';
import '../../widgets/common.dart';
import '../../widgets/mock_banner.dart';

class ResultsScreen extends StatelessWidget {
  const ResultsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final app = AppScope.of(context);
    final a = app.analysis;
    if (a == null) {
      return PageScaffold(
        title: 'Sonuçlar',
        action: () => context.go(Routes.capture),
        actionLabel: 'Fotoğraf çek',
        children: const [Text('Henüz analiz yok.')],
      );
    }
    final action = a.triage.action;
    final refer = action == 'refer_dermatologist';
    return PageScaffold(
      title: 'Sonuçlar',
      action: refer ? () => context.go(Routes.history) : () => context.push(Routes.routine),
      actionLabel: refer ? 'Geçmişe git' : (action == 'proceed' ? 'Rutinimi oluştur' : 'Profile göre rutin oluştur'),
      children: [
        if (a.isMock) const MockBanner(),
        InfoCard(
          title: l.label(l.triageTitles, action),
          body: l.label(l.triageTexts, action),
          tone: switch (action) {
            'proceed' => InfoTone.good,
            'refer_dermatologist' => InfoTone.stop,
            _ => InfoTone.warn,
          },
        ),
        if (!refer && app.photo != null) ...[
          const SizedBox(height: 8),
          _PhotoWithBoxes(bytes: app.photo!, boxes: a.acne?.lesions ?? const []),
          const SizedBox(height: 4),
          Text('Kutular, tespit edilen akne lezyonlarını gösterir.', style: Theme.of(context).textTheme.bodySmall),
        ],
        if (!refer) ..._findings(context, a),
        const Disclaimer(),
      ],
    );
  }

  List<Widget> _findings(BuildContext context, AnalysisResult a) {
    String pct(double v) => '%${(v * 100).round()}';
    return [
      if (a.acne != null) ...[
        const SectionTitle('Akne'),
        _Row('Şiddet seviyesi', l.label(l.severities, a.acne!.severity)),
        _Row('Model güveni', pct(a.acne!.severityProbabilities.reduce((x, y) => x > y ? x : y))),
        _Row('Lezyon sayısı', '${a.acne!.lesionCount}'),
        for (final r in a.regions) _Row('  ${l.label(l.regions, r.region)}', '${r.lesionCount} lezyon'),
      ],
      if (a.wrinkleAreaRatio != null) ...[
        const SectionTitle('Kırışıklık ve ince çizgiler'),
        _Row('Etkilenen alan', pct(a.wrinkleAreaRatio!)),
        if (a.wrinkleConfidence != null) _Row('Model güveni', pct(a.wrinkleConfidence!)),
      ],
      if (a.underEyePresent != null) ...[
        const SectionTitle('Göz altı torbası'),
        _Row('Sonuç', a.underEyePresent! ? 'Var' : 'Yok'),
        if (a.underEyeProbability != null) _Row('Olasılık', pct(a.underEyeProbability!)),
        Text(
          'Bu bir yüz özelliği sınıflandırmasıdır; tıbbi bir değerlendirme değildir.',
          style: Theme.of(context).textTheme.bodySmall,
        ),
      ],
    ];
  }
}

class _Row extends StatelessWidget {
  const _Row(this.k, this.v);
  final String k, v;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 3),
        child: Row(children: [Expanded(child: Text(k)), Text(v, style: const TextStyle(fontWeight: FontWeight.w600))]),
      );
}

/// Draws normalized lesion boxes over the photo at its real aspect ratio.
class _PhotoWithBoxes extends StatelessWidget {
  const _PhotoWithBoxes({required this.bytes, required this.boxes});
  final Uint8List bytes;
  final List<LesionBox> boxes;

  Future<Size> _size() async {
    final codec = await ui.instantiateImageCodec(bytes);
    final f = await codec.getNextFrame();
    return Size(f.image.width.toDouble(), f.image.height.toDouble());
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<Size>(
      future: _size(),
      builder: (context, snap) {
        final ratio = snap.hasData ? snap.data!.width / snap.data!.height : 3 / 4;
        return ClipRRect(
          borderRadius: BorderRadius.circular(16),
          child: AspectRatio(
            aspectRatio: ratio,
            child: Stack(fit: StackFit.expand, children: [
              Image.memory(bytes, fit: BoxFit.fill),
              CustomPaint(painter: _BoxPainter(boxes, Theme.of(context).colorScheme.error)),
            ]),
          ),
        );
      },
    );
  }
}

class _BoxPainter extends CustomPainter {
  _BoxPainter(this.boxes, this.color);
  final List<LesionBox> boxes;
  final Color color;

  @override
  void paint(Canvas canvas, Size s) {
    final p = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2;
    for (final b in boxes) {
      canvas.drawRect(Rect.fromLTRB(b.xMin * s.width, b.yMin * s.height, b.xMax * s.width, b.yMax * s.height), p);
    }
  }

  @override
  bool shouldRepaint(_BoxPainter old) => old.boxes != boxes;
}
