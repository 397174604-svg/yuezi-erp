-- MySQL 5.7
-- F059 member assets. Member accounts are tenant-shared, while every issue,
-- top-up, deduction and consumption records the concrete occurrence store.

CREATE TABLE IF NOT EXISTS member_asset_accounts (
  account_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  customer_id BIGINT NOT NULL,
  account_no VARCHAR(64) NOT NULL,
  balance DECIMAL(20,4) NOT NULL DEFAULT 0,
  frozen_amount DECIMAL(20,4) NOT NULL DEFAULT 0,
  points BIGINT NOT NULL DEFAULT 0,
  status VARCHAR(20) NOT NULL DEFAULT '正常',
  version BIGINT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (account_id),
  UNIQUE KEY uk_member_asset_account_customer (tenant_id, customer_id),
  UNIQUE KEY uk_member_asset_account_no (tenant_id, account_no),
  CONSTRAINT fk_member_asset_account_tenant
    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id),
  CONSTRAINT fk_member_asset_account_customer
    FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS member_asset_cards (
  card_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  customer_id BIGINT NOT NULL,
  issue_store_id BIGINT NOT NULL,
  package_id BIGINT DEFAULT NULL,
  card_no VARCHAR(64) NOT NULL,
  card_name VARCHAR(160) NOT NULL,
  card_type VARCHAR(32) NOT NULL,
  issue_amount DECIMAL(20,4) NOT NULL DEFAULT 0,
  balance DECIMAL(20,4) NOT NULL DEFAULT 0,
  total_count INT NOT NULL DEFAULT 0,
  remaining_count INT NOT NULL DEFAULT 0,
  valid_to DATE DEFAULT NULL,
  status VARCHAR(20) NOT NULL DEFAULT '正常',
  version BIGINT NOT NULL DEFAULT 0,
  created_by_user_id BIGINT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  deleted_at DATETIME DEFAULT NULL,
  PRIMARY KEY (card_id),
  UNIQUE KEY uk_member_asset_card_no (tenant_id, card_no),
  KEY ix_member_asset_card_customer (tenant_id, customer_id, status),
  KEY ix_member_asset_card_store (tenant_id, issue_store_id, status),
  CONSTRAINT fk_member_asset_card_tenant
    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id),
  CONSTRAINT fk_member_asset_card_customer
    FOREIGN KEY (customer_id) REFERENCES customers (customer_id),
  CONSTRAINT fk_member_asset_card_store
    FOREIGN KEY (issue_store_id) REFERENCES stores (store_id),
  CONSTRAINT fk_member_asset_card_creator
    FOREIGN KEY (created_by_user_id) REFERENCES user_accounts (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS member_asset_transactions (
  transaction_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  store_id BIGINT NOT NULL,
  customer_id BIGINT NOT NULL,
  account_id BIGINT DEFAULT NULL,
  card_id BIGINT DEFAULT NULL,
  transaction_no VARCHAR(64) NOT NULL,
  transaction_type VARCHAR(32) NOT NULL,
  amount DECIMAL(20,4) NOT NULL DEFAULT 0,
  count_delta INT NOT NULL DEFAULT 0,
  balance_after DECIMAL(20,4) DEFAULT NULL,
  remaining_count_after INT DEFAULT NULL,
  operator_user_id BIGINT NOT NULL,
  remark VARCHAR(500) DEFAULT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (transaction_id),
  UNIQUE KEY uk_member_asset_transaction_no (tenant_id, transaction_no),
  KEY ix_member_asset_transaction_customer (tenant_id, customer_id, created_at),
  KEY ix_member_asset_transaction_store (tenant_id, store_id, created_at),
  CONSTRAINT fk_member_asset_transaction_tenant
    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id),
  CONSTRAINT fk_member_asset_transaction_store
    FOREIGN KEY (store_id) REFERENCES stores (store_id),
  CONSTRAINT fk_member_asset_transaction_customer
    FOREIGN KEY (customer_id) REFERENCES customers (customer_id),
  CONSTRAINT fk_member_asset_transaction_account
    FOREIGN KEY (account_id) REFERENCES member_asset_accounts (account_id),
  CONSTRAINT fk_member_asset_transaction_card
    FOREIGN KEY (card_id) REFERENCES member_asset_cards (card_id),
  CONSTRAINT fk_member_asset_transaction_operator
    FOREIGN KEY (operator_user_id) REFERENCES user_accounts (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
