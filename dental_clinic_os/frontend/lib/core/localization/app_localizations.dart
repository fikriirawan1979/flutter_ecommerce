import 'package:flutter/material.dart';

abstract class AppLocalizations {
  AppLocalizations(String locale) : localeName = Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations)!;
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
  String get yes;
  String get no;
  String get view;
  String get download;
  String get upload;
  String get select;
  String get filter;
  String get sort;
  String get export;
  String get print;
  String get refresh;
  String get details;
  String get actions;
  String get status;
  String get date;
  String get time;
  String get amount;
  String get total;
  String get subtotal;
  String get discount;
  String get tax;
  String get notes;
  String get description;
  String get name;
  String get phone;
  String get address;
  String get city;
  String get country;
  String get postalCode;

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
  String get menuAssessments;
  String get menuOrders;
  String get menuProducts;
  String get menuReports;

  // Auth
  String get authLoginTitle;
  String get authLoginSubtitle;
  String get authInvalidCredentials;
  String get authSessionExpired;
  String get authUnauthorized;
  String get authRegisterTitle;
  String get authRegisterSubtitle;
  String get authFirstName;
  String get authLastName;
  String get authConfirmPassword;
  String get authAlreadyHaveAccount;
  String get authDontHaveAccount;
  String get authCreateAccount;
  String get authForgotPasswordTitle;
  String get authForgotPasswordSubtitle;
  String get authResetPasswordTitle;
  String get authResetPasswordSubtitle;

  // Dashboard
  String get dashboardTitle;
  String get dashboardOverview;
  String get dashboardRecentOrders;
  String get dashboardPendingAssessments;
  String get dashboardTotalRevenue;
  String get dashboardTotalPatients;
  String get dashboardTotalAssessments;
  String get dashboardWeeklyRevenue;
  String get dashboardMonthlyRevenue;

  // Assessments
  String get assessmentsTitle;
  String get assessmentsList;
  String get assessmentsCreate;
  String get assessmentsView;
  String get assessmentsUploadImages;
  String get assessmentsAnalyze;
  String get assessmentsComplete;
  String get assessmentsReport;
  String get assessmentsStatusPending;
  String get assessmentsStatusUploaded;
  String get assessmentsStatusInReview;
  String get assessmentsStatusCompleted;
  String get assessmentsSkeletalClass;
  String get assessmentsSeverity;
  String get assessmentsTreatmentSuggestion;
  String get assessmentsConfidenceScore;
  String get assessmentsCephalometricMeasurements;
  String get assessmentsSNA;
  String get assessmentsSNB;
  String get assessmentsANB;
  String get assessmentsOverjet;
  String get assessmentsOverbite;

  // Orders
  String get ordersTitle;
  String get ordersList;
  String get ordersCreate;
  String get ordersView;
  String get ordersStatusPending;
  String get ordersStatusPaid;
  String get ordersStatusProcessing;
  String get ordersStatusCompleted;
  String get ordersStatusCancelled;
  String get ordersInvoiceNumber;
  String get orderItems;

  // Products
  String get productsTitle;
  String get productsList;
  String get productsCreate;
  String get productsEdit;
  String get productsName;
  String get productsPrice;
  String get productsFeatures;
  String get productsIsActive;

  // Payments
  String get paymentsTitle;
  String get paymentsCreatePayment;
  String get paymentsPaymentSuccessful;
  String get paymentsPaymentFailed;
  String get paymentsRefund;
  String get paymentsRefundSuccess;
  String get paymentMethod;
  String get cardNumber;
  String get expiryDate;
  String get cvv;

  // Patients
  String get patientsTitle;
  String get patientsList;
  String get patientsCreate;
  String get patientsView;
  String get patientsEdit;
  String get patientsMedicalHistory;
  String get patientsTreatments;

  // Settings
  String get settingsTitle;
  String get settingsProfile;
  String get settingsChangePassword;
  String get settingsNotifications;
  String get settingsLanguage;
  String get settingsTheme;
  String get settingsPrivacy;
  String get settingsTerms;

  // Errors
  String get errorNetwork;
  String get errorServer;
  String get errorNotFound;
  String get errorUnauthorized;
  String get errorForbidden;
  String get errorValidation;
  String get errorRequired;
  String get errorMinLength;
  String get errorMaxLength;
  String get errorInvalidEmail;
  String get errorInvalidPhone;
  String get errorPasswordMismatch;
  String get errorDuplicateEntry;
  String get errorPaymentFailed;
  String get errorUploadFailed;

  // Messages
  String get msgSavedSuccessfully;
  String get msgDeletedSuccessfully;
  String get msgUpdatedSuccessfully;
  String get msgCreatedSuccessfully;
  String get msgConfirmDelete;
  String get msgConfirmAction;
  String get msgNoResultsFound;
  String get msgSomethingWentWrong;
  String get msgTryAgainLater;
  String get msgContactSupport;
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