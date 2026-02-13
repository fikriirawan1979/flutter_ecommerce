import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_theme.dart';
import '../../auth/presentation/providers/auth_provider.dart';

class MainLayout extends ConsumerWidget {
  final Widget child;

  const MainLayout({super.key, required this.child});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authProvider);
    final user = authState.user;
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Scaffold(
      body: Row(
        children: [
          // Sidebar
          Container(
            width: 260,
            decoration: BoxDecoration(
              color: isDark ? AppColors.sidebarDark : AppColors.sidebarLight,
              border: Border(
                right: BorderSide(
                  color: isDark ? AppColors.dividerDark : AppColors.dividerLight,
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
                        child: const Icon(
                          Icons.local_hospital,
                          color: Colors.white,
                          size: 24,
                        ),
                      ),
                      const SizedBox(width: AppSpacing.md),
                      Text(
                        'DentalClinicOS',
                        style: AppTypography.heading4.copyWith(
                          color: isDark
                              ? AppColors.textPrimaryDark
                              : AppColors.textPrimaryLight,
                        ),
                      ),
                    ],
                  ),
                ),
                
                const Divider(height: 1),
                
                // Navigation Items
                Expanded(
                  child: ListView(
                    padding: const EdgeInsets.symmetric(
                      horizontal: AppSpacing.md,
                      vertical: AppSpacing.md,
                    ),
                    children: [
                      _buildSectionTitle('Main'),
                      const SizedBox(height: AppSpacing.sm),
                      _NavItem(
                        icon: Icons.dashboard_outlined,
                        label: 'Dashboard',
                        route: '/',
                        isActive: GoRouterState.of(context).matchedLocation == '/',
                      ),
                      _NavItem(
                        icon: Icons.shopping_cart_outlined,
                        label: 'Assessment Packages',
                        route: '/catalog',
                        isActive: GoRouterState.of(context).matchedLocation == '/catalog',
                      ),
                      
                      if (user?.isPatient ?? false) ...[
                        const SizedBox(height: AppSpacing.lg),
                        _buildSectionTitle('Patient'),
                        const SizedBox(height: AppSpacing.sm),
                        _NavItem(
                          icon: Icons.assignment_outlined,
                          label: 'My Assessments',
                          route: '/assessments',
                          isActive: GoRouterState.of(context).matchedLocation == '/assessments',
                        ),
                        _NavItem(
                          icon: Icons.receipt_long_outlined,
                          label: 'Orders',
                          route: '/orders',
                          isActive: GoRouterState.of(context).matchedLocation == '/orders',
                        ),
                      ],
                      
                      if (user?.isDoctor ?? false) ...[
                        const SizedBox(height: AppSpacing.lg),
                        _buildSectionTitle('Doctor'),
                        const SizedBox(height: AppSpacing.sm),
                        _NavItem(
                          icon: Icons.people_outlined,
                          label: 'Patients',
                          route: '/patients',
                          isActive: GoRouterState.of(context).matchedLocation == '/patients',
                        ),
                        _NavItem(
                          icon: Icons.description_outlined,
                          label: 'Reports',
                          route: '/reports',
                          isActive: GoRouterState.of(context).matchedLocation == '/reports',
                        ),
                      ],
                      
                      if (user?.isAdmin ?? false) ...[
                        const SizedBox(height: AppSpacing.lg),
                        _buildSectionTitle('Admin'),
                        const SizedBox(height: AppSpacing.sm),
                        _NavItem(
                          icon: Icons.manage_accounts_outlined,
                          label: 'Users',
                          route: '/admin/users',
                          isActive: GoRouterState.of(context).matchedLocation == '/admin/users',
                        ),
                        _NavItem(
                          icon: Icons.inventory_2_outlined,
                          label: 'Products',
                          route: '/admin/products',
                          isActive: GoRouterState.of(context).matchedLocation == '/admin/products',
                        ),
                        _NavItem(
                          icon: Icons.analytics_outlined,
                          label: 'Analytics',
                          route: '/admin/analytics',
                          isActive: GoRouterState.of(context).matchedLocation == '/admin/analytics',
                        ),
                      ],
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
                          style: AppTypography.label.copyWith(
                            color: AppColors.primary,
                          ),
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
                                color: isDark
                                    ? AppColors.textPrimaryDark
                                    : AppColors.textPrimaryLight,
                              ),
                              overflow: TextOverflow.ellipsis,
                            ),
                            Text(
                              user?.role.name.toUpperCase() ?? 'PATIENT',
                              style: AppTypography.caption.copyWith(
                                color: AppColors.textSecondaryLight,
                              ),
                            ),
                          ],
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.logout, size: 20),
                        onPressed: () {
                          ref.read(authProvider.notifier).logout();
                        },
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
                    color: isDark ? AppColors.glassDark : AppColors.glassLight,
                    border: Border(
                      bottom: BorderSide(
                        color: isDark ? AppColors.dividerDark : AppColors.dividerLight,
                      ),
                    ),
                  ),
                  child: Row(
                    children: [
                      // Breadcrumbs would go here
                      const Spacer(),
                      // Search Bar
                      Container(
                        width: 300,
                        height: 36,
                        decoration: BoxDecoration(
                          color: isDark ? AppColors.surfaceDark : AppColors.surfaceLight,
                          borderRadius: BorderRadius.circular(AppBorderRadius.medium),
                          border: Border.all(
                            color: isDark ? AppColors.borderDark : AppColors.borderLight,
                          ),
                        ),
                        child: Row(
                          children: [
                            const SizedBox(width: AppSpacing.md),
                            Icon(
                              Icons.search,
                              size: 18,
                              color: isDark
                                  ? AppColors.textSecondaryDark
                                  : AppColors.textSecondaryLight,
                            ),
                            const SizedBox(width: AppSpacing.sm),
                            Expanded(
                              child: TextField(
                                decoration: InputDecoration(
                                  hintText: 'Search...',
                                  hintStyle: AppTypography.bodySmall.copyWith(
                                    color: isDark
                                        ? AppColors.textSecondaryDark
                                        : AppColors.textSecondaryLight,
                                  ),
                                  border: InputBorder.none,
                                  contentPadding: EdgeInsets.zero,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(width: AppSpacing.md),
                      // Notifications
                      IconButton(
                        icon: const Icon(Icons.notifications_outlined),
                        onPressed: () {},
                      ),
                      const SizedBox(width: AppSpacing.sm),
                      // Settings
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
                    color: isDark ? AppColors.backgroundDark : AppColors.backgroundLight,
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
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.xs),
      child: Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(AppBorderRadius.medium),
        child: InkWell(
          onTap: () => context.go(route),
          borderRadius: BorderRadius.circular(AppBorderRadius.medium),
          child: Container(
            padding: const EdgeInsets.symmetric(
              horizontal: AppSpacing.md,
              vertical: AppSpacing.sm + 4,
            ),
            decoration: BoxDecoration(
              color: isActive
                  ? (isDark ? AppColors.sidebarSelectedDark : AppColors.sidebarSelectedLight)
                  : Colors.transparent,
              borderRadius: BorderRadius.circular(AppBorderRadius.medium),
            ),
            child: Row(
              children: [
                Icon(
                  icon,
                  size: 22,
                  color: isActive
                      ? AppColors.primary
                      : (isDark ? AppColors.textSecondaryDark : AppColors.textSecondaryLight),
                ),
                const SizedBox(width: AppSpacing.md),
                Text(
                  label,
                  style: AppTypography.bodyMedium.copyWith(
                    color: isActive
                        ? (isDark ? AppColors.textPrimaryDark : AppColors.textPrimaryLight)
                        : (isDark ? AppColors.textSecondaryDark : AppColors.textSecondaryLight),
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