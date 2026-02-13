import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:dio/dio.dart';
import '../domain/entities/user_entity.dart';
import '../domain/entities/auth_tokens.dart';
import '../../shared/utils/logger.dart';

part 'auth_provider.g.dart';

@riverpod
class Auth extends _$Auth {
  final Dio _dio = Dio(BaseOptions(
    baseUrl: 'http://localhost:8000/api/v1',
    connectTimeout: const Duration(seconds: 5),
    receiveTimeout: const Duration(seconds: 3),
  ));

  @override
  AuthState build() {
    _initializeAuth();
    return const AuthState();
  }

  Future<void> _initializeAuth() async {
    // TODO: Load tokens from secure storage
    // For now, start unauthenticated
  }

  Future<void> login({required String email, required String password}) async {
    try {
      state = state.copyWith(isLoading: true, error: null);

      final response = await _dio.post('/auth/login', data: {
        'email': email,
        'password': password,
      });

      final tokens = AuthTokens.fromJson(response.data['tokens']);
      final user = UserEntity.fromJson(response.data['user']);

      state = state.copyWith(
        user: user,
        tokens: tokens,
        isLoading: false,
        isAuthenticated: true,
      );

      // TODO: Save tokens to secure storage
    } on DioException catch (e) {
      AppLogger.error('Login failed', e);
      state = state.copyWith(
        isLoading: false,
        error: e.response?.data['message'] ?? 'Login failed',
      );
    } catch (e) {
      AppLogger.error('Unexpected error during login', e);
      state = state.copyWith(
        isLoading: false,
        error: 'An unexpected error occurred',
      );
    }
  }

  Future<void> register({
    required String email,
    required String password,
    required String firstName,
    required String lastName,
    String? phone,
  }) async {
    try {
      state = state.copyWith(isLoading: true, error: null);

      final response = await _dio.post('/auth/register', data: {
        'email': email,
        'password': password,
        'first_name': firstName,
        'last_name': lastName,
        'phone': phone,
      });

      final tokens = AuthTokens.fromJson(response.data['tokens']);
      final user = UserEntity.fromJson(response.data['user']);

      state = state.copyWith(
        user: user,
        tokens: tokens,
        isLoading: false,
        isAuthenticated: true,
      );
    } on DioException catch (e) {
      AppLogger.error('Registration failed', e);
      state = state.copyWith(
        isLoading: false,
        error: e.response?.data['message'] ?? 'Registration failed',
      );
    } catch (e) {
      AppLogger.error('Unexpected error during registration', e);
      state = state.copyWith(
        isLoading: false,
        error: 'An unexpected error occurred',
      );
    }
  }

  Future<void> logout() async {
    try {
      // TODO: Call logout endpoint if needed
      // await _dio.post('/auth/logout');
    } catch (e) {
      AppLogger.error('Logout error', e);
    } finally {
      state = const AuthState();
      // TODO: Clear secure storage
    }
  }

  Future<void> refreshToken() async {
    if (state.tokens == null) return;

    try {
      final response = await _dio.post('/auth/refresh', data: {
        'refresh_token': state.tokens!.refreshToken,
      });

      final tokens = AuthTokens.fromJson(response.data);
      state = state.copyWith(tokens: tokens);

      // TODO: Update secure storage
    } catch (e) {
      AppLogger.error('Token refresh failed', e);
      await logout();
    }
  }
}

class AuthState {
  final UserEntity? user;
  final AuthTokens? tokens;
  final bool isLoading;
  final bool isAuthenticated;
  final String? error;

  const AuthState({
    this.user,
    this.tokens,
    this.isLoading = false,
    this.isAuthenticated = false,
    this.error,
  });

  AuthState copyWith({
    UserEntity? user,
    AuthTokens? tokens,
    bool? isLoading,
    bool? isAuthenticated,
    String? error,
  }) {
    return AuthState(
      user: user ?? this.user,
      tokens: tokens ?? this.tokens,
      isLoading: isLoading ?? this.isLoading,
      isAuthenticated: isAuthenticated ?? this.isAuthenticated,
      error: error,
    );
  }
}