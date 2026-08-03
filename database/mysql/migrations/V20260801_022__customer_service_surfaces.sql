-- MySQL 5.7
-- F005/F043/F084/F094 customer-service records and immutable handling logs.

CREATE TABLE IF NOT EXISTS customer_service_records (
  record_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  store_id BIGINT NULL,
  feature_code VARCHAR(8) NOT NULL,
  record_no VARCHAR(64) NOT NULL,
  subject VARCHAR(255) NOT NULL,
  contact_name VARCHAR(128) NULL,
  mobile VARCHAR(32) NULL,
  category VARCHAR(64) NULL,
  channel VARCHAR(64) NULL,
  priority VARCHAR(32) NOT NULL DEFAULT '普通',
  status VARCHAR(32) NOT NULL,
  content TEXT NULL,
  payload_json LONGTEXT NULL,
  external_status VARCHAR(32) NOT NULL DEFAULT 'NOT_REQUIRED',
  assigned_user_id BIGINT NULL,
  created_by_user_id BIGINT NOT NULL,
  updated_by_user_id BIGINT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  deleted_at DATETIME NULL,
  PRIMARY KEY (record_id),
  UNIQUE KEY uk_customer_service_no (tenant_id, feature_code, record_no),
  KEY ix_customer_service_scope (tenant_id, feature_code, store_id, status),
  KEY ix_customer_service_updated (tenant_id, feature_code, updated_at),
  CONSTRAINT fk_customer_service_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id),
  CONSTRAINT fk_customer_service_store FOREIGN KEY (store_id) REFERENCES stores(store_id),
  CONSTRAINT fk_customer_service_assignee FOREIGN KEY (assigned_user_id) REFERENCES user_accounts(user_id),
  CONSTRAINT fk_customer_service_creator FOREIGN KEY (created_by_user_id) REFERENCES user_accounts(user_id),
  CONSTRAINT fk_customer_service_updater FOREIGN KEY (updated_by_user_id) REFERENCES user_accounts(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS customer_service_logs (
  log_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  record_id BIGINT NOT NULL,
  action_code VARCHAR(32) NOT NULL,
  before_status VARCHAR(32) NULL,
  after_status VARCHAR(32) NULL,
  note TEXT NULL,
  actor_user_id BIGINT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (log_id),
  KEY ix_customer_service_log (tenant_id, record_id, created_at),
  CONSTRAINT fk_customer_service_log_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id),
  CONSTRAINT fk_customer_service_log_record FOREIGN KEY (record_id) REFERENCES customer_service_records(record_id),
  CONSTRAINT fk_customer_service_log_actor FOREIGN KEY (actor_user_id) REFERENCES user_accounts(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
