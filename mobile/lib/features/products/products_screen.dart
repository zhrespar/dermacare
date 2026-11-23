import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../app/routes.dart';
import '../../app/state.dart';
import '../../core/labels.dart' as l;
import '../../core/models.dart';
import '../../widgets/common.dart';

/// Every score component and every exclusion reason, so the result is auditable.
class ProductsScreen extends StatelessWidget {
  const ProductsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final r = AppScope.of(context).recommendation;
    final ranked = {for (final p in r?.ranked ?? <RankedProduct>[]) p.productId: p}.values.toList()
      ..sort((a, b) => b.totalScore.compareTo(a.totalScore));
    return PageScaffold(
      title: 'Ürün ayrıntıları',
      action: () => context.push(Routes.history),
      actionLabel: 'Geçmişim',
      children: [
        if (r == null) const Text('Henüz öneri yok.'),
        if (r != null) ...[
          Text('Kural sürümü ${r.rulesVersion} · Katalog ${r.catalogVersion ?? '—'}',
              style: Theme.of(context).textTheme.bodySmall),
          const SectionTitle('Önerilen ürünler'),
          if (ranked.isEmpty) const Text('Uygun ürün yok.'),
          for (final p in ranked) _ProductCard(p),
          if (r.excluded.isNotEmpty) ...[
            const SectionTitle('Elenen ürünler'),
            for (final e in r.excluded)
              ListTile(
                dense: true,
                leading: const Icon(Icons.block),
                title: Text(e.productId),
                subtitle: Text(e.reasons.map(l.exclusionLabel).join(' · ')),
              ),
          ],
        ],
      ],
    );
  }
}

class _ProductCard extends StatelessWidget {
  const _ProductCard(this.p);
  final RankedProduct p;

  static const _parts = {
    'need_ingredient': ('İhtiyaç ve içerik uyumu', 50.0),
    'profile_goal': ('Profil ve hedef uyumu', 25.0),
    'routine_category': ('Rutin uyumu', 15.0),
    'preference': ('Tercihler', 10.0),
  };

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Expanded(child: Text('${p.brand} ${p.name}', style: Theme.of(context).textTheme.titleSmall)),
            Text('${p.totalScore.round()}/100'),
          ]),
          const SizedBox(height: 8),
          for (final e in _parts.entries) ...[
            Text('${e.value.$1}: ${(p.breakdown[e.key] ?? 0).toStringAsFixed(1)} / ${e.value.$2.round()}',
                style: Theme.of(context).textTheme.bodySmall),
            LinearProgressIndicator(value: (p.breakdown[e.key] ?? 0) / e.value.$2),
            const SizedBox(height: 4),
          ],
          if (p.reasons.isNotEmpty) Text(p.reasons.join(' · ')),
        ]),
      ),
    );
  }
}
