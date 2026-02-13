import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart';
import 'l10n/app_localizations.dart';
import 'l10n/app_localizations_en.dart';
import 'l10n/app_localizations_id.dart';

class L10n {
  static final all = [
    const Locale('en'),
    const Locale('id'),
  ];

  static AppLocalizations of(BuildContext context) {
    return AppLocalizations.of(context)!;
  }

  static String getFlag(String code) {
    switch (code) {
      case 'en':
        return '🇺🇸';
      case 'id':
        return '🇮🇩';
      default:
        return '🇺🇸';
    }
  }
}

// Add to MaterialApp:
// localizationsDelegates: const [
//   AppLocalizations.delegate,
//   GlobalMaterialLocalizations.delegate,
//   GlobalWidgetsLocalizations.delegate,
//   GlobalCupertinoLocalizations.delegate,
// ],
// supportedLocales: L10n.all,