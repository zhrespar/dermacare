import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../app/routes.dart';
import '../../app/state.dart';
import '../../core/labels.dart' as l;
import '../../core/models.dart';
import '../../widgets/common.dart';

/// Unanswered fields stay null ("unknown"); they are never treated as "no".
class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

enum _Allergy { unanswered, none, some }

List<String> _list(String s) => s.split(';').map((e) => e.trim()).where((e) => e.isNotEmpty).toList();

class _ProfileScreenState extends State<ProfileScreen> {
  late Profile _p;
  late _Allergy _allergyMode;
  final _allergies = TextEditingController();
  final _avoid = TextEditingController();
  final _reactions = TextEditingController();
  final _budget = TextEditingController();
  bool _busy = false;
  bool _init = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_init) return;
    _init = true;
    final src = AppScope.of(context).profile;
    _p = Profile.fromJson(src.toJson());
    _allergyMode = _p.allergies == null
        ? _Allergy.unanswered
        : (_p.allergies!.isEmpty ? _Allergy.none : _Allergy.some);
    _allergies.text = (_p.allergies ?? []).join('; ');
    _avoid.text = _p.avoidIngredients.join('; ');
    _reactions.text = _p.pastReactionIngredients.join('; ');
    _budget.text = _p.budgetMax?.toStringAsFixed(0) ?? '';
  }

  Future<void> _save() async {
    final app = AppScope.of(context);
    _p.allergies = switch (_allergyMode) {
      _Allergy.unanswered => null,
      _Allergy.none => <String>[],
      _Allergy.some => _list(_allergies.text),
    };
    _p.avoidIngredients = _list(_avoid.text);
    _p.pastReactionIngredients = _list(_reactions.text);
    _p.budgetMax = double.tryParse(_budget.text.replaceAll(',', '.'));
    _p.currency = _p.budgetMax == null ? null : 'TRY';
    setState(() => _busy = true);
    try {
      app.profile = await app.api.putProfile(_p);
      app.update();
      if (mounted) context.push(Routes.capture);
    } catch (e) {
      if (mounted) showError(context, e);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Widget _single(String title, Map<String, String> opts, String? value, ValueChanged<String?> set) {
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      SectionTitle(title),
      Wrap(spacing: 8, runSpacing: 8, children: [
        for (final e in opts.entries)
          ChoiceChip(label: Text(e.value), selected: value == e.key, onSelected: (_) => set(e.key)),
        ChoiceChip(label: const Text('Bilmiyorum'), selected: value == null, onSelected: (_) => set(null)),
      ]),
    ]);
  }

  @override
  Widget build(BuildContext context) {
    return PageScaffold(
      title: 'Cilt profili',
      action: _save,
      actionLabel: 'Kaydet ve devam et',
      busy: _busy,
      children: [
        const Text('Bilmediğiniz soruları boş bırakabilirsiniz; "bilinmiyor" olarak kaydedilir.'),
        _single('Cilt tipi', l.skinTypes, _p.skinType, (v) => setState(() => _p.skinType = v)),
        _single('Hassasiyet', l.sensitivities, _p.sensitivity, (v) => setState(() => _p.sensitivity = v)),
        const SectionTitle('Bilinen alerjiler'),
        SegmentedButton<_Allergy>(
          segments: const [
            ButtonSegment(value: _Allergy.unanswered, label: Text('Boş bırak')),
            ButtonSegment(value: _Allergy.none, label: Text('Yok')),
            ButtonSegment(value: _Allergy.some, label: Text('Var')),
          ],
          selected: {_allergyMode},
          onSelectionChanged: (s) => setState(() => _allergyMode = s.first),
        ),
        if (_allergyMode == _Allergy.some)
          TextField(
            key: const Key('allergies'),
            controller: _allergies,
            decoration: const InputDecoration(
              labelText: 'İçerik adları (INCI)',
              helperText: 'Noktalı virgülle ayırın, ör. PARFUM; LINALOOL',
            ),
          ),
        const SectionTitle('Kaçınmak istediğim içerikler'),
        TextField(controller: _avoid, decoration: const InputDecoration(helperText: 'Noktalı virgülle ayırın')),
        const SectionTitle('Daha önce tepki verdiğim içerikler'),
        TextField(
          controller: _reactions,
          decoration: const InputDecoration(helperText: 'Bu içerikleri barındıran ürünler hiç önerilmez'),
        ),
        const SectionTitle('Hedeflerim'),
        Wrap(spacing: 8, runSpacing: 8, children: [
          for (final e in l.needs.entries)
            FilterChip(
              label: Text(e.value),
              selected: _p.goals.contains(e.key),
              onSelected: (on) => setState(() {
                _p.goals = on ? [..._p.goals, e.key] : _p.goals.where((g) => g != e.key).toList();
              }),
            ),
        ]),
        const SectionTitle('Tercih ettiğim ürün türleri'),
        Wrap(spacing: 8, runSpacing: 8, children: [
          for (final e in l.categories.entries)
            FilterChip(
              label: Text(e.value),
              selected: _p.preferredCategories.contains(e.key),
              onSelected: (on) => setState(() {
                _p.preferredCategories = on
                    ? [..._p.preferredCategories, e.key]
                    : _p.preferredCategories.where((g) => g != e.key).toList();
              }),
            ),
        ]),
        const SectionTitle('Ürün başına en fazla bütçe'),
        TextField(
          controller: _budget,
          keyboardType: const TextInputType.numberWithOptions(decimal: true),
          decoration: const InputDecoration(suffixText: 'TL', helperText: 'Boş bırakırsanız bütçe sınırı uygulanmaz'),
        ),
      ],
    );
  }
}
