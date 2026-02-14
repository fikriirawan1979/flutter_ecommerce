import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

abstract class AppLocalizations {
  AppLocalizations(String locale) : localeName = Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations? _current;

  static AppLocalizations get current => _current!;

  static AppLocalizations of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations)!;
  }

  static Future<AppLocalizations> load(Locale locale) async {
    final name = locale.countryCode?.isEmpty == false
        ? '${locale.languageCode}_${locale.countryCode}'
        : locale.languageCode;
    _current = _lookupAppLocalizations(locale);
    return _current!;
  }

  static AppLocalizations _lookupAppLocalizations(Locale locale) {
    switch (locale.languageCode) {
      case 'id':
        return AppLocalizationsId();
      case 'en':
      default:
        return AppLocalizationsEn();
    }
  }

  static const LocalizationsDelegate<AppLocalizations> delegate = _AppLocalizationsDelegate();

  // Common
  String get appTitle;
  String get welcome;
  String get login;
  String get logout;
  String get email;
  String get password;
  String get forgotPassword;
  String get submit;
  String get cancel;
  String get save;
  String get delete;
  String get edit;
  String get create;
  String get search;
  String get loading;
  String get error;
  String get success;
  String get confirm;
  String get back;
  String get next;
  String get done;
  String get close;

  // Menu Items
  String get menuDashboard;
  String get menuReservation;
  String get menuReception;
  String get menuConsultation;
  String get menuAccounting;
  String get menuPatients;
  String get menuWaiting;
  String get menuSettings;
  String get menuClinicSettings;
  String get menuPoints;
  String get menuQuestionnaire;

  // Auth
  String get authLoginTitle;
  String get authLoginSubtitle;
  String get authInvalidCredentials;
  String get authSessionExpired;
  String get authUnauthorized;

  // Errors
  String get errorNetwork;
  String get errorServer;
  String get errorNotFound;
  String get errorUnauthorized;
  String get errorForbidden;
}

class _AppLocalizationsDelegate extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  bool isSupported(Locale locale) {
    return ['en', 'id'].contains(locale.languageCode);
  }

  @override
  Future<AppLocalizations> load(Locale locale) {
    return AppLocalizations.load(locale);
  }

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

// Import implementations
part 'app_localizations_en.dart';
part 'app_localizations_id.dart';