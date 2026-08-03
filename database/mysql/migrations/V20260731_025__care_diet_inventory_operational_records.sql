-- MySQL 5.7
-- Durable, store-scoped workflow records for the P0 nursing, diet and
-- inventory surfaces that do not yet have a safe one-to-one legacy write
-- model.  The payload stores the audited form fields; workflow state and
-- tenancy stay in first-class columns so cross-store access can be enforced.

CREATE TABLE IF NOT EXISTS erp_operational_records (
  record_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  store_id BIGINT NOT NULL,
  module_code VARCHAR(24) NOT NULL,
  resource_code VARCHAR(64) NOT NULL,
  business_no VARCHAR(64) NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT '草稿',
  payload_json LONGTEXT NOT NULL,
  created_by_user_id BIGINT NOT NULL,
  updated_by_user_id BIGINT NOT NULL,
  version BIGINT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  deleted_at DATETIME DEFAULT NULL,
  PRIMARY KEY (record_id),
  UNIQUE KEY uk_operational_business_no (
    tenant_id, module_code, resource_code, business_no
  ),
  KEY ix_operational_scope (
    tenant_id, store_id, module_code, resource_code, deleted_at
  ),
  KEY ix_operational_status (
    tenant_id, module_code, resource_code, status, updated_at
  ),
  CONSTRAINT fk_operational_tenant
    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id),
  CONSTRAINT fk_operational_store
    FOREIGN KEY (store_id) REFERENCES stores (store_id),
  CONSTRAINT fk_operational_creator
    FOREIGN KEY (created_by_user_id) REFERENCES user_accounts (user_id),
  CONSTRAINT fk_operational_updater
    FOREIGN KEY (updated_by_user_id) REFERENCES user_accounts (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
