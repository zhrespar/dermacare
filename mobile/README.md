# DermaCare mobile (Flutter)

Android + iOS client (Turkish UI). Journey:
Welcome → Auth (register with privacy consent / login) → Skin Profile → Frontal Photo (camera or gallery) →
Quality Check + Analysis → Results (triage, lesion boxes, regions) → Routine (AM/PM + cited explanation) →
Product details (score breakdown, exclusions) → History (+ delete account).

| Path | Contents |
|---|---|
| `lib/core/api_client.dart` | Typed client for every backend endpoint (bearer token) |
| `lib/core/models.dart` | Dart mirrors of the API schemas (`docs/API_SPEC.yaml`) |
| `lib/core/labels.dart` | Turkish labels for API codes |
| `lib/app/state.dart` | Session state (token, profile, photo in memory, analysis, recommendation) |
| `lib/app/router.dart` | Routes; signed-out users are redirected to Auth |
| `lib/features/*` | One folder per screen |

Rules the UI enforces: mock results always show the "DENEME VERİSİ" banner; `refer_dermatologist` stops the cosmetic
flow; `limited` explains that the routine uses the profile only; unanswered profile questions stay unknown; the photo is
kept in memory only.

## Run

```bash
cd mobile
flutter pub get
flutter analyze && flutter test
flutter run -d chrome --dart-define=API_BASE_URL=http://localhost:8000        # quick preview in a browser
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000                   # Android emulator
flutter run --dart-define=API_BASE_URL=http://localhost:8000                  # iOS simulator
```

iOS needs Xcode; Android needs Android Studio (SDK + emulator). Camera/photo permission texts are in
`ios/Runner/Info.plist`.
