import 'package:flutter/material.dart';
import 'package:flutter_web_plugins/flutter_web_plugins.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../features/auth/presentation/providers/auth_provider.dart';
import '../features/dashboard/presentation/screens/main_layout.dart';
import '../features/auth/presentation/screens/login_screen.dart';
import '../features/dashboard/presentation/screens/dashboard_screen.dart';
import '../features/reservation/presentation/screens/reservation_screen.dart';
import '../features/reception/presentation/screens/reception_screen.dart';
import '../features/consultation/presentation/screens/consultation_screen.dart';
import '../features/accounting/presentation/screens/accounting_screen.dart';
import '../features/patients/presentation/screens/patients_screen.dart';
import '../features/waiting/presentation/screens/waiting_screen.dart';
import '../features/settings/presentation/screens/settings_screen.dart';

void configureApp() {
  setUrlStrategy(PathUrlStrategy());
}

final routerProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authProvider);
  
  return GoRouter(
    initialLocation: '/login',
    debugLogDiagnostics: true,
    redirect: (context, state) {
      final isAuthenticated = authState.isAuthenticated;
      final isLoggingIn = state.matchedLocation == '/login';
      
      if (!isAuthenticated && !isLoggingIn) {
        return '/login';
      }
      
      if (isAuthenticated && isLoggingIn) {
        return '/dashboard';
      }
      
      return null;
    },
    routes: [
      // Public route
      GoRoute(
        path: '/login',
        builder: (context, state) => const LoginScreen(),
      ),
      
      // Protected routes with MainLayout
      ShellRoute(
        builder: (context, state, child) => MainLayout(child: child),
        routes: [
          // Dashboard
          GoRoute(
            path: '/dashboard',
            builder: (context, state) => const DashboardScreen(),
          ),
          
          // Main Menu Routes
          GoRoute(
            path: '/reservation',
            builder: (context, state) => const ReservationScreen(),
          ),
          GoRoute(
            path: '/reception',
            builder: (context, state) => const ReceptionScreen(),
          ),
          GoRoute(
            path: '/consultation',
            builder: (context, state) => const ConsultationScreen(),
          ),
          GoRoute(
            path: '/accounting',
            builder: (context, state) => const AccountingScreen(),
          ),
          GoRoute(
            path: '/patients',
            builder: (context, state) => const PatientsScreen(),
          ),
          GoRoute(
            path: '/waiting',
            builder: (context, state) => const WaitingScreen(),
          ),
          
          // Settings Routes
          GoRoute(
            path: '/settings/clinic',
            builder: (context, state) => const SettingsScreen(type: 'clinic'),
          ),
          GoRoute(
            path: '/settings/points',
            builder: (context, state) => const SettingsScreen(type: 'points'),
          ),
          GoRoute(
            path: '/settings/questionnaire',
            builder: (context, state) => const SettingsScreen(type: 'questionnaire'),
          ),
          
          // Catch-all for unknown routes
          GoRoute(
            path: '/:path(.*)',
            builder: (context, state) => const NotFoundScreen(),
          ),
        ],
      ),
    ],
    errorBuilder: (context, state) => const NotFoundScreen(),
  );
});

class NotFoundScreen extends StatelessWidget {
  const NotFoundScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 64, color: Colors.grey),
            const SizedBox(height: 16),
            const Text(
              '404 - Page Not Found',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: () => context.go('/dashboard'),
              child: const Text('Go to Dashboard'),
            ),
          ],
        ),
      ),
    );
  }
}