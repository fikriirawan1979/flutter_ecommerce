import 'package:riverpod_annotation/riverpod_annotation.dart';
import '../../domain/entities/product_entity.dart';

part 'cart_provider.g.dart';

@riverpod
class Cart extends _$Cart {
  @override
  CartState build() {
    return const CartState();
  }

  void addItem(ProductEntity product) {
    final existingIndex = state.items.indexWhere(
      (item) => item.product.id == product.id,
    );

    if (existingIndex >= 0) {
      // Item already exists, increment quantity
      final updatedItems = List<CartItem>.from(state.items);
      updatedItems[existingIndex] = updatedItems[existingIndex].copyWith(
        quantity: updatedItems[existingIndex].quantity + 1,
      );
      state = state.copyWith(items: updatedItems);
    } else {
      // Add new item
      state = state.copyWith(
        items: [...state.items, CartItem(product: product)],
      );
    }
  }

  void removeItem(String productId) {
    state = state.copyWith(
      items: state.items.where((item) => item.product.id != productId).toList(),
    );
  }

  void updateQuantity(String productId, int quantity) {
    if (quantity <= 0) {
      removeItem(productId);
      return;
    }

    final updatedItems = state.items.map((item) {
      if (item.product.id == productId) {
        return item.copyWith(quantity: quantity);
      }
      return item;
    }).toList();

    state = state.copyWith(items: updatedItems);
  }

  void clear() {
    state = const CartState();
  }

  double get total => state.items.fold(
        0,
        (sum, item) => sum + (item.product.price * item.quantity),
      );
}

class CartState {
  final List<CartItem> items;

  const CartState({this.items = const []});

  CartState copyWith({List<CartItem>? items}) {
    return CartState(items: items ?? this.items);
  }

  double get total => items.fold(
        0,
        (sum, item) => sum + (item.product.price * item.quantity),
      );

  String get formattedTotal => '\$${total.toStringAsFixed(2)}';

  int get itemCount => items.fold(0, (sum, item) => sum + item.quantity);
}

class CartItem {
  final ProductEntity product;
  final int quantity;

  const CartItem({
    required this.product,
    this.quantity = 1,
  });

  CartItem copyWith({ProductEntity? product, int? quantity}) {
    return CartItem(
      product: product ?? this.product,
      quantity: quantity ?? this.quantity,
    );
  }
}