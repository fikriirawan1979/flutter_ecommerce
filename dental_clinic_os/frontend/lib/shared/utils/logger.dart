import 'dart:developer' as developer;

class AppLogger {
  static void info(String message) {
    developer.log('[INFO] $message', name: 'DentalClinicOS');
  }

  static void warning(String message) {
    developer.log('[WARN] $message', name: 'DentalClinicOS');
  }

  static void error(String message, [Object? error, StackTrace? stackTrace]) {
    developer.log(
      '[ERROR] $message',
      name: 'DentalClinicOS',
      error: error,
      stackTrace: stackTrace,
    );
  }

  static void debug(String message) {
    developer.log('[DEBUG] $message', name: 'DentalClinicOS');
  }
}