// Typed mirrors of the FastAPI contract (docs/API_SPEC.yaml). Keep field names in sync.
// `isMock == true` results must always be shown with the MOCK banner.

double _d(Object? v) => (v as num).toDouble();
List<String> _strs(Object? v) => (v as List? ?? const []).cast<String>();

class LesionBox {
  LesionBox.fromJson(Map<String, dynamic> j)
      : xMin = _d(j['x_min']),
        yMin = _d(j['y_min']),
        xMax = _d(j['x_max']),
        yMax = _d(j['y_max']),
        confidence = _d(j['confidence']),
        region = j['region'] as String?;
  final double xMin, yMin, xMax, yMax, confidence;
  final String? region;
}

class AcneFinding {
  AcneFinding.fromJson(Map<String, dynamic> j)
      : lesionCount = j['lesion_count'] as int,
        lesions = (j['lesions'] as List)
            .map((e) => LesionBox.fromJson(e as Map<String, dynamic>))
            .toList(),
        severity = j['severity'] as String,
        severityProbabilities =
            (j['severity_probabilities'] as List).map(_d).toList();
  final int lesionCount;
  final List<LesionBox> lesions;
  final String severity;
  final List<double> severityProbabilities;
}

class Triage {
  Triage.fromJson(Map<String, dynamic> j)
      : action = j['action'] as String,
        reasons = _strs(j['reasons']);

  /// proceed | limited | refer_dermatologist | retake
  final String action;
  final List<String> reasons;
}

class AnalysisResult {
  AnalysisResult.fromJson(Map<String, dynamic> j)
      : id = j['id'] as String,
        isMock = j['is_mock'] as bool,
        qualityStatus = (j['quality'] as Map<String, dynamic>)['status'] as String,
        triage = Triage.fromJson(j['triage'] as Map<String, dynamic>),
        acne = j['acne'] == null
            ? null
            : AcneFinding.fromJson(j['acne'] as Map<String, dynamic>),
        wrinkleAreaRatio = j['wrinkles'] == null
            ? null
            : _d((j['wrinkles'] as Map)['affected_area_ratio']),
        underEyePresent = j['under_eye'] == null
            ? null
            : (j['under_eye'] as Map)['present'] as bool,
        disclaimer = j['disclaimer'] as String;
  final String id;
  final bool isMock;
  final String qualityStatus;
  final Triage triage;
  final AcneFinding? acne;
  final double? wrinkleAreaRatio;
  final bool? underEyePresent;
  final String disclaimer;
}

class RoutineStep {
  RoutineStep.fromJson(Map<String, dynamic> j)
      : step = j['step'] as int,
        category = j['category'] as String,
        productId = j['product_id'] as String,
        usageInstructions = j['usage_instructions'] as String?;
  final int step;
  final String category;
  final String productId;
  final String? usageInstructions;
}

class RankedProduct {
  RankedProduct.fromJson(Map<String, dynamic> j)
      : productId = j['product_id'] as String,
        brand = j['brand'] as String,
        name = j['name'] as String,
        totalScore = _d(j['total_score']),
        breakdown = (j['breakdown'] as Map<String, dynamic>)
            .map((k, v) => MapEntry(k, _d(v))),
        reasons = _strs(j['reasons']);
  final String productId, brand, name;
  final double totalScore;
  final Map<String, double> breakdown;
  final List<String> reasons;
}

class RecommendationResult {
  RecommendationResult.fromJson(this.raw)
      : rulesVersion = raw['rules_version'] as String,
        needs = _strs(raw['needs']),
        missingInformation = _strs(raw['missing_information']),
        ranked = [...raw['morning'] as List, ...raw['evening'] as List]
            .map((e) => RankedProduct.fromJson(e as Map<String, dynamic>))
            .toList(),
        morningRoutine = (raw['morning_routine'] as List? ?? const [])
            .map((e) => RoutineStep.fromJson(e as Map<String, dynamic>))
            .toList(),
        eveningRoutine = (raw['evening_routine'] as List? ?? const [])
            .map((e) => RoutineStep.fromJson(e as Map<String, dynamic>))
            .toList();

  /// Original JSON, sent back unchanged to /api/v1/explanations.
  final Map<String, dynamic> raw;
  final String rulesVersion;
  final List<String> needs, missingInformation;
  final List<RankedProduct> ranked;
  final List<RoutineStep> morningRoutine, eveningRoutine;
}

class Citation {
  Citation.fromJson(Map<String, dynamic> j)
      : sourceId = j['source_id'] as String,
        title = j['title'] as String,
        publisher = j['publisher'] as String,
        sourceUrl = j['source_url'] as String;
  final String sourceId, title, publisher, sourceUrl;
}

class Explanation {
  Explanation.fromJson(Map<String, dynamic> j)
      : mode = j['mode'] as String,
        text = j['text'] as String,
        citations = (j['citations'] as List)
            .map((e) => Citation.fromJson(e as Map<String, dynamic>))
            .toList(),
        fallbackReason = j['fallback_reason'] as String?,
        disclaimer = j['disclaimer'] as String;

  /// llm_grounded | rule_template
  final String mode;
  final String text;
  final List<Citation> citations;
  final String? fallbackReason;
  final String disclaimer;
}
