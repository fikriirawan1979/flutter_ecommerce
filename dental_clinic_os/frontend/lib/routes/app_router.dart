import 'package:flutter/material.dart';
import 'package:flutter_web_plugins/flutter_web_plugins.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

// Auth Provider
final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  return AuthNotifier();
});

class AuthState {
  final bool isAuthenticated;
  final UserRole? role;
  final String? tenantId;

  const AuthState({
    this.isAuthenticated = false,
    this.role,
    this.tenantId,
  });

  AuthState copyWith({
    bool? isAuthenticated,
    UserRole? role,
    String? tenantId,
  }) {
    return AuthState(
      isAuthenticated: isAuthenticated ?? this.isAuthenticated,
      role: role ?? this.role,
      tenantId: tenantId ?? this.tenantId,
    );
  }
}

enum UserRole { patient, doctor, admin, superAdmin }

class AuthNotifier extends StateNotifier<AuthState> {
  AuthNotifier() : super(const AuthState());

  void login(UserRole role, String tenantId) {
    state = AuthState(isAuthenticated: true, role: role, tenantId: tenantId);
  }

  void logout() {
    state = const AuthState();
  }
}

void configureApp() {
  setUrlStrategy(PathUrlStrategy());
}

final appRouterProvider = Provider<GoRouter>((ref) {
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

// ==================== SCREEN WIDGETS ====================

class LoginScreen extends ConsumerWidget {
  const LoginScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final emailController = TextEditingController();
    final passwordController = TextEditingController();

    return Scaffold(
      body: Center(
        child: Container(
          constraints: const BoxConstraints(maxWidth: 400),
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Icon(Icons.local_hospital, size: 64, color: Colors.blue),
              const SizedBox(height: 24),
              const Text(
                'DentalClinicOS',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              const Text(
                'Sign in to your account',
                textAlign: TextAlign.center,
                style: TextStyle(color: Colors.grey),
              ),
              const SizedBox(height: 32),
              TextField(
                controller: emailController,
                decoration: const InputDecoration(
                  labelText: 'Email',
                  prefixIcon: Icon(Icons.email),
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: passwordController,
                obscureText: true,
                decoration: const InputDecoration(
                  labelText: 'Password',
                  prefixIcon: Icon(Icons.lock),
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 24),
              ElevatedButton(
                onPressed: () {
                  ref.read(authProvider.notifier).login(UserRole.admin, 'demo-tenant');
                  context.go('/dashboard');
                },
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                ),
                child: const Text('Sign In'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class MainLayout extends ConsumerWidget {
  final Widget child;

  const MainLayout({Key? key, required this.child}) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('DentalClinicOS'),
        actions: [
          if (authState.isAuthenticated)
            IconButton(
              icon: const Icon(Icons.logout),
              onPressed: () {
                ref.read(authProvider.notifier).logout();
                context.go('/login');
              },
            ),
        ],
      ),
      body: Row(
        children: [
          NavigationRail(
            extended: MediaQuery.of(context).size.width > 800,
            selectedIndex: _getSelectedIndex(context),
            onDestinationSelected: (index) => _onNavigate(context, index),
            destinations: const [
              NavigationRailDestination(
                icon: Icon(Icons.dashboard),
                label: Text('Dashboard'),
              ),
              NavigationRailDestination(
                icon: Icon(Icons.calendar_today),
                label: Text('Reservation'),
              ),
              NavigationRailDestination(
                icon: Icon(Icons.reception),
                label: Text('Reception'),
              ),
              NavigationRailDestination(
                icon: Icon(Icons.medical_services),
                label: Text('Consultation'),
              ),
              NavigationRailDestination(
                icon: Icon(Icons.account_balance_wallet),
                label: Text('Accounting'),
              ),
              NavigationRailDestination(
                icon: Icon(Icons.people),
                label: Text('Patients'),
              ),
              NavigationRailDestination(
                icon: Icon(Icons.access_time),
                label: Text('Waiting'),
              ),
              NavigationRailDestination(
                icon: Icon(Icons.settings),
                label: Text('Settings'),
              ),
            ],
          ),
          const VerticalDivider(thickness: 1, width: 1),
          Expanded(child: child),
        ],
      ),
    );
  }

  int _getSelectedIndex(BuildContext context) {
    final location = GoRouterState.of(context).matchedLocation;
    if (location.startsWith('/dashboard')) return 0;
    if (location.startsWith('/reservation')) return 1;
    if (location.startsWith('/reception')) return 2;
    if (location.startsWith('/consultation')) return 3;
    if (location.startsWith('/accounting')) return 4;
    if (location.startsWith('/patients')) return 5;
    if (location.startsWith('/waiting')) return 6;
    if (location.startsWith('/settings')) return 7;
    return 0;
  }

  void _onNavigate(BuildContext context, int index) {
    final routes = [
      '/dashboard',
      '/reservation',
      '/reception',
      '/consultation',
      '/accounting',
      '/patients',
      '/waiting',
      '/settings/clinic',
    ];
    context.go(routes[index]);
  }
}

class DashboardScreen extends StatelessWidget {
  const DashboardScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Dashboard',
            style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 24),
          Wrap(
            spacing: 16,
            runSpacing: 16,
            children: [
              _buildStatCard('Total Patients', '124', Icons.people, Colors.blue),
              _buildStatCard('Today\'s Appointments', '8', Icons.calendar_today, Colors.green),
              _buildStatCard('Pending Assessments', '3', Icons.assignment, Colors.orange),
              _buildStatCard('Revenue This Month', '\$12,450', Icons.attach_money, Colors.purple),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildStatCard(String title, String value, IconData icon, Color color) {
    return Card(
      child: Container(
        width: 200,
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, color: color, size: 32),
            const SizedBox(height: 8),
            Text(value, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
            const SizedBox(height: 4),
            Text(title, style: const TextStyle(color: Colors.grey)),
          ],
        ),
      ),
    );
  }
}

class ReservationScreen extends StatelessWidget {
  const ReservationScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return const Center(child: Text('Reservation Screen', style: TextStyle(fontSize: 24)));
  }
}

class ReceptionScreen extends StatelessWidget {
  const ReceptionScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return const Center(child: Text('Reception Screen', style: TextStyle(fontSize: 24)));
  }
}

class ConsultationScreen extends StatelessWidget {
  const ConsultationScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return const Center(child: Text('Consultation Screen', style: TextStyle(fontSize: 24)));
  }
}

class AccountingScreen extends StatelessWidget {
  const AccountingScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return const Center(child: Text('Accounting Screen', style: TextStyle(fontSize: 24)));
  }
}

class PatientsScreen extends StatelessWidget {
  const PatientsScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return const Center(child: Text('Patients Screen', style: TextStyle(fontSize: 24)));
  }
}

class WaitingScreen extends StatelessWidget {
  const WaitingScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return const Center(child: Text('Waiting Monitor Screen', style: TextStyle(fontSize: 24)));
  }
}

class SettingsScreen extends StatelessWidget {
  final String type;

  const SettingsScreen({Key? key, required this.type}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final title = {
      'clinic': 'Clinic Settings',
      'points': 'Points Master',
      'questionnaire': 'Questionnaire Settings',
    }[type] ?? 'Settings';

    return Center(child: Text(title, style: const TextStyle(fontSize: 24)));
  }
}

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