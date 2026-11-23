import 'dart:convert';

import 'package:http/http.dart' as http;

import 'config.dart';
import 'models.dart';

/// Typed client for the FastAPI backend (docs/API_SPEC.yaml).
class ApiClient {
  ApiClient({http.Client? client, String? baseUrl})
      : _client = client ?? http.Client(),
        _base = baseUrl ?? apiBaseUrl;

  final http.Client _client;
  final String _base;
  String? token;

  Map<String, String> get _auth => token == null ? {} : {'Authorization': 'Bearer $token'};

  Future<Map<String, dynamic>> health() async => _json(await _client.get(Uri.parse('$_base/health')));

  // ---- account ---------------------------------------------------------------

  Future<void> register(String email, String password, String consentVersion) async {
    final res = await _post('/api/v1/auth/register',
        {'email': email, 'password': password, 'consent_version': consentVersion},
        expect: 201);
    token = res['access_token'] as String;
  }

  Future<void> login(String email, String password) async {
    final res = await _post('/api/v1/auth/login', {'email': email, 'password': password});
    token = res['access_token'] as String;
  }

  Future<Profile> getProfile() async =>
      Profile.fromJson(_json(await _client.get(_u('/api/v1/profile'), headers: _auth)));

  Future<Profile> putProfile(Profile p) async {
    final res = await _client.put(_u('/api/v1/profile'),
        headers: {..._auth, 'content-type': 'application/json'}, body: jsonEncode(p.toJson()));
    return Profile.fromJson(_json(res));
  }

  Future<void> deleteAccount() async {
    final res = await _client.delete(_u('/api/v1/me'), headers: _auth);
    if (res.statusCode != 204) throw ApiException(res.statusCode, res.body);
    token = null;
  }

  // ---- analysis / recommendation / explanation -------------------------------

  Future<AnalysisResult> analyze(List<int> imageBytes, {String filename = 'face.jpg'}) async {
    final req = http.MultipartRequest('POST', _u('/api/v1/analyses'))
      ..headers.addAll(_auth)
      ..files.add(http.MultipartFile.fromBytes('image', imageBytes, filename: filename));
    final res = await http.Response.fromStream(await _client.send(req));
    return AnalysisResult.fromJson(_json(res));
  }

  Future<List<AnalysisSummary>> history() async {
    final res = await _client.get(_u('/api/v1/analyses'), headers: _auth);
    if (res.statusCode != 200) throw ApiException(res.statusCode, res.body);
    return (jsonDecode(utf8.decode(res.bodyBytes)) as List)
        .map((e) => AnalysisSummary.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  /// Stored profile + optional stored analysis + current catalog version.
  Future<RecommendationResult> recommend({String? analysisId}) async =>
      RecommendationResult.fromJson(
          await _post('/api/v1/recommendations', {if (analysisId != null) 'analysis_id': analysisId}));

  Future<RecommendationResult> previewRecommendations(Map<String, dynamic> request) async =>
      RecommendationResult.fromJson(await _post('/api/v1/recommendations/preview', request));

  /// The engine result is sent back unchanged; the server only explains it.
  Future<Explanation> explain(RecommendationResult rec, {String language = 'tr'}) async =>
      Explanation.fromJson(
          await _post('/api/v1/explanations', {'recommendation': rec.raw, 'language': language}));

  // ---- helpers ---------------------------------------------------------------

  Uri _u(String path) => Uri.parse('$_base$path');

  Future<Map<String, dynamic>> _post(String path, Map<String, dynamic> body, {int expect = 200}) async {
    final res = await _client.post(_u(path),
        headers: {..._auth, 'content-type': 'application/json'}, body: jsonEncode(body));
    return _json(res, expect: expect);
  }

  Map<String, dynamic> _json(http.Response res, {int expect = 200}) {
    if (res.statusCode != expect) throw ApiException(res.statusCode, res.body);
    return jsonDecode(utf8.decode(res.bodyBytes)) as Map<String, dynamic>;
  }
}

class ApiException implements Exception {
  ApiException(this.statusCode, this.body);
  final int statusCode;
  final String body;

  /// Server error code such as "invalid_credentials", if present.
  String? get code {
    try {
      final d = jsonDecode(body);
      return d is Map && d['detail'] is String ? d['detail'] as String : null;
    } catch (_) {
      return null;
    }
  }

  @override
  String toString() => 'ApiException($statusCode${code == null ? '' : ', $code'})';
}
