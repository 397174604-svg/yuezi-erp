-- MySQL 5.7
-- Normalized package version, pricing, contract snapshot and entitlement model.
-- No package prices are seeded here: source-document OCR values still require
-- business approval before they become selectable production master data.

CREATE TABLE IF NOT EXISTS package_products (
  package_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  package_code VARCHAR(64) NOT NULL,
  package_name VARCHAR(160) NOT NULL,
  package_category VARCHAR(64) NOT NULL DEFAULT '月子套餐',
  legacy_bundle_id BIGINT DEFAULT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'DRAFT',
  sort_order INT NOT NULL DEFAULT 0,
  note VARCHAR(1000) DEFAULT NULL,
  version BIGINT NOT NULL DEFAULT 0,
  created_by_user_id BIGINT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP,
  deleted_at DATETIME DEFAULT NULL,
  PRIMARY KEY (package_id),
  UNIQUE KEY uk_package_product_code (tenant_id, package_code),
  KEY ix_package_product_status (tenant_id, status, sort_order),
  KEY ix_package_product_legacy (legacy_bundle_id),
  KEY fk_package_product_creator (created_by_user_id),
  CONSTRAINT fk_package_product_tenant
    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id),
  CONSTRAINT fk_package_product_creator
    FOREIGN KEY (created_by_user_id) REFERENCES user_accounts (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS package_versions (
  package_version_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  package_id BIGINT NOT NULL,
  version_no VARCHAR(32) NOT NULL,
  effective_from DATE NOT NULL,
  effective_to DATE DEFAULT NULL,
  version_status VARCHAR(20) NOT NULL DEFAULT 'DRAFT',
  source_type VARCHAR(32) NOT NULL DEFAULT 'MANUAL',
  evidence_note VARCHAR(1000) DEFAULT NULL,
  published_at DATETIME DEFAULT NULL,
  published_by_user_id BIGINT DEFAULT NULL,
  created_by_user_id BIGINT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (package_version_id),
  UNIQUE KEY uk_package_version_no (package_id, version_no),
  KEY ix_package_version_effective
    (tenant_id, version_status, effective_from, effective_to),
  KEY fk_package_version_publisher (published_by_user_id),
  KEY fk_package_version_creator (created_by_user_id),
  CONSTRAINT fk_package_version_tenant
    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id),
  CONSTRAINT fk_package_version_product
    FOREIGN KEY (package_id) REFERENCES package_products (package_id),
  CONSTRAINT fk_package_version_publisher
    FOREIGN KEY (published_by_user_id) REFERENCES user_accounts (user_id),
  CONSTRAINT fk_package_version_creator
    FOREIGN KEY (created_by_user_id) REFERENCES user_accounts (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS service_projects (
  service_project_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  project_code VARCHAR(64) NOT NULL,
  project_name VARCHAR(160) NOT NULL,
  target_module VARCHAR(32) NOT NULL,
  project_category VARCHAR(64) DEFAULT NULL,
  unit VARCHAR(32) NOT NULL DEFAULT '次',
  legacy_item_id BIGINT DEFAULT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
  note VARCHAR(1000) DEFAULT NULL,
  version BIGINT NOT NULL DEFAULT 0,
  created_by_user_id BIGINT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP,
  deleted_at DATETIME DEFAULT NULL,
  PRIMARY KEY (service_project_id),
  UNIQUE KEY uk_service_project_code (tenant_id, project_code),
  KEY ix_service_project_module
    (tenant_id, target_module, status, project_category),
  KEY ix_service_project_legacy (legacy_item_id),
  KEY fk_service_project_creator (created_by_user_id),
  CONSTRAINT fk_service_project_tenant
    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id),
  CONSTRAINT fk_service_project_creator
    FOREIGN KEY (created_by_user_id) REFERENCES user_accounts (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS package_price_rules (
  price_rule_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  package_version_id BIGINT NOT NULL,
  store_id BIGINT NOT NULL,
  room_type_id BIGINT NOT NULL,
  stay_days INT NOT NULL,
  reference_amount DECIMAL(20,4) NOT NULL,
  currency_code CHAR(3) NOT NULL DEFAULT 'CNY',
  effective_from DATE NOT NULL,
  effective_to DATE DEFAULT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'DRAFT',
  version BIGINT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (price_rule_id),
  UNIQUE KEY uk_package_price_start (
    package_version_id, store_id, room_type_id, stay_days, effective_from
  ),
  KEY ix_package_price_lookup (
    tenant_id, store_id, room_type_id, stay_days, status,
    effective_from, effective_to
  ),
  CONSTRAINT fk_package_price_tenant
    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id),
  CONSTRAINT fk_package_price_version
    FOREIGN KEY (package_version_id)
    REFERENCES package_versions (package_version_id),
  CONSTRAINT fk_package_price_store
    FOREIGN KEY (store_id) REFERENCES stores (store_id),
  CONSTRAINT fk_package_price_room_type
    FOREIGN KEY (room_type_id) REFERENCES room_types (room_type_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS package_entitlement_rules (
  entitlement_rule_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  package_version_id BIGINT NOT NULL,
  service_project_id BIGINT NOT NULL,
  entitlement_mode VARCHAR(24) NOT NULL DEFAULT 'COUNT',
  granted_quantity DECIMAL(20,4) DEFAULT NULL,
  unlimited_flag TINYINT(1) NOT NULL DEFAULT 0,
  per_item_limit DECIMAL(20,4) DEFAULT NULL,
  choice_group_code VARCHAR(64) DEFAULT NULL,
  valid_days INT DEFAULT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'DRAFT',
  sort_order INT NOT NULL DEFAULT 0,
  note VARCHAR(1000) DEFAULT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (entitlement_rule_id),
  UNIQUE KEY uk_package_entitlement_project (
    package_version_id, service_project_id, choice_group_code
  ),
  KEY ix_package_entitlement_module
    (tenant_id, package_version_id, status, sort_order),
  CONSTRAINT fk_package_entitlement_tenant
    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id),
  CONSTRAINT fk_package_entitlement_version
    FOREIGN KEY (package_version_id)
    REFERENCES package_versions (package_version_id),
  CONSTRAINT fk_package_entitlement_project
    FOREIGN KEY (service_project_id)
    REFERENCES service_projects (service_project_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS contract_package_snapshots (
  package_snapshot_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  contract_id BIGINT NOT NULL,
  package_version_id BIGINT NOT NULL,
  price_rule_id BIGINT NOT NULL,
  package_code VARCHAR(64) NOT NULL,
  package_name VARCHAR(160) NOT NULL,
  version_no VARCHAR(32) NOT NULL,
  store_id BIGINT NOT NULL,
  room_type_id BIGINT NOT NULL,
  stay_days INT NOT NULL,
  reference_amount DECIMAL(20,4) NOT NULL,
  deal_amount DECIMAL(20,4) NOT NULL,
  currency_code CHAR(3) NOT NULL DEFAULT 'CNY',
  effective_from DATE NOT NULL,
  effective_to DATE DEFAULT NULL,
  snapshot_json TEXT DEFAULT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (package_snapshot_id),
  UNIQUE KEY uk_contract_package_snapshot (contract_id),
  KEY ix_contract_package_version (package_version_id, contract_id),
  KEY fk_contract_package_price (price_rule_id),
  KEY fk_contract_package_store (store_id),
  KEY fk_contract_package_room_type (room_type_id),
  CONSTRAINT fk_contract_package_tenant
    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id),
  CONSTRAINT fk_contract_package_contract
    FOREIGN KEY (contract_id) REFERENCES contracts (contract_id),
  CONSTRAINT fk_contract_package_version
    FOREIGN KEY (package_version_id)
    REFERENCES package_versions (package_version_id),
  CONSTRAINT fk_contract_package_price
    FOREIGN KEY (price_rule_id) REFERENCES package_price_rules (price_rule_id),
  CONSTRAINT fk_contract_package_store
    FOREIGN KEY (store_id) REFERENCES stores (store_id),
  CONSTRAINT fk_contract_package_room_type
    FOREIGN KEY (room_type_id) REFERENCES room_types (room_type_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS contract_entitlement_snapshots (
  entitlement_snapshot_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  contract_id BIGINT NOT NULL,
  package_snapshot_id BIGINT NOT NULL,
  source_rule_id BIGINT NOT NULL,
  service_project_id BIGINT NOT NULL,
  project_code VARCHAR(64) NOT NULL,
  project_name VARCHAR(160) NOT NULL,
  target_module VARCHAR(32) NOT NULL,
  entitlement_mode VARCHAR(24) NOT NULL,
  granted_quantity DECIMAL(20,4) DEFAULT NULL,
  unlimited_flag TINYINT(1) NOT NULL DEFAULT 0,
  per_item_limit DECIMAL(20,4) DEFAULT NULL,
  choice_group_code VARCHAR(64) DEFAULT NULL,
  valid_days INT DEFAULT NULL,
  grant_status VARCHAR(20) NOT NULL DEFAULT 'FROZEN',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (entitlement_snapshot_id),
  UNIQUE KEY uk_contract_entitlement_rule (contract_id, source_rule_id),
  KEY ix_contract_entitlement_status
    (tenant_id, contract_id, grant_status, target_module),
  KEY fk_contract_entitlement_package_snapshot (package_snapshot_id),
  KEY fk_contract_entitlement_project (service_project_id),
  CONSTRAINT fk_contract_entitlement_tenant
    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id),
  CONSTRAINT fk_contract_entitlement_contract
    FOREIGN KEY (contract_id) REFERENCES contracts (contract_id),
  CONSTRAINT fk_contract_entitlement_package_snapshot
    FOREIGN KEY (package_snapshot_id)
    REFERENCES contract_package_snapshots (package_snapshot_id),
  CONSTRAINT fk_contract_entitlement_rule
    FOREIGN KEY (source_rule_id)
    REFERENCES package_entitlement_rules (entitlement_rule_id),
  CONSTRAINT fk_contract_entitlement_project
    FOREIGN KEY (service_project_id)
    REFERENCES service_projects (service_project_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS customer_service_entitlements (
  customer_entitlement_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  store_id BIGINT NOT NULL,
  customer_id BIGINT NOT NULL,
  contract_id BIGINT NOT NULL,
  entitlement_snapshot_id BIGINT NOT NULL,
  service_project_id BIGINT NOT NULL,
  target_module VARCHAR(32) NOT NULL,
  entitlement_mode VARCHAR(24) NOT NULL,
  granted_quantity DECIMAL(20,4) DEFAULT NULL,
  used_quantity DECIMAL(20,4) NOT NULL DEFAULT 0,
  reserved_quantity DECIMAL(20,4) NOT NULL DEFAULT 0,
  unlimited_flag TINYINT(1) NOT NULL DEFAULT 0,
  valid_from DATE NOT NULL,
  valid_to DATE DEFAULT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
  version BIGINT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (customer_entitlement_id),
  UNIQUE KEY uk_customer_entitlement_snapshot (entitlement_snapshot_id),
  KEY ix_customer_entitlement_lookup
    (tenant_id, customer_id, target_module, status, valid_to),
  KEY ix_customer_entitlement_contract (contract_id, status),
  KEY fk_customer_entitlement_store (store_id),
  KEY fk_customer_entitlement_project (service_project_id),
  CONSTRAINT fk_customer_entitlement_tenant
    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id),
  CONSTRAINT fk_customer_entitlement_store
    FOREIGN KEY (store_id) REFERENCES stores (store_id),
  CONSTRAINT fk_customer_entitlement_customer
    FOREIGN KEY (customer_id) REFERENCES customers (customer_id),
  CONSTRAINT fk_customer_entitlement_contract
    FOREIGN KEY (contract_id) REFERENCES contracts (contract_id),
  CONSTRAINT fk_customer_entitlement_snapshot
    FOREIGN KEY (entitlement_snapshot_id)
    REFERENCES contract_entitlement_snapshots (entitlement_snapshot_id),
  CONSTRAINT fk_customer_entitlement_project
    FOREIGN KEY (service_project_id)
    REFERENCES service_projects (service_project_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS customer_entitlement_ledger (
  ledger_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  customer_entitlement_id BIGINT NOT NULL,
  transaction_type VARCHAR(24) NOT NULL,
  quantity_change DECIMAL(20,4) NOT NULL,
  balance_after DECIMAL(20,4) DEFAULT NULL,
  business_type VARCHAR(32) NOT NULL,
  business_id BIGINT NOT NULL,
  operator_user_id BIGINT NOT NULL,
  remark VARCHAR(1000) DEFAULT NULL,
  occurred_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (ledger_id),
  UNIQUE KEY uk_entitlement_ledger_business (
    customer_entitlement_id, transaction_type, business_type, business_id
  ),
  KEY ix_entitlement_ledger_time
    (tenant_id, customer_entitlement_id, occurred_at),
  KEY fk_entitlement_ledger_operator (operator_user_id),
  CONSTRAINT fk_entitlement_ledger_tenant
    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id),
  CONSTRAINT fk_entitlement_ledger_entitlement
    FOREIGN KEY (customer_entitlement_id)
    REFERENCES customer_service_entitlements (customer_entitlement_id),
  CONSTRAINT fk_entitlement_ledger_operator
    FOREIGN KEY (operator_user_id) REFERENCES user_accounts (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

ALTER TABLE contracts
  ADD COLUMN package_version_id BIGINT DEFAULT NULL AFTER package_name,
  ADD COLUMN package_price_rule_id BIGINT DEFAULT NULL
    AFTER package_version_id,
  ADD KEY ix_contract_package_version (package_version_id),
  ADD KEY ix_contract_package_price_rule (package_price_rule_id),
  ADD CONSTRAINT fk_contract_selected_package_version
    FOREIGN KEY (package_version_id)
    REFERENCES package_versions (package_version_id),
  ADD CONSTRAINT fk_contract_selected_package_price
    FOREIGN KEY (package_price_rule_id)
    REFERENCES package_price_rules (price_rule_id);

ALTER TABLE customer_entry_profiles
  ADD COLUMN intended_package_version_id BIGINT DEFAULT NULL
    AFTER intended_package_id,
  ADD COLUMN intended_package_price_rule_id BIGINT DEFAULT NULL
    AFTER intended_package_version_id,
  ADD KEY ix_customer_entry_package_version
    (intended_package_version_id),
  ADD KEY ix_customer_entry_package_price_rule
    (intended_package_price_rule_id),
  ADD CONSTRAINT fk_customer_entry_package_version
    FOREIGN KEY (intended_package_version_id)
    REFERENCES package_versions (package_version_id),
  ADD CONSTRAINT fk_customer_entry_package_price_rule
    FOREIGN KEY (intended_package_price_rule_id)
    REFERENCES package_price_rules (price_rule_id);
