-- MySQL 5.7.  Member assets are store-owned transactions; no seed data.
CREATE TABLE IF NOT EXISTS member_asset_accounts (
  account_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  store_id BIGINT NOT NULL,
  customer_id BIGINT NOT NULL,
  account_no VARCHAR(64) NOT NULL,
  balance DECIMAL(20,4) NOT NULL DEFAULT 0,
  frozen_amount DECIMAL(20,4) NOT NULL DEFAULT 0,
  points INT NOT NULL DEFAULT 0,
  status VARCHAR(24) NOT NULL DEFAULT 'ACTIVE',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (account_id),
  UNIQUE KEY uk_member_asset_account_customer (tenant_id, customer_id),
  UNIQUE KEY uk_member_asset_account_no (tenant_id, account_no),
  KEY idx_member_asset_account_store (tenant_id, store_id, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS member_asset_cards (
  card_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  store_id BIGINT NOT NULL,
  customer_id BIGINT NOT NULL,
  card_no VARCHAR(64) NOT NULL,
  card_name VARCHAR(128) NOT NULL,
  card_type VARCHAR(24) NOT NULL,
  initial_amount DECIMAL(20,4) NOT NULL DEFAULT 0,
  balance DECIMAL(20,4) NOT NULL DEFAULT 0,
  total_count INT NOT NULL DEFAULT 0,
  remaining_count INT NOT NULL DEFAULT 0,
  valid_to DATE NOT NULL,
  status VARCHAR(24) NOT NULL DEFAULT 'ACTIVE',
  created_by_user_id BIGINT DEFAULT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (card_id),
  UNIQUE KEY uk_member_asset_card_no (tenant_id, card_no),
  KEY idx_member_asset_card_store (tenant_id, store_id, status),
  KEY idx_member_asset_card_customer (tenant_id, customer_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS member_asset_transactions (
  transaction_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  store_id BIGINT NOT NULL,
  customer_id BIGINT NOT NULL,
  account_id BIGINT DEFAULT NULL,
  card_id BIGINT DEFAULT NULL,
  transaction_type VARCHAR(32) NOT NULL,
  amount DECIMAL(20,4) NOT NULL DEFAULT 0,
  count_delta INT NOT NULL DEFAULT 0,
  balance_after DECIMAL(20,4) DEFAULT NULL,
  remaining_count_after INT DEFAULT NULL,
  remark VARCHAR(255) DEFAULT NULL,
  created_by_user_id BIGINT DEFAULT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (transaction_id),
  KEY idx_member_asset_transaction_store (tenant_id, store_id, created_at),
  KEY idx_member_asset_transaction_customer (tenant_id, customer_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
