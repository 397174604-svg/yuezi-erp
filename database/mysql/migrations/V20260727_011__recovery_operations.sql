-- MySQL 5.7
-- Recovery operations for the legacy role "产后修复师".
-- The tables are intentionally empty after migration: business rows must come
-- from the new ERP, never from scraped legacy customer records.

CREATE TABLE IF NOT EXISTS recovery_service_entitlements (
  entitlement_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  store_id BIGINT NOT NULL,
  customer_id BIGINT NOT NULL,
  contract_id BIGINT NULL,
  card_no VARCHAR(64) NULL,
  card_name VARCHAR(128) NULL,
  source_type VARCHAR(32) NOT NULL,
  source_no VARCHAR(64) NULL,
  service_name VARCHAR(128) NOT NULL,
  project_category VARCHAR(64) NOT NULL,
  stage VARCHAR(64) NULL,
  unit VARCHAR(16) NOT NULL DEFAULT '次',
  unit_price DECIMAL(12,2) NULL,
  duration_minutes INT NULL,
  total_count DECIMAL(10,2) NOT NULL DEFAULT 0,
  used_count DECIMAL(10,2) NOT NULL DEFAULT 0,
  booked_count DECIMAL(10,2) NOT NULL DEFAULT 0,
  assigned_staff_id BIGINT NULL,
  valid_from DATE NULL,
  valid_until DATE NULL,
  status VARCHAR(32) NOT NULL DEFAULT '有效',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  deleted_at DATETIME NULL,
  PRIMARY KEY (entitlement_id),
  KEY ix_recovery_entitlement_customer (tenant_id, customer_id, status),
  KEY ix_recovery_entitlement_store (store_id, project_category, status),
  KEY ix_recovery_entitlement_card (tenant_id, card_no),
  KEY fk_recovery_entitlement_contract (contract_id),
  KEY fk_recovery_entitlement_staff (assigned_staff_id),
  CONSTRAINT fk_recovery_entitlement_tenant
    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id),
  CONSTRAINT fk_recovery_entitlement_store
    FOREIGN KEY (store_id) REFERENCES stores (store_id),
  CONSTRAINT fk_recovery_entitlement_customer
    FOREIGN KEY (customer_id) REFERENCES customers (customer_id),
  CONSTRAINT fk_recovery_entitlement_contract
    FOREIGN KEY (contract_id) REFERENCES contracts (contract_id),
  CONSTRAINT fk_recovery_entitlement_staff
    FOREIGN KEY (assigned_staff_id) REFERENCES staff (staff_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS recovery_appointments (
  appointment_id BIGINT NOT NULL AUTO_INCREMENT,
  appointment_no VARCHAR(64) NOT NULL,
  tenant_id BIGINT NOT NULL,
  store_id BIGINT NOT NULL,
  customer_id BIGINT NOT NULL,
  entitlement_id BIGINT NULL,
  service_name VARCHAR(128) NOT NULL,
  project_category VARCHAR(64) NULL,
  appointment_date DATE NOT NULL,
  period_start TIME NULL,
  period_end TIME NULL,
  technician_staff_id BIGINT NULL,
  service_place VARCHAR(128) NULL,
  service_count DECIMAL(10,2) NOT NULL DEFAULT 1,
  status VARCHAR(32) NOT NULL DEFAULT '已预约',
  remark VARCHAR(1000) NULL,
  created_by_user_id BIGINT NOT NULL,
  confirmed_at DATETIME NULL,
  completed_at DATETIME NULL,
  cancelled_at DATETIME NULL,
  version BIGINT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  deleted_at DATETIME NULL,
  PRIMARY KEY (appointment_id),
  UNIQUE KEY uk_recovery_appointment_no (appointment_no),
  KEY ix_recovery_appointment_store_date (store_id, appointment_date, status),
  KEY ix_recovery_appointment_customer (customer_id, appointment_date),
  KEY ix_recovery_appointment_technician (technician_staff_id, appointment_date, status),
  KEY fk_recovery_appointment_entitlement (entitlement_id),
  KEY fk_recovery_appointment_creator (created_by_user_id),
  CONSTRAINT fk_recovery_appointment_tenant
    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id),
  CONSTRAINT fk_recovery_appointment_store
    FOREIGN KEY (store_id) REFERENCES stores (store_id),
  CONSTRAINT fk_recovery_appointment_customer
    FOREIGN KEY (customer_id) REFERENCES customers (customer_id),
  CONSTRAINT fk_recovery_appointment_entitlement
    FOREIGN KEY (entitlement_id) REFERENCES recovery_service_entitlements (entitlement_id),
  CONSTRAINT fk_recovery_appointment_technician
    FOREIGN KEY (technician_staff_id) REFERENCES staff (staff_id),
  CONSTRAINT fk_recovery_appointment_creator
    FOREIGN KEY (created_by_user_id) REFERENCES user_accounts (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS recovery_staff_schedules (
  schedule_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  store_id BIGINT NOT NULL,
  staff_id BIGINT NOT NULL,
  schedule_date DATE NOT NULL,
  shift_name VARCHAR(64) NOT NULL,
  start_time TIME NULL,
  end_time TIME NULL,
  max_bookings INT NOT NULL DEFAULT 0,
  status VARCHAR(32) NOT NULL DEFAULT '出勤',
  remark VARCHAR(1000) NULL,
  created_by_user_id BIGINT NOT NULL,
  version BIGINT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  deleted_at DATETIME NULL,
  PRIMARY KEY (schedule_id),
  UNIQUE KEY uk_recovery_schedule_staff_day_shift
    (tenant_id, staff_id, schedule_date, shift_name),
  KEY ix_recovery_schedule_store_date (store_id, schedule_date, status),
  KEY fk_recovery_schedule_creator (created_by_user_id),
  CONSTRAINT fk_recovery_schedule_tenant
    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id),
  CONSTRAINT fk_recovery_schedule_store
    FOREIGN KEY (store_id) REFERENCES stores (store_id),
  CONSTRAINT fk_recovery_schedule_staff
    FOREIGN KEY (staff_id) REFERENCES staff (staff_id),
  CONSTRAINT fk_recovery_schedule_creator
    FOREIGN KEY (created_by_user_id) REFERENCES user_accounts (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS recovery_service_records (
  record_id BIGINT NOT NULL AUTO_INCREMENT,
  record_no VARCHAR(64) NOT NULL,
  tenant_id BIGINT NOT NULL,
  store_id BIGINT NOT NULL,
  customer_id BIGINT NOT NULL,
  appointment_id BIGINT NULL,
  entitlement_id BIGINT NULL,
  service_name VARCHAR(128) NOT NULL,
  project_category VARCHAR(64) NULL,
  technician_staff_id BIGINT NOT NULL,
  service_date DATE NOT NULL,
  period_start TIME NULL,
  period_end TIME NULL,
  used_count DECIMAL(10,2) NOT NULL DEFAULT 1,
  price DECIMAL(12,2) NULL,
  labor_fee DECIMAL(12,2) NULL,
  service_result TEXT NULL,
  customer_feedback TEXT NULL,
  review_status VARCHAR(32) NOT NULL DEFAULT '未审核',
  reviewed_by_user_id BIGINT NULL,
  reviewed_at DATETIME NULL,
  created_by_user_id BIGINT NOT NULL,
  version BIGINT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  deleted_at DATETIME NULL,
  PRIMARY KEY (record_id),
  UNIQUE KEY uk_recovery_service_record_no (record_no),
  UNIQUE KEY uk_recovery_service_record_appointment (appointment_id),
  KEY ix_recovery_record_store_date (store_id, service_date, review_status),
  KEY ix_recovery_record_customer (customer_id, service_date),
  KEY ix_recovery_record_technician (technician_staff_id, service_date),
  KEY fk_recovery_record_entitlement (entitlement_id),
  KEY fk_recovery_record_creator (created_by_user_id),
  KEY fk_recovery_record_reviewer (reviewed_by_user_id),
  CONSTRAINT fk_recovery_record_tenant
    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id),
  CONSTRAINT fk_recovery_record_store
    FOREIGN KEY (store_id) REFERENCES stores (store_id),
  CONSTRAINT fk_recovery_record_customer
    FOREIGN KEY (customer_id) REFERENCES customers (customer_id),
  CONSTRAINT fk_recovery_record_appointment
    FOREIGN KEY (appointment_id) REFERENCES recovery_appointments (appointment_id),
  CONSTRAINT fk_recovery_record_entitlement
    FOREIGN KEY (entitlement_id) REFERENCES recovery_service_entitlements (entitlement_id),
  CONSTRAINT fk_recovery_record_technician
    FOREIGN KEY (technician_staff_id) REFERENCES staff (staff_id),
  CONSTRAINT fk_recovery_record_creator
    FOREIGN KEY (created_by_user_id) REFERENCES user_accounts (user_id),
  CONSTRAINT fk_recovery_record_reviewer
    FOREIGN KEY (reviewed_by_user_id) REFERENCES user_accounts (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS recovery_material_consumptions (
  consumption_id BIGINT NOT NULL AUTO_INCREMENT,
  document_no VARCHAR(64) NOT NULL,
  tenant_id BIGINT NOT NULL,
  store_id BIGINT NOT NULL,
  service_record_id BIGINT NOT NULL,
  material_item_id BIGINT NULL,
  material_code VARCHAR(64) NULL,
  material_name VARCHAR(128) NOT NULL,
  material_category VARCHAR(64) NULL,
  material_model VARCHAR(64) NULL,
  unit VARCHAR(16) NULL,
  quantity DECIMAL(12,4) NOT NULL,
  warehouse_name VARCHAR(128) NULL,
  stock_status VARCHAR(32) NOT NULL DEFAULT '待扣减',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (consumption_id),
  UNIQUE KEY uk_recovery_consumption_document (document_no),
  KEY ix_recovery_consumption_record (service_record_id),
  KEY ix_recovery_consumption_store (store_id, created_at),
  KEY fk_recovery_consumption_item (material_item_id),
  CONSTRAINT fk_recovery_consumption_tenant
    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id),
  CONSTRAINT fk_recovery_consumption_store
    FOREIGN KEY (store_id) REFERENCES stores (store_id),
  CONSTRAINT fk_recovery_consumption_record
    FOREIGN KEY (service_record_id) REFERENCES recovery_service_records (record_id),
  CONSTRAINT fk_recovery_consumption_item
    FOREIGN KEY (material_item_id) REFERENCES items (item_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS recovery_health_assessments (
  assessment_id BIGINT NOT NULL AUTO_INCREMENT,
  assessment_no VARCHAR(64) NOT NULL,
  tenant_id BIGINT NOT NULL,
  store_id BIGINT NOT NULL,
  customer_id BIGINT NOT NULL,
  assessment_name VARCHAR(128) NOT NULL,
  assessment_type VARCHAR(64) NULL,
  assessed_at DATE NOT NULL,
  postpartum_days INT NULL,
  assessor_staff_id BIGINT NOT NULL,
  main_concern TEXT NULL,
  assessment_result TEXT NOT NULL,
  recommendation TEXT NULL,
  contraindication TEXT NULL,
  created_by_user_id BIGINT NOT NULL,
  version BIGINT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  deleted_at DATETIME NULL,
  PRIMARY KEY (assessment_id),
  UNIQUE KEY uk_recovery_assessment_no (assessment_no),
  KEY ix_recovery_assessment_store_date (store_id, assessed_at),
  KEY ix_recovery_assessment_customer (customer_id, assessed_at),
  KEY fk_recovery_assessment_assessor (assessor_staff_id),
  KEY fk_recovery_assessment_creator (created_by_user_id),
  CONSTRAINT fk_recovery_assessment_tenant
    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id),
  CONSTRAINT fk_recovery_assessment_store
    FOREIGN KEY (store_id) REFERENCES stores (store_id),
  CONSTRAINT fk_recovery_assessment_customer
    FOREIGN KEY (customer_id) REFERENCES customers (customer_id),
  CONSTRAINT fk_recovery_assessment_assessor
    FOREIGN KEY (assessor_staff_id) REFERENCES staff (staff_id),
  CONSTRAINT fk_recovery_assessment_creator
    FOREIGN KEY (created_by_user_id) REFERENCES user_accounts (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- The legacy recovery role can view sales/finance pages, but its observed
-- grants do not authorize the MVP contract/receipt write operations.
DELETE rp
FROM role_permissions rp
JOIN roles r ON r.role_id = rp.role_id
JOIN permissions p ON p.permission_id = rp.permission_id
WHERE r.code = 'RECOVERY_THERAPIST'
  AND p.code IN (
    'SALES.CREATE', 'SALES.UPDATE',
    'FINANCE.CREATE', 'FINANCE.UPDATE'
  );
