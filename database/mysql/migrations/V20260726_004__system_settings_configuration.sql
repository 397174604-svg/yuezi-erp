-- MySQL 5.7
-- Normalized system-settings configuration imported from the legacy ERP.
-- Real operational logs, announcement bodies and birthday-message customer rows
-- are intentionally excluded from this migration.

CREATE TABLE IF NOT EXISTS sys_config_import_runs (
  import_run_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  source_system VARCHAR(64) NOT NULL,
  captured_at DATETIME NOT NULL,
  source_manifest VARCHAR(255) DEFAULT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'READY',
  summary_text TEXT DEFAULT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (import_run_id),
  KEY ix_sys_config_run_tenant (tenant_id, captured_at),
  CONSTRAINT fk_sys_config_run_tenant
    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sys_dictionary_types (
  dictionary_type_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  legacy_type_id BIGINT DEFAULT NULL,
  code VARCHAR(64) NOT NULL,
  name VARCHAR(128) NOT NULL,
  sort_order INT NOT NULL DEFAULT 0,
  status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
  remark VARCHAR(500) DEFAULT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (dictionary_type_id),
  UNIQUE KEY uk_sys_dictionary_type_code (tenant_id, code),
  UNIQUE KEY uk_sys_dictionary_type_legacy (tenant_id, legacy_type_id),
  CONSTRAINT fk_sys_dictionary_type_tenant
    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sys_dictionary_items (
  dictionary_item_id BIGINT NOT NULL AUTO_INCREMENT,
  dictionary_type_id BIGINT NOT NULL,
  legacy_item_id BIGINT DEFAULT NULL,
  parent_item_id BIGINT DEFAULT NULL,
  store_id BIGINT DEFAULT NULL,
  code VARCHAR(64) DEFAULT NULL,
  name VARCHAR(255) NOT NULL,
  sort_order INT NOT NULL DEFAULT 0,
  status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
  remark VARCHAR(500) DEFAULT NULL,
  ext_value_1 VARCHAR(500) DEFAULT NULL,
  ext_value_2 VARCHAR(500) DEFAULT NULL,
  ext_value_3 VARCHAR(500) DEFAULT NULL,
  ext_value_4 VARCHAR(500) DEFAULT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (dictionary_item_id),
  UNIQUE KEY uk_sys_dictionary_item_legacy (dictionary_type_id, legacy_item_id),
  KEY ix_sys_dictionary_item_code (dictionary_type_id, code),
  KEY ix_sys_dictionary_item_parent (parent_item_id),
  CONSTRAINT fk_sys_dictionary_item_type
    FOREIGN KEY (dictionary_type_id) REFERENCES sys_dictionary_types (dictionary_type_id)
      ON DELETE CASCADE,
  CONSTRAINT fk_sys_dictionary_item_parent
    FOREIGN KEY (parent_item_id) REFERENCES sys_dictionary_items (dictionary_item_id),
  CONSTRAINT fk_sys_dictionary_item_store
    FOREIGN KEY (store_id) REFERENCES stores (store_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sys_legacy_menus (
  menu_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  legacy_menu_id BIGINT NOT NULL,
  parent_menu_id BIGINT DEFAULT NULL,
  surface VARCHAR(16) NOT NULL COMMENT 'WEB or APP',
  title VARCHAR(255) NOT NULL,
  link_url VARCHAR(1000) DEFAULT NULL,
  navigation_tag VARCHAR(128) DEFAULT NULL,
  icon_class VARCHAR(255) DEFAULT NULL,
  icon_url VARCHAR(1000) DEFAULT NULL,
  big_image_url VARCHAR(1000) DEFAULT NULL,
  is_visible TINYINT(1) NOT NULL DEFAULT 1,
  sort_order INT NOT NULL DEFAULT 0,
  remark VARCHAR(500) DEFAULT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (menu_id),
  UNIQUE KEY uk_sys_legacy_menu (tenant_id, surface, legacy_menu_id),
  KEY ix_sys_legacy_menu_parent (parent_menu_id, sort_order),
  CONSTRAINT fk_sys_legacy_menu_tenant
    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id),
  CONSTRAINT fk_sys_legacy_menu_parent
    FOREIGN KEY (parent_menu_id) REFERENCES sys_legacy_menus (menu_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sys_legacy_buttons (
  button_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  legacy_button_id BIGINT NOT NULL,
  name VARCHAR(128) NOT NULL,
  button_tag VARCHAR(128) DEFAULT NULL,
  icon_class VARCHAR(255) DEFAULT NULL,
  icon_url VARCHAR(1000) DEFAULT NULL,
  button_html TEXT DEFAULT NULL,
  sort_order INT NOT NULL DEFAULT 0,
  remark VARCHAR(500) DEFAULT NULL,
  PRIMARY KEY (button_id),
  UNIQUE KEY uk_sys_legacy_button (tenant_id, legacy_button_id),
  CONSTRAINT fk_sys_legacy_button_tenant
    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sys_role_resource_grants (
  grant_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  role_id BIGINT DEFAULT NULL,
  legacy_role_id BIGINT NOT NULL,
  surface VARCHAR(16) NOT NULL COMMENT 'WEB or APP',
  legacy_menu_id BIGINT NOT NULL,
  legacy_button_id BIGINT NOT NULL,
  imported_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (grant_id),
  UNIQUE KEY uk_sys_role_resource_grant
    (tenant_id, legacy_role_id, surface, legacy_menu_id, legacy_button_id),
  KEY ix_sys_role_resource_role (role_id, surface),
  CONSTRAINT fk_sys_role_resource_tenant
    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id),
  CONSTRAINT fk_sys_role_resource_role
    FOREIGN KEY (role_id) REFERENCES roles (role_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sys_role_department_scopes (
  scope_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  role_id BIGINT DEFAULT NULL,
  legacy_role_id BIGINT NOT NULL,
  legacy_menu_id BIGINT NOT NULL,
  legacy_department_id BIGINT DEFAULT NULL,
  department_id BIGINT DEFAULT NULL,
  granted TINYINT(1) NOT NULL DEFAULT 0,
  imported_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (scope_id),
  UNIQUE KEY uk_sys_role_department_scope
    (tenant_id, legacy_role_id, legacy_menu_id, legacy_department_id),
  KEY ix_sys_role_department_role (role_id, legacy_menu_id, granted),
  CONSTRAINT fk_sys_role_department_tenant
    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id),
  CONSTRAINT fk_sys_role_department_role
    FOREIGN KEY (role_id) REFERENCES roles (role_id) ON DELETE CASCADE,
  CONSTRAINT fk_sys_role_department_department
    FOREIGN KEY (department_id) REFERENCES departments (department_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sys_parameters (
  parameter_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  legacy_parameter_id BIGINT DEFAULT NULL,
  parameter_type VARCHAR(64) NOT NULL,
  parameter_code VARCHAR(128) NOT NULL,
  parameter_value TEXT DEFAULT NULL,
  parameter_level INT NOT NULL DEFAULT 0,
  legacy_type_id BIGINT DEFAULT NULL,
  remark VARCHAR(1000) DEFAULT NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (parameter_id),
  UNIQUE KEY uk_sys_parameter_code (tenant_id, parameter_code),
  UNIQUE KEY uk_sys_parameter_legacy (tenant_id, legacy_parameter_id),
  CONSTRAINT fk_sys_parameter_tenant
    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sys_warning_parameters (
  warning_parameter_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  legacy_key_id BIGINT DEFAULT NULL,
  legacy_warning_id BIGINT NOT NULL,
  warning_name VARCHAR(255) NOT NULL,
  threshold_value DECIMAL(18,4) DEFAULT NULL,
  remark VARCHAR(1000) DEFAULT NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (warning_parameter_id),
  UNIQUE KEY uk_sys_warning_legacy (tenant_id, legacy_warning_id),
  CONSTRAINT fk_sys_warning_tenant
    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sys_approval_categories (
  approval_category_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  legacy_category_id BIGINT NOT NULL,
  parent_category_id BIGINT DEFAULT NULL,
  name VARCHAR(255) NOT NULL,
  icon_class VARCHAR(255) DEFAULT NULL,
  attributes_text TEXT DEFAULT NULL,
  PRIMARY KEY (approval_category_id),
  UNIQUE KEY uk_sys_approval_category_legacy (tenant_id, legacy_category_id),
  CONSTRAINT fk_sys_approval_category_tenant
    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id),
  CONSTRAINT fk_sys_approval_category_parent
    FOREIGN KEY (parent_category_id) REFERENCES sys_approval_categories (approval_category_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sys_approval_processes (
  approval_process_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  approval_category_id BIGINT DEFAULT NULL,
  legacy_process_id BIGINT NOT NULL,
  code VARCHAR(128) DEFAULT NULL,
  name VARCHAR(255) NOT NULL,
  parent_process_id BIGINT DEFAULT NULL,
  role_id BIGINT DEFAULT NULL,
  legacy_role_id BIGINT DEFAULT NULL,
  role_name VARCHAR(255) DEFAULT NULL,
  sort_order INT NOT NULL DEFAULT 0,
  sequence_no INT DEFAULT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
  is_jump TINYINT(1) NOT NULL DEFAULT 0,
  remark VARCHAR(1000) DEFAULT NULL,
  PRIMARY KEY (approval_process_id),
  UNIQUE KEY uk_sys_approval_process_legacy (tenant_id, legacy_process_id),
  KEY ix_sys_approval_process_category (approval_category_id, sort_order),
  CONSTRAINT fk_sys_approval_process_tenant
    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id),
  CONSTRAINT fk_sys_approval_process_category
    FOREIGN KEY (approval_category_id) REFERENCES sys_approval_categories (approval_category_id),
  CONSTRAINT fk_sys_approval_process_parent
    FOREIGN KEY (parent_process_id) REFERENCES sys_approval_processes (approval_process_id),
  CONSTRAINT fk_sys_approval_process_role
    FOREIGN KEY (role_id) REFERENCES roles (role_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sys_sms_nodes (
  sms_node_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  legacy_node_id BIGINT NOT NULL,
  node_code VARCHAR(64) NOT NULL,
  node_name VARCHAR(255) NOT NULL,
  template_text TEXT DEFAULT NULL,
  sort_order INT NOT NULL DEFAULT 0,
  status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
  PRIMARY KEY (sms_node_id),
  UNIQUE KEY uk_sys_sms_node_code (tenant_id, node_code),
  UNIQUE KEY uk_sys_sms_node_legacy (tenant_id, legacy_node_id),
  CONSTRAINT fk_sys_sms_node_tenant
    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sys_sms_recipients (
  sms_node_id BIGINT NOT NULL,
  store_id BIGINT NOT NULL,
  user_id BIGINT DEFAULT NULL,
  legacy_user_id BIGINT NOT NULL,
  recipient_name VARCHAR(128) DEFAULT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (sms_node_id, store_id, legacy_user_id),
  CONSTRAINT fk_sys_sms_recipient_node
    FOREIGN KEY (sms_node_id) REFERENCES sys_sms_nodes (sms_node_id) ON DELETE CASCADE,
  CONSTRAINT fk_sys_sms_recipient_store
    FOREIGN KEY (store_id) REFERENCES stores (store_id),
  CONSTRAINT fk_sys_sms_recipient_user
    FOREIGN KEY (user_id) REFERENCES user_accounts (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sys_report_templates (
  report_template_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  legacy_template_id BIGINT NOT NULL,
  type_name VARCHAR(128) DEFAULT NULL,
  title VARCHAR(255) NOT NULL,
  memo VARCHAR(500) DEFAULT NULL,
  creator_name VARCHAR(128) DEFAULT NULL,
  legacy_created_at DATETIME DEFAULT NULL,
  sort_order INT NOT NULL DEFAULT 0,
  store_name VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (report_template_id),
  UNIQUE KEY uk_sys_report_template_legacy (tenant_id, legacy_template_id),
  CONSTRAINT fk_sys_report_template_tenant
    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sys_message_templates (
  message_template_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  legacy_template_id BIGINT DEFAULT NULL,
  template_name VARCHAR(255) NOT NULL,
  template_code VARCHAR(128) NOT NULL,
  external_template_id VARCHAR(255) DEFAULT NULL,
  type_name VARCHAR(128) DEFAULT NULL,
  template_fields TEXT DEFAULT NULL,
  explanation TEXT DEFAULT NULL,
  remark VARCHAR(1000) DEFAULT NULL,
  PRIMARY KEY (message_template_id),
  UNIQUE KEY uk_sys_message_template_code (tenant_id, template_code),
  CONSTRAINT fk_sys_message_template_tenant
    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sys_plan_tasks (
  plan_task_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  legacy_task_id BIGINT DEFAULT NULL,
  task_code VARCHAR(128) NOT NULL,
  task_title VARCHAR(255) NOT NULL,
  start_time DATETIME DEFAULT NULL,
  end_time DATETIME DEFAULT NULL,
  interval_days INT DEFAULT NULL,
  recipient_type VARCHAR(64) DEFAULT NULL,
  recipient_text TEXT DEFAULT NULL,
  message_content TEXT DEFAULT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
  PRIMARY KEY (plan_task_id),
  UNIQUE KEY uk_sys_plan_task_code (tenant_id, task_code),
  CONSTRAINT fk_sys_plan_task_tenant
    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sys_rebate_profiles (
  rebate_profile_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  minimum_sale_enabled TINYINT(1) NOT NULL DEFAULT 0,
  minimum_sale_amount DECIMAL(18,2) NOT NULL DEFAULT 0,
  rebate_mode VARCHAR(20) NOT NULL,
  rebate_rate_1 DECIMAL(18,4) NOT NULL DEFAULT 0,
  rebate_rate_2 DECIMAL(18,4) NOT NULL DEFAULT 0,
  rebate_rate_3 DECIMAL(18,4) NOT NULL DEFAULT 0,
  minimum_rebate_amount DECIMAL(18,2) NOT NULL DEFAULT 0,
  maximum_rebate_amount DECIMAL(18,2) NOT NULL DEFAULT 0,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (rebate_profile_id),
  UNIQUE KEY uk_sys_rebate_profile_tenant (tenant_id),
  CONSTRAINT fk_sys_rebate_profile_tenant
    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sys_rebate_category_settings (
  rebate_category_setting_id BIGINT NOT NULL AUTO_INCREMENT,
  rebate_profile_id BIGINT NOT NULL,
  category_code VARCHAR(32) NOT NULL,
  category_name VARCHAR(128) NOT NULL,
  enabled TINYINT(1) NOT NULL DEFAULT 1,
  calculation_mode VARCHAR(20) NOT NULL COMMENT 'percentage or fixed_amount',
  rebate_value DECIMAL(18,4) NOT NULL DEFAULT 0,
  input_hint VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (rebate_category_setting_id),
  UNIQUE KEY uk_sys_rebate_category (rebate_profile_id, category_code),
  CONSTRAINT fk_sys_rebate_category_profile
    FOREIGN KEY (rebate_profile_id) REFERENCES sys_rebate_profiles (rebate_profile_id)
      ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sys_club_profiles (
  club_profile_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  store_id BIGINT DEFAULT NULL,
  club_name VARCHAR(255) NOT NULL,
  city VARCHAR(128) DEFAULT NULL,
  address VARCHAR(500) DEFAULT NULL,
  telephone VARCHAR(64) DEFAULT NULL,
  introduction TEXT DEFAULT NULL,
  image_path VARCHAR(1000) DEFAULT NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (club_profile_id),
  UNIQUE KEY uk_sys_club_profile_scope (tenant_id, store_id),
  CONSTRAINT fk_sys_club_profile_tenant
    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id),
  CONSTRAINT fk_sys_club_profile_store
    FOREIGN KEY (store_id) REFERENCES stores (store_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
