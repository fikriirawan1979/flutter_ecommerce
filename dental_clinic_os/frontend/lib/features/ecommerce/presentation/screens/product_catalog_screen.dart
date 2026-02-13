import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/theme/app_theme.dart';
import '../widgets/product_card.dart';
import '../../domain/entities/product_entity.dart';

// Mock products for demo
final mockProducts = [
  const ProductEntity(
    id: '1',
    name: 'Basic Dental Assessment',
    description: 'Comprehensive oral examination with basic diagnostic imaging',
    price: 149.00,
    features: ['Oral examination', '2D X-ray imaging', 'Basic report'],
  ),
  const ProductEntity(
    id: '2',
    name: 'Advanced Cephalometric Analysis',
    description: 'Complete cephalometric analysis with AI-assisted measurements',
    price: 299.00,
    features: ['Cephalometric tracing', 'Skeletal analysis', 'Treatment planning', 'PDF report'],
  ),
  const ProductEntity(
    id: '3',
    name: 'Full Orthodontic Package',
    description: 'Complete orthodontic assessment including 3D imaging and treatment simulation',
    price: 499.00,
    features: ['3D imaging', 'Cephalometric analysis', 'Treatment simulation', 'Progress tracking', 'Priority support'],
  ),
  const ProductEntity(
    id: '4',
    name: 'TMJ Assessment',
    description: 'Specialized temporomandibular joint evaluation and treatment recommendations',
    price: 199.00,
    features: ['TMJ examination', 'Joint imaging', 'Bite analysis', 'Treatment options'],
  ),
  const ProductEntity(
    id: '5',
    name: 'Sleep Apnea Screening',
    description: 'Dental sleep medicine assessment for sleep-related breathing disorders',
    price: 249.00,
    features: ['Airway assessment', 'Sleep screening', 'Oral appliance consultation', 'Referral coordination'],
  ),
  const ProductEntity(
    id: '6',
    name: 'Pediatric Dental Assessment',
    description: 'Child-friendly dental evaluation with growth and development analysis',
    price: 129.00,
    features: ['Child-friendly exam', 'Growth analysis', 'Habit assessment', 'Parent consultation'],
  ),
];

class ProductCatalogScreen extends ConsumerWidget {
  const ProductCatalogScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      backgroundColor: isDark ? AppColors.backgroundDark : AppColors.backgroundLight,
      body: Padding(
        padding: const EdgeInsets.all(AppSpacing.xl),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Assessment Packages',
                      style: AppTypography.heading2.copyWith(
                        color: isDark
                            ? AppColors.textPrimaryDark
                            : AppColors.textPrimaryLight,
                      ),
                    ),
                    const SizedBox(height: AppSpacing.xs),
                    Text(
                      'Choose the right assessment package for your needs',
                      style: AppTypography.bodyLarge.copyWith(
                        color: AppColors.textSecondaryLight,
                      ),
                    ),
                  ],
                ),
                // Filter chips
                Row(
                  children: [
                    _FilterChip(label: 'All', isActive: true, onTap: () {}),
                    const SizedBox(width: AppSpacing.sm),
                    _FilterChip(label: 'Basic', isActive: false, onTap: () {}),
                    const SizedBox(width: AppSpacing.sm),
                    _FilterChip(label: 'Advanced', isActive: false, onTap: () {}),
                  ],
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.xl),
            
            // Products Grid
            Expanded(
              child: GridView.builder(
                gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 3,
                  crossAxisSpacing: AppSpacing.lg,
                  mainAxisSpacing: AppSpacing.lg,
                  childAspectRatio: 0.85,
                ),
                itemCount: mockProducts.length,
                itemBuilder: (context, index) {
                  return ProductCard(product: mockProducts[index]);
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _FilterChip extends StatelessWidget {
  final String label;
  final bool isActive;
  final VoidCallback onTap;

  const _FilterChip({
    required this.label,
    required this.isActive,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(AppBorderRadius.medium),
      child: Container(
        padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.md,
          vertical: AppSpacing.sm,
        ),
        decoration: BoxDecoration(
          color: isActive
              ? AppColors.primary
              : (isDark ? AppColors.surfaceDark : AppColors.surfaceLight),
          borderRadius: BorderRadius.circular(AppBorderRadius.medium),
          border: Border.all(
            color: isActive
                ? AppColors.primary
                : (isDark ? AppColors.borderDark : AppColors.borderLight),
          ),
        ),
        child: Text(
          label,
          style: AppTypography.bodySmall.copyWith(
            color: isActive
                ? Colors.white
                : (isDark ? AppColors.textSecondaryDark : AppColors.textSecondaryLight),
            fontWeight: isActive ? FontWeight.w600 : FontWeight.w400,
          ),
        ),
      ),
    );
  }
}