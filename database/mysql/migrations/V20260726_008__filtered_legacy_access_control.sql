-- MySQL 5.7
-- Preserve the legacy ERP identity and permission keys without coupling the
-- application to role names. The raw crawl remains outside the database import.

ALTER TABLE roles
  ADD COLUMN legacy_role_id INT DEFAULT NULL AFTER code,
  ADD COLUMN source_system VARCHAR(32) NOT NULL DEFAULT 'LOCAL' AFTER legacy_role_id,
  ADD UNIQUE KEY uk_roles_tenant_legacy (tenant_id, source_system, legacy_role_id);

ALTER TABLE user_accounts
  ADD COLUMN legacy_user_id INT DEFAULT NULL AFTER tenant_id,
  ADD COLUMN legacy_username VARCHAR(128) DEFAULT NULL AFTER username,
  ADD COLUMN department_id BIGINT DEFAULT NULL AFTER default_store_id,
  ADD COLUMN must_change_password TINYINT(1) NOT NULL DEFAULT 0 AFTER password_changed_at,
  ADD COLUMN source_system VARCHAR(32) NOT NULL DEFAULT 'LOCAL' AFTER must_change_password,
  ADD UNIQUE KEY uk_user_tenant_legacy (tenant_id, source_system, legacy_user_id),
  ADD KEY ix_user_department (department_id);

CREATE TABLE IF NOT EXISTS legacy_permission_resources (
  legacy_permission_id BIGINT NOT NULL AUTO_INCREMENT,
  surface VARCHAR(16) NOT NULL,
  menu_id INT NOT NULL,
  button_id INT NOT NULL DEFAULT 0,
  menu_name VARCHAR(255) NOT NULL,
  button_name VARCHAR(255) DEFAULT NULL,
  permission_id BIGINT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (legacy_permission_id),
  UNIQUE KEY uk_legacy_permission_source (surface, menu_id, button_id),
  UNIQUE KEY uk_legacy_permission_target (permission_id),
  CONSTRAINT fk_legacy_permission_target
    FOREIGN KEY (permission_id) REFERENCES permissions (permission_id)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS legacy_role_data_scope_grants (
  role_id BIGINT NOT NULL,
  nav_id INT NOT NULL,
  department_id INT NOT NULL,
  parent_department_id INT DEFAULT NULL,
  department_name VARCHAR(255) NOT NULL,
  granted TINYINT(1) NOT NULL DEFAULT 0,
  empty_result TINYINT(1) NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (role_id, nav_id, department_id),
  KEY ix_legacy_scope_nav (nav_id, department_id, granted),
  CONSTRAINT fk_legacy_scope_role
    FOREIGN KEY (role_id) REFERENCES roles (role_id)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS legacy_role_exclusions (
  legacy_role_id INT NOT NULL,
  role_name VARCHAR(128) NOT NULL,
  reason VARCHAR(255) NOT NULL,
  excluded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (legacy_role_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS legacy_access_import_runs (
  import_id BIGINT NOT NULL AUTO_INCREMENT,
  source_roles INT NOT NULL,
  imported_roles INT NOT NULL,
  excluded_roles INT NOT NULL,
  source_users INT NOT NULL,
  imported_users INT NOT NULL,
  excluded_users INT NOT NULL,
  role_relations INT NOT NULL,
  web_grants INT NOT NULL,
  app_grants INT NOT NULL,
  data_scope_grants INT NOT NULL,
  detail_json TEXT DEFAULT NULL,
  imported_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (import_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
