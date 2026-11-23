import 'dart:convert';

import 'package:http/http.dart' as http;

import 'config.dart';
import 'models.dart';

class ApiClient {
  ApiClient({http.Client? client, String? baseUrl})
      : _client = client ?? http.Client(),
        _base = baseUrl ?? apiBaseUrl;

  final http.Client _client;
  final String _base;

  Future<Map<String, dynamic>> health() async {
    final res = await _client.get(Uri.parse('$_base/health'));
    if (res.statusCode != 200) {
      throw ApiException(res.statusCode, res.body);
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  Future<AnalysisResult> analyze(List<int> imageBytes, {String filename = 'face.jpg'}) async {
    final req = http.MultipartRequest('POST', Uri.parse('$_base/api/v1/analyses'))
      ..files.add(http.MultipartFile.fromBytes('image', imageBytes, filename: filename));
    final res = await http.Response.fromStream(await _client.send(req));
    return AnalysisResult.fromJson(_json(res));
  }

  Future<RecommendationResult> previewRecommendations(Map<String, dynamic> request) async {
    final res = await _post('/api/v1/recommendations/preview', request);
    return RecommendationResult.fromJson(_json(res));
  }

  /// The engine result is sent back unchanged; the server only explains it.
  Future<Explanation> explain(RecommendationResult rec, {String language = 'tr'}) async {
    final res = await _post('/api/v1/explanations', {'recommendation': rec.raw, 'language': language});
    return Explanation.fromJson(_json(res));
  }

  Future<http.Response> _post(String path, Map<String, dynamic> body) => _client.post(
        Uri.parse('$_base$path'),
        headers: {'content-type': 'application/json'},
        body: jsonEncode(body),
      );

  Map<String, dynamic> _json(http.Response res) {
    if (res.statusCode != 200) throw ApiException(res.statusCode, res.body);
    return jsonDecode(utf8.decode(res.bodyBytes)) as Map<String, dynamic>;
  }
}

class ApiException implements Exception {
  ApiException(this.statusCode, this.body);
  final int statusCode;
  final String body;

  @override
  String toString() => 'ApiException($statusCode)';
}
