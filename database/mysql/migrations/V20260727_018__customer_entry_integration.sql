-- MySQL 5.7
-- Persist every field submitted by the field-level customer entry page and
-- keep server-side drafts in MySQL. This is business state, not mock data.

CREATE TABLE customer_entry_drafts (
  draft_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  store_id BIGINT NOT NULL,
  owner_user_id BIGINT NOT NULL,
  payload_json LONGTEXT NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT '草稿',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (draft_id),
  KEY ix_customer_entry_draft_owner
    (tenant_id, owner_user_id, status, updated_at),
  KEY ix_customer_entry_draft_store (store_id, status),
  CONSTRAINT fk_customer_entry_draft_tenant
    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id),
  CONSTRAINT fk_customer_entry_draft_store
    FOREIGN KEY (store_id) REFERENCES stores (store_id),
  CONSTRAINT fk_customer_entry_draft_owner
    FOREIGN KEY (owner_user_id) REFERENCES user_accounts (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE customer_entry_profiles (
  profile_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  customer_id BIGINT NOT NULL,
  country_code VARCHAR(8) NOT NULL DEFAULT '+86',
  member_card VARCHAR(64) DEFAULT NULL,
  tags_json TEXT DEFAULT NULL,
  is_to_store TINYINT(1) NOT NULL DEFAULT 0,
  intended_days INT DEFAULT NULL,
  planned_stay_date DATE DEFAULT NULL,
  intended_room_id BIGINT DEFAULT NULL,
  intended_room_type VARCHAR(100) DEFAULT NULL,
  estimated_contract_amount DECIMAL(20,4) DEFAULT NULL,
  intended_package_id BIGINT DEFAULT NULL,
  intended_package_name VARCHAR(160) DEFAULT NULL,
  intended_package_amount DECIMAL(20,4) DEFAULT NULL,
  recovery_store_id BIGINT DEFAULT NULL,
  companion_name VARCHAR(100) DEFAULT NULL,
  companion_phone VARCHAR(32) DEFAULT NULL,
  fetus_type VARCHAR(32) DEFAULT NULL,
  pregnancy_count VARCHAR(32) DEFAULT NULL,
  area_id VARCHAR(64) DEFAULT NULL,
  area_name VARCHAR(160) DEFAULT NULL,
  first_visit_at DATETIME DEFAULT NULL,
  tracker_staff_id BIGINT DEFAULT NULL,
  tracker_department VARCHAR(160) DEFAULT NULL,
  ethnicity VARCHAR(64) DEFAULT NULL,
  work_unit VARCHAR(200) DEFAULT NULL,
  occupation VARCHAR(100) DEFAULT NULL,
  email VARCHAR(160) DEFAULT NULL,
  entry_time DATETIME DEFAULT NULL,
  address VARCHAR(500) DEFAULT NULL,
  diet_note VARCHAR(1000) DEFAULT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (profile_id),
  UNIQUE KEY ux_customer_entry_profile (tenant_id, customer_id),
  KEY ix_customer_entry_room (intended_room_id),
  KEY ix_customer_entry_tracker (tracker_staff_id),
  KEY ix_customer_entry_recovery_store (recovery_store_id),
  CONSTRAINT fk_customer_entry_profile_tenant
    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id),
  CONSTRAINT fk_customer_entry_profile_customer
    FOREIGN KEY (customer_id) REFERENCES customers (customer_id),
  CONSTRAINT fk_customer_entry_profile_room
    FOREIGN KEY (intended_room_id) REFERENCES rooms (room_id),
  CONSTRAINT fk_customer_entry_profile_tracker
    FOREIGN KEY (tracker_staff_id) REFERENCES staff (staff_id),
  CONSTRAINT fk_customer_entry_profile_recovery_store
    FOREIGN KEY (recovery_store_id) REFERENCES stores (store_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
