import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:flutter/foundation.dart';

part 'user_entity.freezed.dart';
part 'user_entity.g.dart';

enum UserRole {
  patient,
  doctor,
  admin,
}

@freezed
class UserEntity with _$UserEntity {
  const factory UserEntity({
    required String id,
    required String email,
    required String firstName,
    required String lastName,
    String? phone,
    String? avatarUrl,
    @Default(UserRole.patient) UserRole role,
    DateTime? dateOfBirth,
    String? gender,
    String? address,
    DateTime? createdAt,
    DateTime? updatedAt,
  }) = _UserEntity;

  factory UserEntity.fromJson(Map<String, dynamic> json) =>
      _$UserEntityFromJson(json);

  const UserEntity._();

  String get fullName => '$firstName $lastName';
  
  String get initials => '${firstName[0]}${lastName[0]}'.toUpperCase();
  
  bool get isPatient => role == UserRole.patient;
  bool get isDoctor => role == UserRole.doctor;
  bool get isAdmin => role == UserRole.admin;
}