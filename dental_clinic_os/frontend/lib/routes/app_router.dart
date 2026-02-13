import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';
import '../../features/auth/presentation/providers/auth_provider.dart';
import '../../features/auth/presentation/screens/login_screen.dart';
import '../../features/dashboard/presentation/screens/main_layout.dart';
import '../../features/ecommerce/presentation/screens/product_catalog_screen.dart';
import '../../features/dashboard/presentation/screens/patient_dashboard_screen.dart';
import '../../features/dashboard/presentation/screens/doctor_dashboard_screen.dart';
import '../../features/dashboard/presentation/screens/admin_dashboard_screen.dart';

part 'app_router.g.dart';

@riverpod
GoRouter appRouter(AppRouterRef ref) {
  final authState = ref.watch(authProvider);
  
  return GoRouter(
    initialLocation: '/',
    debugLogDiagnostics: true,
    redirect: (context, state) {
      final isAuthenticated = authState.isAuthenticated;
      final isLoginRoute = state.matchedLocation == '/login';
      
      if (!isAuthenticated && !isLoginRoute) {
        return '/login';
      }
      
      if (isAuthenticated && isLoginRoute) {
        return '/';
      }
      
      return null;
    },
    refreshListenable: authStateNotifierProvider,
    routes: [
      GoRoute(
        path: '/login',
        builder: (context, state) => const LoginScreen(),
      ),
      ShellRoute(
        builder: (context, state, child) => MainLayout(child: child),
        routes: [
          GoRoute(
            path: '/',
            builder: (context, state) {
              final userRole = authState.user?.role;
              switch (userRole) {
                case 'doctor':
                  return const DoctorDashboardScreen();
                case 'admin':
                  return const AdminDashboardScreen();
                case 'patient':
                default:
                  return const PatientDashboardScreen();
              }
            },
          ),
          GoRoute(
            path: '/catalog',
            builder: (context, state) => const ProductCatalogScreen(),
          ),
          GoRoute(
            path: '/assessments',
            builder: (context, state) => const PatientDashboardScreen(),
          ),
          GoRoute(
            path: '/orders',
            builder: (context, state) => const PatientDashboardScreen(),
          ),
          GoRoute(
            path: '/patients',
            builder: (context, state) => const DoctorDashboardScreen(),
          ),
          GoRoute(
            path: '/reports',
            builder: (context, state) => const DoctorDashboardScreen(),
          ),
          GoRoute(
            path: '/admin/users',
            builder: (context, state) => const AdminDashboardScreen(),
          ),
          GoRoute(
            path: '/admin/products',
            builder: (context, state) => const AdminDashboardScreen(),
          ),
          GoRoute(
            path: '/admin/analytics',
            builder: (context, state) => const AdminDashboardScreen(),
          ),
        ],
      ),
    ],
  );
}

// Custom ChangeNotifier for router refresh
final authStateNotifierProvider = ChangeNotifierProvider<AuthStateNotifier>((ref) {
  return AuthStateNotifier(ref);
});

class AuthStateNotifier extends ChangeNotifier {
  final Ref ref;
  
  AuthStateNotifier(this.ref) {
    ref.listen(authProvider, (_, __) => notifyListeners());
  }
}