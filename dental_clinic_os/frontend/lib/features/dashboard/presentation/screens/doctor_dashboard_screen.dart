import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/theme/app_theme.dart';

class DoctorDashboardScreen extends ConsumerWidget {
  const DoctorDashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      backgroundColor: isDark ? AppColors.backgroundDark : AppColors.backgroundLight,
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(AppSpacing.xl),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Doctor Dashboard',
              style: AppTypography.heading2.copyWith(
                color: isDark ? AppColors.textPrimaryDark : AppColors.textPrimaryLight,
              ),
            ),
            const SizedBox(height: AppSpacing.xs),
            Text(
              'Manage patient assessments and reviews',
              style: AppTypography.bodyLarge.copyWith(
                color: AppColors.textSecondaryLight,
              ),
            ),
            const SizedBox(height: AppSpacing.xl),
            
            // Stats
            Row(
              children: [
                Expanded(
                  child: _StatCard(
                    title: 'Pending Review',
                    value: '8',
                    subtitle: 'Need your attention',
                    icon: Icons.pending_actions,
                    color: AppColors.warning,
                  ),
                ),
                const SizedBox(width: AppSpacing.lg),
                Expanded(
                  child: _StatCard(
                    title: 'Reviewed Today',
                    value: '12',
                    subtitle: 'Assessments completed',
                    icon: Icons.check_circle,
                    color: AppColors.success,
                  ),
                ),
                const SizedBox(width: AppSpacing.lg),
                Expanded(
                  child: _StatCard(
                    title: 'Total Patients',
                    value: '156',
                    subtitle: 'Active cases',
                    icon: Icons.people,
                    color: AppColors.info,
                  ),
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.xl),
            
            // Pending Assessments Table
            Container(
              padding: const EdgeInsets.all(AppSpacing.lg),
              decoration: BoxDecoration(
                color: isDark ? AppColors.cardDark : AppColors.cardLight,
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
                        'Pending Assessments',
                        style: AppTypography.heading4.copyWith(
                          color: isDark ? AppColors.textPrimaryDark : AppColors.textPrimaryLight,
                        ),
                      ),
                      TextButton(
                        onPressed: () {},
                        child: const Text('View All'),
                      ),
                    ],
                  ),
                  const SizedBox(height: AppSpacing.lg),
                  _AssessmentTableHeader(),
                  const Divider(),
                  _AssessmentTableRow(
                    patientName: 'John Smith',
                    assessmentType: 'Cephalometric Analysis',
                    submittedDate: 'Feb 12, 2024',
                    priority: 'High',
                  ),
                  const Divider(),
                  _AssessmentTableRow(
                    patientName: 'Sarah Johnson',
                    assessmentType: 'TMJ Assessment',
                    submittedDate: 'Feb 12, 2024',
                    priority: 'Normal',
                  ),
                  const Divider(),
                  _AssessmentTableRow(
                    patientName: 'Michael Brown',
                    assessmentType: 'Orthodontic Package',
                    submittedDate: 'Feb 11, 2024',
                    priority: 'High',
                  ),
                  const Divider(),
                  _AssessmentTableRow(
                    patientName: 'Emily Davis',
                    assessmentType: 'Basic Checkup',
                    submittedDate: 'Feb 11, 2024',
                    priority: 'Normal',
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
  final String subtitle;
  final IconData icon;
  final Color color;

  const _StatCard({
    required this.title,
    required this.value,
    required this.subtitle,
    required this.icon,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Container(
      padding: const EdgeInsets.all(AppSpacing.lg),
      decoration: BoxDecoration(
        color: isDark ? AppColors.cardDark : AppColors.cardLight,
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
              color: isDark ? AppColors.textPrimaryDark : AppColors.textPrimaryLight,
            ),
          ),
          const SizedBox(height: AppSpacing.xs),
          Text(
            subtitle,
            style: AppTypography.bodySmall.copyWith(
              color: AppColors.textSecondaryLight,
            ),
          ),
        ],
      ),
    );
  }
}

class _AssessmentTableHeader extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: AppSpacing.sm),
      child: Row(
        children: [
          Expanded(
            flex: 2,
            child: Text(
              'Patient',
              style: AppTypography.label.copyWith(
                color: AppColors.textSecondaryLight,
              ),
            ),
          ),
          Expanded(
            flex: 2,
            child: Text(
              'Assessment Type',
              style: AppTypography.label.copyWith(
                color: AppColors.textSecondaryLight,
              ),
            ),
          ),
          Expanded(
            child: Text(
              'Date',
              style: AppTypography.label.copyWith(
                color: AppColors.textSecondaryLight,
              ),
            ),
          ),
          Expanded(
            child: Text(
              'Priority',
              style: AppTypography.label.copyWith(
                color: AppColors.textSecondaryLight,
              ),
            ),
          ),
          SizedBox(width: 100),
        ],
      ),
    );
  }
}

class _AssessmentTableRow extends StatelessWidget {
  final String patientName;
  final String assessmentType;
  final String submittedDate;
  final String priority;

  const _AssessmentTableRow({
    required this.patientName,
    required this.assessmentType,
    required this.submittedDate,
    required this.priority,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final priorityColor = priority == 'High' ? AppColors.error : AppColors.success;

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: AppSpacing.md),
      child: Row(
        children: [
          Expanded(
            flex: 2,
            child: Row(
              children: [
                CircleAvatar(
                  radius: 16,
                  backgroundColor: AppColors.primary.withOpacity(0.2),
                  child: Text(
                    patientName.split(' ').map((e) => e[0]).join(),
                    style: AppTypography.label.copyWith(color: AppColors.primary),
                  ),
                ),
                const SizedBox(width: AppSpacing.md),
                Text(
                  patientName,
                  style: AppTypography.bodyMedium.copyWith(
                    color: isDark ? AppColors.textPrimaryDark : AppColors.textPrimaryLight,
                  ),
                ),
              ],
            ),
          ),
          Expanded(
            flex: 2,
            child: Text(
              assessmentType,
              style: AppTypography.bodySmall.copyWith(
                color: AppColors.textSecondaryLight,
              ),
            ),
          ),
          Expanded(
            child: Text(
              submittedDate,
              style: AppTypography.bodySmall.copyWith(
                color: AppColors.textSecondaryLight,
              ),
            ),
          ),
          Expanded(
            child: Container(
              padding: const EdgeInsets.symmetric(
                horizontal: AppSpacing.md,
                vertical: AppSpacing.xs,
              ),
              decoration: BoxDecoration(
                color: priorityColor.withOpacity(0.1),
                borderRadius: BorderRadius.circular(AppBorderRadius.medium),
              ),
              child: Text(
                priority,
                style: AppTypography.label.copyWith(color: priorityColor),
              ),
            ),
          ),
          SizedBox(
            width: 100,
            child: ElevatedButton(
              onPressed: () {},
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(horizontal: AppSpacing.md),
              ),
              child: const Text('Review'),
            ),
          ),
        ],
      ),
    );
  }
}