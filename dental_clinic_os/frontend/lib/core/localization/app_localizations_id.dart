part of 'app_localizations.dart';

class AppLocalizationsId extends AppLocalizations {
  AppLocalizationsId([String locale = 'id']) : super(locale);

  @override
  String get appTitle => 'DentalClinicOS';

  @override
  String get welcome => 'Selamat Datang';

  @override
  String get login => 'Masuk';

  @override
  String get logout => 'Keluar';

  @override
  String get email => 'Email';

  @override
  String get password => 'Kata Sandi';

  @override
  String get forgotPassword => 'Lupa Kata Sandi?';

  @override
  String get submit => 'Kirim';

  @override
  String get cancel => 'Batal';

  @override
  String get save => 'Simpan';

  @override
  String get delete => 'Hapus';

  @override
  String get edit => 'Ubah';

  @override
  String get create => 'Buat';

  @override
  String get search => 'Cari';

  @override
  String get loading => 'Memuat...';

  @override
  String get error => 'Kesalahan';

  @override
  String get success => 'Berhasil';

  @override
  String get confirm => 'Konfirmasi';

  @override
  String get back => 'Kembali';

  @override
  String get next => 'Lanjut';

  @override
  String get done => 'Selesai';

  @override
  String get close => 'Tutup';

  // Menu Items
  @override
  String get menuDashboard => 'Dasbor';

  @override
  String get menuReservation => 'Reservasi';

  @override
  String get menuReception => 'Resepsionis';

  @override
  String get menuConsultation => 'Ruang Konsultasi';

  @override
  String get menuAccounting => 'Akuntansi';

  @override
  String get menuPatients => 'Pasien';

  @override
  String get menuWaiting => 'Monitor Antrian';

  @override
  String get menuSettings => 'Pengaturan';

  @override
  String get menuClinicSettings => 'Pengaturan Klinik';

  @override
  String get menuPoints => 'Master Poin';

  @override
  String get menuQuestionnaire => 'Kuesioner';

  // Auth
  @override
  String get authLoginTitle => 'Masuk';

  @override
  String get authLoginSubtitle => 'Masukkan kredensial Anda untuk melanjutkan';

  @override
  String get authInvalidCredentials => 'Email atau kata sandi tidak valid';

  @override
  String get authSessionExpired => 'Sesi Anda telah berakhir. Silakan masuk kembali.';

  @override
  String get authUnauthorized => 'Anda tidak memiliki akses ke halaman ini';

  // Errors
  @override
  String get errorNetwork => 'Kesalahan jaringan. Periksa koneksi Anda.';

  @override
  String get errorServer => 'Kesalahan server. Silakan coba lagi nanti.';

  @override
  String get errorNotFound => 'Halaman tidak ditemukan';

  @override
  String get errorUnauthorized => 'Tidak terotorisasi';

  @override
  String get errorForbidden => 'Akses dilarang';
}