import 'package:dermacare/core/models.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('parses mock analysis contract', () {
    final a = AnalysisResult.fromJson({
      'id': 'x',
      'is_mock': true,
      'quality': {'status': 'accepted', 'reasons': []},
      'triage': {'action': 'proceed', 'reasons': ['mock_backend']},
      'acne': {
        'lesion_count': 1,
        'lesions': [
          {'x_min': 0.2, 'y_min': 0.4, 'x_max': 0.25, 'y_max': 0.45, 'confidence': 0.5, 'region': 'right_cheek'}
        ],
        'severity': 'mild',
        'severity_probabilities': [0.7, 0.1, 0.1, 0.1],
      },
      'wrinkles': null,
      'under_eye': {'present': false, 'probability': 0.2},
      'model_versions': {},
      'disclaimer': 'd',
    });
    expect(a.isMock, isTrue);
    expect(a.acne!.lesions.single.region, 'right_cheek');
    expect(a.underEyePresent, isFalse);
  });

  test('parses rule-template explanation', () {
    final e = Explanation.fromJson({
      'mode': 'rule_template',
      'text': 't',
      'citations': [],
      'fallback_reason': 'no_verified_sources',
      'disclaimer': 'd',
    });
    expect(e.citations, isEmpty);
    expect(e.fallbackReason, 'no_verified_sources');
  });
}
