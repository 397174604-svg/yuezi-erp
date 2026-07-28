-- MySQL 5.7
-- Organization, employee privacy, account and normalized RBAC extension.
-- This migration is applied after the disposable fake data in `yuezi` is reset.

CREATE TABLE IF NOT EXISTS schema_migrations (
  version VARCHAR(64) NOT NULL,
  description VARCHAR(255) NOT NULL,
  checksum CHAR(64) NOT NULL,
  applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (version)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS departments (
  department_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  store_id BIGINT NOT NULL,
  parent_department_id BIGINT DEFAULT NULL,
  code VARCHAR(64) NOT NULL,
  name VARCHAR(128) NOT NULL,
  manager_staff_id BIGINT DEFAULT NULL,
  sort_order INT NOT NULL DEFAULT 0,
  status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (department_id),
  UNIQUE KEY uk_department_store_code (tenant_id, store_id, code),
  KEY ix_department_store (tenant_id, store_id, status),
  KEY ix_department_parent (parent_department_id),
  CONSTRAINT fk_department_tenant
    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id),
  CONSTRAINT fk_department_store
    FOREIGN KEY (store_id) REFERENCES stores (store_id),
  CONSTRAINT fk_department_parent
    FOREIGN KEY (parent_department_id) REFERENCES departments (department_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS positions (
  position_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  department_id BIGINT NOT NULL,
  code VARCHAR(64) NOT NULL,
  name VARCHAR(128) NOT NULL,
  job_family VARCHAR(64) DEFAULT NULL,
  grade_code VARCHAR(32) DEFAULT NULL,
  is_manager TINYINT(1) NOT NULL DEFAULT 0,
  status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (position_id),
  UNIQUE KEY uk_position_department_code (department_id, code),
  KEY ix_position_tenant (tenant_id, status),
  CONSTRAINT fk_position_tenant
    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id),
  CONSTRAINT fk_position_department
    FOREIGN KEY (department_id) REFERENCES departments (department_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- MySQL 5.7 refuses to add AUTO_INCREMENT while other tables reference the
-- column. Preserve the four legacy relationships across the staff alteration.
ALTER TABLE schedules
  DROP FOREIGN KEY fk_schedules_1;
ALTER TABLE service_recommendations
  DROP FOREIGN KEY fk_service_recommendations_expert;
ALTER TABLE staff_points
  DROP FOREIGN KEY fk_staff_points_0;
ALTER TABLE staff_point_ledger
  DROP FOREIGN KEY fk_staff_point_ledger_0;

ALTER TABLE staff
  MODIFY staff_id BIGINT NOT NULL AUTO_INCREMENT,
  MODIFY name VARCHAR(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  MODIFY role VARCHAR(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  MODIFY position VARCHAR(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  MODIFY department VARCHAR(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  MODIFY status VARCHAR(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'ACTIVE',
  ADD COLUMN employee_no VARCHAR(32) DEFAULT NULL AFTER store_id,
  ADD COLUMN department_id BIGINT DEFAULT NULL AFTER employee_no,
  ADD COLUMN position_id BIGINT DEFAULT NULL AFTER department_id,
  ADD COLUMN gender VARCHAR(8) DEFAULT NULL AFTER name,
  ADD COLUMN birth_date DATE DEFAULT NULL AFTER gender,
  ADD COLUMN education VARCHAR(32) DEFAULT NULL AFTER birth_date,
  ADD COLUMN hire_date DATE DEFAULT NULL AFTER education,
  ADD COLUMN employment_status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE' AFTER hire_date,
  ADD COLUMN source_file VARCHAR(255) DEFAULT NULL AFTER password_hash,
  ADD COLUMN source_page INT DEFAULT NULL AFTER source_file,
  ADD COLUMN source_row INT DEFAULT NULL AFTER source_page,
  ADD COLUMN review_status VARCHAR(32) NOT NULL DEFAULT 'PENDING' AFTER source_row,
  ADD COLUMN created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP AFTER review_status,
  ADD COLUMN updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP AFTER created_at,
  ADD UNIQUE KEY uk_staff_tenant_employee_no (tenant_id, employee_no),
  ADD KEY ix_staff_department (department_id, employment_status),
  ADD KEY ix_staff_position (position_id),
  ADD CONSTRAINT fk_staff_department
    FOREIGN KEY (department_id) REFERENCES departments (department_id),
  ADD CONSTRAINT fk_staff_position
    FOREIGN KEY (position_id) REFERENCES positions (position_id);

ALTER TABLE schedules
  ADD CONSTRAINT fk_schedules_1
    FOREIGN KEY (staff_id) REFERENCES staff (staff_id)
    ON DELETE NO ACTION ON UPDATE NO ACTION;
ALTER TABLE service_recommendations
  ADD CONSTRAINT fk_service_recommendations_expert
    FOREIGN KEY (expert_id) REFERENCES staff (staff_id);
ALTER TABLE staff_points
  ADD CONSTRAINT fk_staff_points_0
    FOREIGN KEY (staff_id) REFERENCES staff (staff_id)
    ON DELETE NO ACTION ON UPDATE NO ACTION;
ALTER TABLE staff_point_ledger
  ADD CONSTRAINT fk_staff_point_ledger_0
    FOREIGN KEY (staff_id) REFERENCES staff (staff_id)
    ON DELETE NO ACTION ON UPDATE NO ACTION;

-- The legacy `phone` column remains only for compatibility and stores masked text.
-- Full PII is encrypted by the importer and stored in this one-to-one private table.
CREATE TABLE IF NOT EXISTS staff_private (
  staff_id BIGINT NOT NULL,
  encryption_version VARCHAR(32) NOT NULL,
  mobile_cipher VARBINARY(512) DEFAULT NULL,
  mobile_hash BINARY(32) DEFAULT NULL,
  id_no_cipher VARBINARY(512) DEFAULT NULL,
  id_no_hash BINARY(32) DEFAULT NULL,
  home_address_cipher VARBINARY(2048) DEFAULT NULL,
  emergency_name_cipher VARBINARY(512) DEFAULT NULL,
  emergency_phone_cipher VARBINARY(512) DEFAULT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (staff_id),
  UNIQUE KEY uk_staff_private_mobile_hash (mobile_hash),
  UNIQUE KEY uk_staff_private_id_hash (id_no_hash),
  CONSTRAINT fk_staff_private_staff
    FOREIGN KEY (staff_id) REFERENCES staff (staff_id)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

ALTER TABLE roles
  ADD COLUMN code VARCHAR(64) DEFAULT NULL AFTER tenant_id,
  ADD COLUMN role_type VARCHAR(32) NOT NULL DEFAULT 'JOB' AFTER name,
  ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE' AFTER description,
  ADD COLUMN updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP AFTER created_at,
  ADD UNIQUE KEY uk_roles_tenant_code (tenant_id, code);

CREATE TABLE IF NOT EXISTS permissions (
  permission_id BIGINT NOT NULL AUTO_INCREMENT,
  parent_id BIGINT DEFAULT NULL,
  code VARCHAR(128) NOT NULL,
  module_code VARCHAR(64) NOT NULL,
  resource_type VARCHAR(20) NOT NULL,
  action_code VARCHAR(32) NOT NULL,
  name VARCHAR(128) NOT NULL,
  sort_order INT NOT NULL DEFAULT 0,
  status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
  PRIMARY KEY (permission_id),
  UNIQUE KEY uk_permission_code (code),
  KEY ix_permission_module (module_code, resource_type, action_code),
  CONSTRAINT fk_permission_parent
    FOREIGN KEY (parent_id) REFERENCES permissions (permission_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS role_permissions (
  role_id BIGINT NOT NULL,
  permission_id BIGINT NOT NULL,
  effect VARCHAR(8) NOT NULL DEFAULT 'ALLOW',
  condition_json TEXT DEFAULT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (role_id, permission_id),
  CONSTRAINT fk_role_permission_role
    FOREIGN KEY (role_id) REFERENCES roles (role_id) ON DELETE CASCADE,
  CONSTRAINT fk_role_permission_permission
    FOREIGN KEY (permission_id) REFERENCES permissions (permission_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS user_accounts (
  user_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  staff_id BIGINT DEFAULT NULL,
  username VARCHAR(64) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  default_store_id BIGINT DEFAULT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
  failed_login_count INT NOT NULL DEFAULT 0,
  locked_until DATETIME DEFAULT NULL,
  last_login_at DATETIME DEFAULT NULL,
  password_changed_at DATETIME DEFAULT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id),
  UNIQUE KEY uk_user_tenant_username (tenant_id, username),
  UNIQUE KEY uk_user_staff (staff_id),
  KEY ix_user_default_store (default_store_id),
  CONSTRAINT fk_user_tenant
    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id),
  CONSTRAINT fk_user_staff
    FOREIGN KEY (staff_id) REFERENCES staff (staff_id),
  CONSTRAINT fk_user_store
    FOREIGN KEY (default_store_id) REFERENCES stores (store_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS user_roles (
  user_id BIGINT NOT NULL,
  role_id BIGINT NOT NULL,
  effective_from DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  effective_to DATETIME DEFAULT NULL,
  assigned_by BIGINT DEFAULT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id, role_id, effective_from),
  KEY ix_user_role_effective (role_id, effective_to),
  CONSTRAINT fk_user_role_user
    FOREIGN KEY (user_id) REFERENCES user_accounts (user_id) ON DELETE CASCADE,
  CONSTRAINT fk_user_role_role
    FOREIGN KEY (role_id) REFERENCES roles (role_id) ON DELETE CASCADE,
  CONSTRAINT fk_user_role_assigner
    FOREIGN KEY (assigned_by) REFERENCES user_accounts (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS user_stores (
  user_id BIGINT NOT NULL,
  store_id BIGINT NOT NULL,
  access_level VARCHAR(16) NOT NULL DEFAULT 'READ',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id, store_id),
  CONSTRAINT fk_user_store_user
    FOREIGN KEY (user_id) REFERENCES user_accounts (user_id) ON DELETE CASCADE,
  CONSTRAINT fk_user_store_store
    FOREIGN KEY (store_id) REFERENCES stores (store_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS role_data_scopes (
  role_id BIGINT NOT NULL,
  module_code VARCHAR(64) NOT NULL,
  scope_type VARCHAR(24) NOT NULL,
  allow_cross_store TINYINT(1) NOT NULL DEFAULT 0,
  allow_cross_department TINYINT(1) NOT NULL DEFAULT 0,
  condition_json TEXT DEFAULT NULL,
  PRIMARY KEY (role_id, module_code),
  CONSTRAINT fk_role_data_scope_role
    FOREIGN KEY (role_id) REFERENCES roles (role_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS field_permissions (
  role_id BIGINT NOT NULL,
  resource_code VARCHAR(128) NOT NULL,
  field_code VARCHAR(64) NOT NULL,
  visible TINYINT(1) NOT NULL DEFAULT 1,
  masked TINYINT(1) NOT NULL DEFAULT 0,
  editable TINYINT(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (role_id, resource_code, field_code),
  CONSTRAINT fk_field_permission_role
    FOREIGN KEY (role_id) REFERENCES roles (role_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS access_delegations (
  delegation_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  delegator_user_id BIGINT NOT NULL,
  delegate_user_id BIGINT NOT NULL,
  role_id BIGINT DEFAULT NULL,
  module_code VARCHAR(64) DEFAULT NULL,
  reason VARCHAR(255) NOT NULL,
  effective_from DATETIME NOT NULL,
  effective_to DATETIME NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
  approved_by BIGINT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (delegation_id),
  KEY ix_delegation_active (delegate_user_id, effective_from, effective_to, status),
  CONSTRAINT fk_delegation_tenant
    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id),
  CONSTRAINT fk_delegation_from
    FOREIGN KEY (delegator_user_id) REFERENCES user_accounts (user_id),
  CONSTRAINT fk_delegation_to
    FOREIGN KEY (delegate_user_id) REFERENCES user_accounts (user_id),
  CONSTRAINT fk_delegation_role
    FOREIGN KEY (role_id) REFERENCES roles (role_id),
  CONSTRAINT fk_delegation_approver
    FOREIGN KEY (approved_by) REFERENCES user_accounts (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
