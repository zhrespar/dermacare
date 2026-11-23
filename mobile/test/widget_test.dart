import 'dart:convert';

import 'package:dermacare/app/app.dart';
import 'package:dermacare/app/state.dart';
import 'package:dermacare/core/api_client.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

// 1x1 PNG. Synthetic test image only — never a real face.
final png = base64Decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==');

const analysisJson = {
  'id': 'a1',
  'is_mock': true,
  'quality': {'status': 'accepted', 'reasons': []},
  'triage': {'action': 'proceed', 'reasons': ['mock_backend']},
  'acne': {
    'lesion_count': 1,
    'lesions': [
      {'x_min': 0.2, 'y_min': 0.5, 'x_max': 0.25, 'y_max': 0.55, 'confidence': 0.5, 'region': 'right_cheek'}
    ],
    'severity': 'mild',
    'severity_probabilities': [0.7, 0.1, 0.1, 0.1],
  },
  'wrinkles': {'affected_area_ratio': 0.05, 'mean_confidence': 0.5},
  'under_eye': {'present': false, 'probability': 0.2},
  'regions': [
    {'region': 'right_cheek', 'lesion_count': 1}
  ],
  'model_versions': {},
  'disclaimer': 'd',
};

const rankedJson = {
  'product_id': 'P1',
  'brand': 'FIXTURE',
  'name': 'Serum',
  'routine_slot': 'pm',
  'total_score': 80.0,
  'breakdown': {'need_ingredient': 50.0, 'profile_goal': 15.0, 'routine_category': 15.0, 'preference': 0.0},
  'reasons': ['addresses: acne_care'],
};

const recommendationJson = {
  'rules_version': '0.1.0-provisional',
  'mode': 'multimodal',
  'needs': ['acne_care', 'sun_protection'],
  'missing_information': [],
  'morning': [],
  'evening': [rankedJson],
  'morning_routine': [],
  'evening_routine': [
    {'step': 1, 'category': 'serum', 'product_id': 'P1', 'usage_instructions': null}
  ],
  'skipped_for_compatibility': [],
  'excluded': [
    {'product_id': 'P2', 'reasons': ['contains_blocked_ingredient:parfum']}
  ],
  'pending_rules': [],
  'recommendation_id': 'r1',
  'catalog_version': 'FIXTURE-v1',
};

class FakeBackend {
  final calls = <String>[];

  http.Response _j(Object body, [int status = 200]) => http.Response(jsonEncode(body), status,
      headers: {'content-type': 'application/json; charset=utf-8'});

  Future<http.Response> handle(http.Request r) async {
    final key = '${r.method} ${r.url.path}';
    calls.add(key);
    if (r.url.path != '/api/v1/auth/register' && r.headers['Authorization'] != 'Bearer T') {
      return _j({'detail': 'not_authenticated'}, 401);
    }
    return switch (key) {
      'POST /api/v1/auth/register' => _j({'access_token': 'T', 'token_type': 'bearer'}, 201),
      'GET /api/v1/profile' => _j({'allergies': null, 'goals': []}),
      'PUT /api/v1/profile' => _j(jsonDecode(r.body) as Object),
      'POST /api/v1/analyses' => _j(analysisJson),
      'POST /api/v1/recommendations' => _j(recommendationJson),
      'POST /api/v1/explanations' => _j({
          'mode': 'rule_template',
          'text': 'Akşam 1 (serum): FIXTURE Serum',
          'citations': [],
          'provider': 'none',
          'model': 'none',
          'rules_version': 'x',
          'fallback_reason': 'no_verified_sources',
          'metrics': {'retrieved_chunks': 0},
          'disclaimer': 'd',
        }),
      'GET /api/v1/analyses' => _j([
          {'id': 'a1', 'created_at': '2026-11-23T10:00:00Z', 'status': 'completed', 'is_mock': true, 'triage_action': 'proceed', 'model_versions': {}}
        ]),
      'DELETE /api/v1/me' => http.Response('', 204),
      _ => _j({'detail': 'not_found'}, 404),
    };
  }
}

Future<void> tapAndSettle(WidgetTester t, Finder f) async {
  await t.ensureVisible(f);
  await t.tap(f);
  await t.pumpAndSettle();
}

void main() {
  testWidgets('welcome shows disclaimer and start button', (t) async {
    await t.pumpWidget(DermaCareApp(api: ApiClient(client: MockClient((_) async => http.Response('', 500)))));
    expect(find.text('DermaCare'), findsOneWidget);
    expect(find.textContaining('teşhisi koymaz'), findsOneWidget);
    expect(find.byKey(const Key('get-started')), findsOneWidget);
  });

  testWidgets('full journey: register, profile, photo, results, routine, explanation, history, delete',
      (t) async {
    final be = FakeBackend();
    await t.pumpWidget(DermaCareApp(api: ApiClient(client: MockClient(be.handle), baseUrl: 'http://x')));

    await tapAndSettle(t, find.byKey(const Key('get-started')));
    await t.enterText(find.byKey(const Key('email')), 'fixture@example.com');
    await t.enterText(find.byKey(const Key('password')), 'long-enough-pw');
    await tapAndSettle(t, find.byKey(const Key('consent')));
    await tapAndSettle(t, find.byKey(const Key('next')));
    expect(find.text('Cilt profili'), findsOneWidget);

    await tapAndSettle(t, find.text('Yağlı'));
    await tapAndSettle(t, find.byKey(const Key('next')));
    expect(find.text('Yüz fotoğrafı'), findsOneWidget);

    AppScope.of(t.element(find.text('Yüz fotoğrafı'))).setPhoto(png, 'fixture.png');
    await t.pumpAndSettle();
    await tapAndSettle(t, find.byKey(const Key('next')));
    expect(find.text('Fotoğraf uygun'), findsOneWidget);

    await tapAndSettle(t, find.byKey(const Key('next')));
    expect(find.byKey(const Key('mock-banner')), findsOneWidget);
    expect(find.text('Analiz tamamlandı'), findsOneWidget);
    await t.scrollUntilVisible(find.text('  Sağ yanak'), 200);
    expect(find.text('  Sağ yanak'), findsOneWidget);

    await tapAndSettle(t, find.byKey(const Key('next')));
    expect(find.text('FIXTURE Serum'), findsOneWidget);
    await tapAndSettle(t, find.byKey(const Key('explain')));
    expect(find.byKey(const Key('explanation-text')), findsOneWidget);
    expect(find.textContaining('dış kaynak kullanılmadı'), findsOneWidget);

    await tapAndSettle(t, find.byKey(const Key('next')));
    expect(find.text('Kaçındığınız içerik: parfum'), findsOneWidget);

    await tapAndSettle(t, find.byKey(const Key('next')));
    expect(find.text('Geçmiş'), findsOneWidget);
    expect(find.textContaining('deneme verisi'), findsOneWidget);

    await tapAndSettle(t, find.byKey(const Key('delete-account')));
    await tapAndSettle(t, find.byKey(const Key('confirm-delete')));
    expect(find.byKey(const Key('get-started')), findsOneWidget);
    expect(be.calls, contains('DELETE /api/v1/me'));
    expect(be.calls.where((c) => c == 'POST /api/v1/analyses').length, 1);
  });

  testWidgets('protected screens redirect to auth when signed out', (t) async {
    await t.pumpWidget(DermaCareApp(api: ApiClient(client: MockClient((_) async => http.Response('', 500)))));
    final ctx = t.element(find.byKey(const Key('get-started')));
    GoRouter.of(ctx).go('/routine');
    await t.pumpAndSettle();
    expect(find.text('Hesap oluştur'), findsOneWidget);
  });
}
