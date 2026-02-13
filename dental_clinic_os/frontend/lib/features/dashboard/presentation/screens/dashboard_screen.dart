import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/theme/app_theme.dart';

class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      backgroundColor: AppColors.backgroundLight,
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(AppSpacing.xl),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Dashboard',
              style: AppTypography.heading2.copyWith(
                color: AppColors.textPrimaryLight,
              ),
            ),
            const SizedBox(height: AppSpacing.xl),
            
            // Stats Cards
            Row(
              children: [
                _StatCard(
                  title: 'Today\'s Appointments',
                  value: '12',
                  icon: Icons.calendar_today,
                  color: AppColors.primary,
                ),
                const SizedBox(width: AppSpacing.lg),
                _StatCard(
                  title: 'Waiting Patients',
                  value: '5',
                  icon: Icons.access_time,
                  color: AppColors.warning,
                ),
                const SizedBox(width: AppSpacing.lg),
                _StatCard(
                  title: 'Completed',
                  value: '8',
                  icon: Icons.check_circle,
                  color: AppColors.success,
                ),
              ],
            ),
            
            const SizedBox(height: AppSpacing.xl),
            
            // Recent Activity
            Container(
              padding: const EdgeInsets.all(AppSpacing.lg),
              decoration: BoxDecoration(
                color: AppColors.cardLight,
                borderRadius: BorderRadius.circular(AppBorderRadius.large),
                boxShadow: [AppShadows.small],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Recent Activity',
                    style: AppTypography.heading4,
                  ),
                  const SizedBox(height: AppSpacing.lg),
                  const ListTile(
                    leading: Icon(Icons.person_add, color: AppColors.primary),
                    title: Text('New patient registered'),
                    subtitle: Text('John Doe - 10:30 AM'),
                  ),
                  const Divider(),
                  const ListTile(
                    leading: Icon(Icons.check_circle, color: AppColors.success),
                    title: Text('Appointment completed'),
                    subtitle: Text('Jane Smith - 09:15 AM'),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _StatCard extends StatelessWidget {
  final String title;
  final String value;
  final IconData icon;
  final Color color;

  const _StatCard({
    required this.title,
    required this.value,
    required this.icon,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(AppSpacing.lg),
        decoration: BoxDecoration(
          color: AppColors.cardLight,
          borderRadius: BorderRadius.circular(AppBorderRadius.large),
          boxShadow: [AppShadows.small],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  title,
                  style: AppTypography.bodySmall.copyWith(
                    color: AppColors.textSecondaryLight,
                  ),
                ),
                Container(
                  padding: const EdgeInsets.all(AppSpacing.sm),
                  decoration: BoxDecoration(
                    color: color.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(AppBorderRadius.medium),
                  ),
                  child: Icon(icon, color: color, size: 20),
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.md),
            Text(
              value,
              style: AppTypography.heading1.copyWith(
                color: AppColors.textPrimaryLight,
              ),
            ),
          ],
        ),
      ),
    );
  }
}