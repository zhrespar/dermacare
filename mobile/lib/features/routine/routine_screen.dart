import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../app/routes.dart';
import '../../app/state.dart';
import '../../core/labels.dart' as l;
import '../../core/models.dart';
import '../../widgets/common.dart';
import '../../widgets/mock_banner.dart';

/// Rule-engine routine (authoritative) + optional cited explanation (explains only, never changes it).
class RoutineScreen extends StatefulWidget {
  const RoutineScreen({super.key});

  @override
  State<RoutineScreen> createState() => _RoutineScreenState();
}

class _RoutineScreenState extends State<RoutineScreen> {
  Object? _error;
  bool _explaining = false;
  bool _started = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_started) return;
    _started = true;
    _load();
  }

  Future<void> _load() async {
    final app = AppScope.of(context);
    if (app.recommendation != null) return;
    setState(() => _error = null);
    try {
      app.recommendation = await app.api.recommend(analysisId: app.analysis?.id);
      app.update();
    } catch (e) {
      if (mounted) setState(() => _error = e);
    }
  }

  Future<void> _explain() async {
    final app = AppScope.of(context);
    setState(() => _explaining = true);
    try {
      app.explanation = await app.api.explain(app.recommendation!);
      app.update();
    } catch (e) {
      if (mounted) showError(context, e);
    } finally {
      if (mounted) setState(() => _explaining = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final app = AppScope.of(context);
    final r = app.recommendation;
    if (_error != null) {
      return PageScaffold(title: 'Rutinim', action: _load, actionLabel: 'Tekrar dene', children: [
        InfoCard(title: 'Rutin oluşturulamadı', body: errorText(_error!), tone: InfoTone.stop),
      ]);
    }
    if (r == null) {
      return const PageScaffold(title: 'Rutinim', children: [
        SizedBox(height: 80),
        Center(child: CircularProgressIndicator()),
      ]);
    }
    final byId = {for (final p in r.ranked) p.productId: p};
    final empty = r.morningRoutine.isEmpty && r.eveningRoutine.isEmpty;
    return PageScaffold(
      title: 'Rutinim',
      action: () => context.push(Routes.products),
      actionLabel: 'Ürün ayrıntıları',
      children: [
        if (app.analysis?.isMock ?? false) const MockBanner(),
        Wrap(spacing: 6, runSpacing: 6, children: [
          for (final n in r.needs) Chip(label: Text(l.label(l.needs, n))),
        ]),
        if (empty)
          InfoCard(
            title: 'Henüz ürün önerilemiyor',
            body: r.catalogVersion == null
                ? 'Doğrulanmış ürün kataloğu henüz yüklenmedi.'
                : 'Katalogda profilinize ve kısıtlarınıza uyan ürün bulunamadı.',
            tone: InfoTone.warn,
          ),
        _routine(context, 'Sabah', r.morningRoutine, byId),
        _routine(context, 'Akşam', r.eveningRoutine, byId),
        if (r.missingInformation.isNotEmpty)
          InfoCard(
            title: 'Eksik bilgi',
            body: 'Daha isabetli öneriler için profilinizi tamamlayın: '
                '${r.missingInformation.map(_missing).join(', ')}.',
          ),
        const SectionTitle('Neden bu ürünler?'),
        if (app.explanation == null)
          OutlinedButton(
            key: const Key('explain'),
            onPressed: empty || _explaining ? null : _explain,
            child: Text(_explaining ? 'Hazırlanıyor…' : 'Açıklamayı göster'),
          )
        else
          _ExplanationView(app.explanation!),
        const Disclaimer(),
      ],
    );
  }

  String _missing(String m) => switch (m) {
        'allergies' => 'alerjiler',
        'sensitivity' => 'hassasiyet',
        'no_catalog_version' => 'ürün kataloğu',
        _ when m.startsWith('image_findings_withheld') => 'fotoğraf bulguları (güven düşük)',
        _ => m,
      };

  Widget _routine(BuildContext context, String title, List<RoutineStep> steps, Map<String, RankedProduct> byId) {
    if (steps.isEmpty) return const SizedBox.shrink();
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      SectionTitle(title),
      for (final s in steps)
        Card(
          child: ListTile(
            leading: CircleAvatar(child: Text('${s.step}')),
            title: Text('${byId[s.productId]?.brand ?? ''} ${byId[s.productId]?.name ?? s.productId}'),
            subtitle: Text([
              l.label(l.categories, s.category),
              if (s.usageInstructions != null) s.usageInstructions!,
            ].join(' · ')),
            trailing: Text('${byId[s.productId]?.totalScore.round() ?? '-'}/100'),
          ),
        ),
    ]);
  }
}

class _ExplanationView extends StatelessWidget {
  const _ExplanationView(this.e);
  final Explanation e;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(
            e.mode == 'llm_grounded' ? 'Kaynaklara dayalı açıklama' : 'Kural tabanlı açıklama',
            style: Theme.of(context).textTheme.labelLarge,
          ),
          const SizedBox(height: 8),
          Text(e.text, key: const Key('explanation-text')),
          if (e.citations.isNotEmpty) ...[
            const SizedBox(height: 12),
            Text('Kaynaklar', style: Theme.of(context).textTheme.labelLarge),
            for (final c in e.citations)
              Padding(
                padding: const EdgeInsets.only(top: 4),
                child: SelectableText('[${c.sourceId}] ${c.title} — ${c.publisher}\n${c.sourceUrl}'),
              ),
          ] else
            Padding(
              padding: const EdgeInsets.only(top: 8),
              child: Text(
                'Bu açıklama kuralların gerekçelerinden oluşturuldu; dış kaynak kullanılmadı.',
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ),
        ]),
      ),
    );
  }
}
