import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../core/theme/app_theme.dart';
import '../../features/auth/presentation/providers/auth_provider.dart';

class MainLayout extends ConsumerWidget {
  final Widget child;

  const MainLayout({Key? key, required this.child}) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authProvider);
    final user = authState.user;
    final location = GoRouterState.of(context).matchedLocation;
    
    // Role-based menu items
    final menuItems = _getMenuItemsForRole(user?.role ?? 'patient');
    
    return Scaffold(
      body: Row(
        children: [
          // Sidebar
          Container(
            width: 260,
            decoration: BoxDecoration(
              color: Theme.of(context).brightness == Brightness.dark
                  ? AppColors.sidebarDark
                  : AppColors.sidebarLight,
              border: Border(
                right: BorderSide(
                  color: Theme.of(context).brightness == Brightness.dark
                      ? AppColors.dividerDark
                      : AppColors.dividerLight,
                ),
              ),
            ),
            child: Column(
              children: [
                // App Header
                Container(
                  padding: const EdgeInsets.all(AppSpacing.lg),
                  child: Row(
                    children: [
                      Container(
                        width: 40,
                        height: 40,
                        decoration: BoxDecoration(
                          gradient: const LinearGradient(
                            colors: [AppColors.primary, AppColors.primaryLight],
                          ),
                          borderRadius: BorderRadius.circular(AppBorderRadius.medium),
                        ),
                        child: const Icon(Icons.local_hospital, color: Colors.white),
                      ),
                      const SizedBox(width: AppSpacing.md),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'DentalClinicOS',
                              style: AppTypography.heading4.copyWith(
                                color: Theme.of(context).brightness == Brightness.dark
                                    ? AppColors.textPrimaryDark
                                    : AppColors.textPrimaryLight,
                              ),
                              overflow: TextOverflow.ellipsis,
                            ),
                            if (user?.clinicName != null)
                              Text(
                                user!.clinicName!,
                                style: AppTypography.caption.copyWith(
                                  color: AppColors.textSecondaryLight,
                                ),
                                overflow: TextOverflow.ellipsis,
                              ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
                
                const Divider(height: 1),
                
                // Navigation Items
                Expanded(
                  child: ListView(
                    padding: const EdgeInsets.symmetric(horizontal: AppSpacing.md, vertical: AppSpacing.md),
                    children: [
                      _buildSectionTitle('Menu'),
                      const SizedBox(height: AppSpacing.sm),
                      
                      ...menuItems.where((item) => item.category == 'main').map((item) => 
                        _NavItem(
                          icon: item.icon,
                          label: item.label,
                          route: item.route,
                          isActive: location == item.route,
                        )
                      ),
                      
                      const SizedBox(height: AppSpacing.lg),
                      _buildSectionTitle('Settings'),
                      const SizedBox(height: AppSpacing.sm),
                      
                      ...menuItems.where((item) => item.category == 'settings').map((item) => 
                        _NavItem(
                          icon: item.icon,
                          label: item.label,
                          route: item.route,
                          isActive: location == item.route,
                        )
                      ),
                    ],
                  ),
                ),
                
                const Divider(height: 1),
                
                // User Profile
                Container(
                  padding: const EdgeInsets.all(AppSpacing.md),
                  child: Row(
                    children: [
                      CircleAvatar(
                        radius: 18,
                        backgroundColor: AppColors.primary.withOpacity(0.2),
                        child: Text(
                          user?.initials ?? 'U',
                          style: AppTypography.label.copyWith(color: AppColors.primary),
                        ),
                      ),
                      const SizedBox(width: AppSpacing.md),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              user?.fullName ?? 'User',
                              style: AppTypography.bodySmall.copyWith(
                                fontWeight: FontWeight.w600,
                              ),
                              overflow: TextOverflow.ellipsis,
                            ),
                            Text(
                              user?.role.toUpperCase() ?? 'USER',
                              style: AppTypography.caption.copyWith(
                                color: AppColors.textSecondaryLight,
                              ),
                            ),
                          ],
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.logout, size: 20),
                        onPressed: () => ref.read(authProvider.notifier).logout(),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          
          // Main Content
          Expanded(
            child: Column(
              children: [
                // Top Bar
                Container(
                  height: 60,
                  padding: const EdgeInsets.symmetric(horizontal: AppSpacing.lg),
                  decoration: BoxDecoration(
                    color: Theme.of(context).brightness == Brightness.dark
                        ? AppColors.glassDark
                        : AppColors.glassLight,
                    border: Border(
                      bottom: BorderSide(
                        color: Theme.of(context).brightness == Brightness.dark
                            ? AppColors.dividerDark
                            : AppColors.dividerLight,
                      ),
                    ),
                  ),
                  child: Row(
                    children: [
                      Text(
                        _getPageTitle(location),
                        style: AppTypography.heading4,
                      ),
                      const Spacer(),
                      // Language Switcher
                      _LanguageSwitcher(),
                      const SizedBox(width: AppSpacing.md),
                      IconButton(
                        icon: const Icon(Icons.notifications_outlined),
                        onPressed: () {},
                      ),
                      IconButton(
                        icon: const Icon(Icons.settings_outlined),
                        onPressed: () {},
                      ),
                    ],
                  ),
                ),
                
                // Content Area
                Expanded(
                  child: Container(
                    color: Theme.of(context).brightness == Brightness.dark
                        ? AppColors.backgroundDark
                        : AppColors.backgroundLight,
                    child: child,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  List<MenuItem> _getMenuItemsForRole(String role) {
    final items = <MenuItem>[
      MenuItem(
        icon: Icons.dashboard_outlined,
        label: 'Dashboard',
        route: '/dashboard',
        category: 'main',
        roles: ['super_admin', 'clinic_admin', 'doctor', 'patient'],
      ),
      MenuItem(
        icon: Icons.calendar_today_outlined,
        label: 'Reservations',
        route: '/reservation',
        category: 'main',
        roles: ['super_admin', 'clinic_admin', 'doctor', 'patient'],
      ),
      MenuItem(
        icon: Icons.meeting_room_outlined,
        label: 'Reception',
        route: '/reception',
        category: 'main',
        roles: ['super_admin', 'clinic_admin', 'doctor'],
      ),
      MenuItem(
        icon: Icons.medical_services_outlined,
        label: 'Consultation',
        route: '/consultation',
        category: 'main',
        roles: ['super_admin', 'clinic_admin', 'doctor'],
      ),
      MenuItem(
        icon: Icons.account_balance_wallet_outlined,
        label: 'Accounting',
        route: '/accounting',
        category: 'main',
        roles: ['super_admin', 'clinic_admin'],
      ),
      MenuItem(
        icon: Icons.people_outlined,
        label: 'Patients',
        route: '/patients',
        category: 'main',
        roles: ['super_admin', 'clinic_admin', 'doctor'],
      ),
      MenuItem(
        icon: Icons.access_time_outlined,
        label: 'Waiting Monitor',
        route: '/waiting',
        category: 'main',
        roles: ['super_admin', 'clinic_admin', 'doctor', 'patient'],
      ),
      // Settings
      MenuItem(
        icon: Icons.business_outlined,
        label: 'Clinic Settings',
        route: '/settings/clinic',
        category: 'settings',
        roles: ['super_admin', 'clinic_admin'],
      ),
      MenuItem(
        icon: Icons.star_outline,
        label: 'Points Master',
        route: '/settings/points',
        category: 'settings',
        roles: ['super_admin', 'clinic_admin'],
      ),
      MenuItem(
        icon: Icons.question_answer_outlined,
        label: 'Questionnaire',
        route: '/settings/questionnaire',
        category: 'settings',
        roles: ['super_admin', 'clinic_admin'],
      ),
    ];
    
    return items.where((item) => item.roles.contains(role)).toList();
  }

  String _getPageTitle(String location) {
    final titles = {
      '/dashboard': 'Dashboard',
      '/reservation': 'Reservations',
      '/reception': 'Reception',
      '/consultation': 'Consultation Room',
      '/accounting': 'Accounting',
      '/patients': 'Patient Management',
      '/waiting': 'Waiting Monitor',
      '/settings/clinic': 'Clinic Settings',
      '/settings/points': 'Points Master',
      '/settings/questionnaire': 'Questionnaire Settings',
    };
    return titles[location] ?? 'Page';
  }

  Widget _buildSectionTitle(String title) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: AppSpacing.md),
      child: Text(
        title.toUpperCase(),
        style: AppTypography.label.copyWith(
          color: AppColors.textSecondaryLight,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}

class MenuItem {
  final IconData icon;
  final String label;
  final String route;
  final String category;
  final List<String> roles;

  MenuItem({
    required this.icon,
    required this.label,
    required this.route,
    required this.category,
    required this.roles,
  });
}

class _NavItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final String route;
  final bool isActive;

  const _NavItem({
    required this.icon,
    required this.label,
    required this.route,
    this.isActive = false,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.xs),
      child: Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(AppBorderRadius.medium),
        child: InkWell(
          onTap: () => context.go(route),
          borderRadius: BorderRadius.circular(AppBorderRadius.medium),
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: AppSpacing.md, vertical: AppSpacing.sm + 4),
            decoration: BoxDecoration(
              color: isActive
                  ? (Theme.of(context).brightness == Brightness.dark
                      ? AppColors.sidebarSelectedDark
                      : AppColors.sidebarSelectedLight)
                  : Colors.transparent,
              borderRadius: BorderRadius.circular(AppBorderRadius.medium),
            ),
            child: Row(
              children: [
                Icon(
                  icon,
                  size: 22,
                  color: isActive ? AppColors.primary : AppColors.textSecondaryLight,
                ),
                const SizedBox(width: AppSpacing.md),
                Text(
                  label,
                  style: AppTypography.bodyMedium.copyWith(
                    color: isActive
                        ? (Theme.of(context).brightness == Brightness.dark
                            ? AppColors.textPrimaryDark
                            : AppColors.textPrimaryLight)
                        : AppColors.textSecondaryLight,
                    fontWeight: isActive ? FontWeight.w600 : FontWeight.w400,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _LanguageSwitcher extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return PopupMenuButton<String>(
      icon: const Icon(Icons.language),
      tooltip: 'Change Language',
      onSelected: (lang) {
        // Implement language change
      },
      itemBuilder: (context) => [
        const PopupMenuItem(value: 'en', child: Text('English')),
        const PopupMenuItem(value: 'id', child: Text('Bahasa Indonesia')),
      ],
    );
  }
}