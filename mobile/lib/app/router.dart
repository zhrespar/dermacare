import 'package:go_router/go_router.dart';

import '../features/analysis/quality_check_screen.dart';
import '../features/auth/auth_screen.dart';
import '../features/capture/capture_screen.dart';
import '../features/history/history_screen.dart';
import '../features/products/products_screen.dart';
import '../features/profile/profile_screen.dart';
import '../features/results/results_screen.dart';
import '../features/routine/routine_screen.dart';
import '../features/welcome/welcome_screen.dart';
import 'routes.dart';
import 'state.dart';

GoRouter buildRouter(AppState state) => GoRouter(
      initialLocation: Routes.welcome,
      refreshListenable: state,
      redirect: (_, s) {
        final open = s.matchedLocation == Routes.welcome || s.matchedLocation == Routes.auth;
        return !state.signedIn && !open ? Routes.auth : null;
      },
      routes: [
        GoRoute(path: Routes.welcome, builder: (_, __) => const WelcomeScreen()),
        GoRoute(path: Routes.auth, builder: (_, __) => const AuthScreen()),
        GoRoute(path: Routes.profile, builder: (_, __) => const ProfileScreen()),
        GoRoute(path: Routes.capture, builder: (_, __) => const CaptureScreen()),
        GoRoute(path: Routes.quality, builder: (_, __) => const QualityCheckScreen()),
        GoRoute(path: Routes.results, builder: (_, __) => const ResultsScreen()),
        GoRoute(path: Routes.routine, builder: (_, __) => const RoutineScreen()),
        GoRoute(path: Routes.products, builder: (_, __) => const ProductsScreen()),
        GoRoute(path: Routes.history, builder: (_, __) => const HistoryScreen()),
      ],
    );
