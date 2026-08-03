-- MySQL 5.7
-- Manual external-statement registration and receipt reconciliation.
-- This table records user-supplied bank/POS/WeChat/Alipay references only;
-- it does not claim that an external payment gateway has been connected.

CREATE TABLE IF NOT EXISTS finance_reconciliations (
  reconciliation_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  store_id BIGINT NOT NULL,
  receipt_id BIGINT NOT NULL,
  external_channel VARCHAR(64) NOT NULL,
  external_reference VARCHAR(128) NOT NULL,
  external_amount DECIMAL(20,4) NOT NULL,
  system_amount DECIMAL(20,4) NOT NULL,
  difference_amount DECIMAL(20,4) NOT NULL,
  transaction_date DATE NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT '待匹配',
  remark VARCHAR(1000) NULL,
  created_by_user_id BIGINT NOT NULL,
  matched_by_user_id BIGINT NULL,
  matched_at DATETIME NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP,
  deleted_at DATETIME NULL,
  PRIMARY KEY (reconciliation_id),
  UNIQUE KEY uk_finance_reconciliation_external (
    tenant_id, store_id, external_channel, external_reference
  ),
  KEY ix_finance_reconciliation_store (
    tenant_id, store_id, status, transaction_date
  ),
  KEY ix_finance_reconciliation_receipt (receipt_id),
  CONSTRAINT fk_finance_reconciliation_store
    FOREIGN KEY (store_id) REFERENCES stores(store_id),
  CONSTRAINT fk_finance_reconciliation_receipt
    FOREIGN KEY (receipt_id) REFERENCES finance_receipts(receipt_id),
  CONSTRAINT fk_finance_reconciliation_creator
    FOREIGN KEY (created_by_user_id) REFERENCES user_accounts(user_id),
  CONSTRAINT fk_finance_reconciliation_matcher
    FOREIGN KEY (matched_by_user_id) REFERENCES user_accounts(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
