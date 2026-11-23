import 'dart:typed_data';

import 'package:flutter/widgets.dart';

import '../core/api_client.dart';
import '../core/models.dart';

/// Session state shared by all screens. Holds nothing on disk; the photo stays in memory only.
class AppState extends ChangeNotifier {
  AppState(this.api);

  final ApiClient api;
  Profile profile = Profile();
  Uint8List? photo;
  String photoName = 'face.jpg';
  AnalysisResult? analysis;
  RecommendationResult? recommendation;
  Explanation? explanation;

  bool get signedIn => api.token != null;

  void setPhoto(Uint8List bytes, String name) {
    photo = bytes;
    photoName = name;
    analysis = null;
    recommendation = null;
    explanation = null;
    notifyListeners();
  }

  void update() => notifyListeners();

  void signOut() {
    api.token = null;
    profile = Profile();
    photo = null;
    analysis = null;
    recommendation = null;
    explanation = null;
    notifyListeners();
  }
}

class AppScope extends InheritedNotifier<AppState> {
  const AppScope({super.key, required AppState state, required super.child}) : super(notifier: state);

  static AppState of(BuildContext context) =>
      context.dependOnInheritedWidgetOfExactType<AppScope>()!.notifier!;
}
