/// Backend base URL. Override at build time:
///   flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
/// (10.0.2.2 = host machine from the Android emulator; iOS simulator can use localhost.)
const apiBaseUrl = String.fromEnvironment('API_BASE_URL', defaultValue: 'http://localhost:8000');

const disclaimer = 'DermaCare kozmetik karar destek amaçlı bir araştırma prototipidir. '
    'Hastalık teşhisi koymaz ve tedavi önermez. Tıbbi bir endişeniz varsa dermatoloğa danışın.';
