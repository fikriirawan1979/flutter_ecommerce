part of 'app_localizations.dart';

class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get appTitle => 'DentalClinicOS';

  @override
  String get welcome => 'Welcome';

  @override
  String get login => 'Login';

  @override
  String get logout => 'Logout';

  @override
  String get email => 'Email';

  @override
  String get password => 'Password';

  @override
  String get forgotPassword => 'Forgot Password?';

  @override
  String get submit => 'Submit';

  @override
  String get cancel => 'Cancel';

  @override
  String get save => 'Save';

  @override
  String get delete => 'Delete';

  @override
  String get edit => 'Edit';

  @override
  String get create => 'Create';

  @override
  String get search => 'Search';

  @override
  String get loading => 'Loading...';

  @override
  String get error => 'Error';

  @override
  String get success => 'Success';

  @override
  String get confirm => 'Confirm';

  @override
  String get back => 'Back';

  @override
  String get next => 'Next';

  @override
  String get done => 'Done';

  @override
  String get close => 'Close';

  // Menu Items
  @override
  String get menuDashboard => 'Dashboard';

  @override
  String get menuReservation => 'Reservations';

  @override
  String get menuReception => 'Reception';

  @override
  String get menuConsultation => 'Consultation';

  @override
  String get menuAccounting => 'Accounting';

  @override
  String get menuPatients => 'Patients';

  @override
  String get menuWaiting => 'Waiting Monitor';

  @override
  String get menuSettings => 'Settings';

  @override
  String get menuClinicSettings => 'Clinic Settings';

  @override
  String get menuPoints => 'Points Master';

  @override
  String get menuQuestionnaire => 'Questionnaire';

  // Auth
  @override
  String get authLoginTitle => 'Sign In';

  @override
  String get authLoginSubtitle => 'Enter your credentials to continue';

  @override
  String get authInvalidCredentials => 'Invalid email or password';

  @override
  String get authSessionExpired => 'Your session has expired. Please login again.';

  @override
  String get authUnauthorized => 'You are not authorized to access this page';

  // Errors
  @override
  String get errorNetwork => 'Network error. Please check your connection.';

  @override
  String get errorServer => 'Server error. Please try again later.';

  @override
  String get errorNotFound => 'Page not found';

  @override
  String get errorUnauthorized => 'Unauthorized';

  @override
  String get errorForbidden => 'Access forbidden';
}