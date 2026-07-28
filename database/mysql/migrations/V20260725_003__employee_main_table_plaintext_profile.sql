-- MySQL 5.7
-- Put the complete current employee profile directly on `staff` so Navicat
-- and legacy-compatible APIs can read it without joining an extension table.

ALTER TABLE staff
  ADD COLUMN id_no VARCHAR(128) DEFAULT NULL AFTER phone,
  ADD COLUMN id_no_normalized VARCHAR(32) DEFAULT NULL AFTER id_no,
  ADD COLUMN id_no_valid TINYINT(1) NOT NULL DEFAULT 0 AFTER id_no_normalized,
  ADD COLUMN id_valid_until DATE DEFAULT NULL AFTER id_no_valid,
  ADD COLUMN home_address VARCHAR(1024) DEFAULT NULL AFTER id_valid_until,
  ADD COLUMN emergency_contact_name VARCHAR(64) DEFAULT NULL AFTER home_address,
  ADD COLUMN emergency_contact_phone VARCHAR(32) DEFAULT NULL AFTER emergency_contact_name,
  ADD COLUMN salary_card_no VARCHAR(64) DEFAULT NULL AFTER emergency_contact_phone,
  ADD KEY ix_staff_id_no_normalized (id_no_normalized),
  ADD KEY ix_staff_emergency_phone (emergency_contact_phone);
