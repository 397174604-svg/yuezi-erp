-- P1 minimal local workflows.  Neither table connects to an online payment
-- gateway or an electronic-signature provider.

CREATE TABLE IF NOT EXISTS erp_count_card_extensions (
  card_id BIGINT NOT NULL,
  tenant_id BIGINT NOT NULL,
  store_id BIGINT NOT NULL,
  card_no VARCHAR(64) NOT NULL,
  receipt_id BIGINT NOT NULL,
  lifecycle_status VARCHAR(32) NOT NULL DEFAULT '待启用',
  activated_by_user_id BIGINT NULL,
  activated_at DATETIME NULL,
  deactivated_by_user_id BIGINT NULL,
  deactivated_at DATETIME NULL,
  created_by_user_id BIGINT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (card_id),
  UNIQUE KEY uk_erp_count_card_no (tenant_id, card_no),
  UNIQUE KEY uk_erp_count_card_receipt (receipt_id),
  KEY ix_erp_count_card_store (tenant_id, store_id, lifecycle_status),
  CONSTRAINT fk_erp_count_card_extension_card
    FOREIGN KEY (card_id) REFERENCES count_cards(card_id),
  CONSTRAINT fk_erp_count_card_extension_store
    FOREIGN KEY (store_id) REFERENCES stores(store_id),
  CONSTRAINT fk_erp_count_card_extension_receipt
    FOREIGN KEY (receipt_id) REFERENCES finance_receipts(receipt_id),
  CONSTRAINT fk_erp_count_card_extension_creator
    FOREIGN KEY (created_by_user_id) REFERENCES user_accounts(user_id),
  CONSTRAINT fk_erp_count_card_extension_activator
    FOREIGN KEY (activated_by_user_id) REFERENCES user_accounts(user_id),
  CONSTRAINT fk_erp_count_card_extension_deactivator
    FOREIGN KEY (deactivated_by_user_id) REFERENCES user_accounts(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sales_contract_sign_archives (
  archive_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  store_id BIGINT NOT NULL,
  contract_id BIGINT NOT NULL,
  archive_no VARCHAR(64) NOT NULL,
  archive_status VARCHAR(32) NOT NULL DEFAULT '线下已归档',
  signing_mode VARCHAR(64) NOT NULL DEFAULT '线下纸质签署',
  signed_at DATE NOT NULL,
  archive_reference VARCHAR(128) NOT NULL,
  original_location VARCHAR(255) NOT NULL,
  void_reason VARCHAR(500) NULL,
  archived_by_user_id BIGINT NOT NULL,
  archived_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  voided_by_user_id BIGINT NULL,
  voided_at DATETIME NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (archive_id),
  UNIQUE KEY uk_contract_sign_archive_contract (contract_id),
  UNIQUE KEY uk_contract_sign_archive_no (tenant_id, archive_no),
  KEY ix_contract_sign_archive_store (tenant_id, store_id, archive_status),
  CONSTRAINT fk_contract_sign_archive_store
    FOREIGN KEY (store_id) REFERENCES stores(store_id),
  CONSTRAINT fk_contract_sign_archive_contract
    FOREIGN KEY (contract_id) REFERENCES contracts(contract_id),
  CONSTRAINT fk_contract_sign_archive_actor
    FOREIGN KEY (archived_by_user_id) REFERENCES user_accounts(user_id),
  CONSTRAINT fk_contract_sign_archive_void_actor
    FOREIGN KEY (voided_by_user_id) REFERENCES user_accounts(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
