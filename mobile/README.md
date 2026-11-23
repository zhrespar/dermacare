# DermaCare mobile (Flutter)

Android + iOS client. Screens follow the journey:
Welcome → Auth → Skin Profile → Frontal Photo → Quality Check → Analysis → Results → Routine → Products → History.

## First-time setup

The Dart/Flutter sources are committed; native platform folders are generated once by the Flutter tool
(they were not generated in the initial commit because the Flutter SDK was not available in that environment):

```bash
cd mobile
flutter create --org com.dermacare --project-name dermacare --platforms=android,ios .
flutter pub get
flutter analyze
flutter test
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000   # Android emulator
```

Commit the generated `android/` and `ios/` folders after review. Camera permissions
(`NSCameraUsageDescription`, Android `CAMERA`) are added when the capture screen is implemented.
