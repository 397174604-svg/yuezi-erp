CREATE TABLE IF NOT EXISTS finance_receipt_extensions (
  receipt_id BIGINT NOT NULL,
  receipt_kind VARCHAR(20) NOT NULL DEFAULT '收款单',
  gift_amount DECIMAL(20,4) NOT NULL DEFAULT 0,
  income_type VARCHAR(64) NULL,
  bank_name VARCHAR(128) NULL,
  bank_account VARCHAR(128) NULL,
  invoice_status VARCHAR(32) NOT NULL DEFAULT '未开票',
  coupon_code VARCHAR(128) NULL,
  document_date DATE NOT NULL,
  attachment_names TEXT NULL,
  fee_amount DECIMAL(20,4) NOT NULL DEFAULT 0,
  received_amount DECIMAL(20,4) NULL,
  writeoff_balance DECIMAL(20,4) NOT NULL DEFAULT 0,
  settled TINYINT(1) NOT NULL DEFAULT 0,
  source_no VARCHAR(128) NULL,
  customer_status VARCHAR(64) NULL,
  audit_remark VARCHAR(1000) NULL,
  created_by_user_id BIGINT NOT NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (receipt_id),
  KEY ix_finance_receipt_extension_creator (created_by_user_id),
  CONSTRAINT fk_finance_receipt_extension_receipt
    FOREIGN KEY (receipt_id) REFERENCES finance_receipts(receipt_id),
  CONSTRAINT fk_finance_receipt_extension_creator
    FOREIGN KEY (created_by_user_id) REFERENCES user_accounts(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS finance_writeoffs (
  writeoff_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  store_id BIGINT NOT NULL,
  receipt_id BIGINT NOT NULL,
  writeoff_type VARCHAR(64) NOT NULL,
  payment_method VARCHAR(64) NOT NULL,
  amount DECIMAL(20,4) NOT NULL,
  remark VARCHAR(1000) NULL,
  created_by_user_id BIGINT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (writeoff_id),
  KEY ix_finance_writeoff_receipt (receipt_id),
  KEY ix_finance_writeoff_store (tenant_id, store_id, created_at),
  CONSTRAINT fk_finance_writeoff_receipt
    FOREIGN KEY (receipt_id) REFERENCES finance_receipts(receipt_id),
  CONSTRAINT fk_finance_writeoff_store
    FOREIGN KEY (store_id) REFERENCES stores(store_id),
  CONSTRAINT fk_finance_writeoff_user
    FOREIGN KEY (created_by_user_id) REFERENCES user_accounts(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS finance_refund_extensions (
  refund_id BIGINT NOT NULL,
  refund_channel VARCHAR(64) NULL,
  audit_status VARCHAR(32) NOT NULL DEFAULT '待提交',
  audit_remark VARCHAR(1000) NULL,
  bank_name VARCHAR(128) NULL,
  bank_branch VARCHAR(255) NULL,
  bank_account VARCHAR(128) NULL,
  payment_remark VARCHAR(1000) NULL,
  cashier_user_id BIGINT NULL,
  created_by_user_id BIGINT NOT NULL,
  paid_by_user_id BIGINT NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (refund_id),
  CONSTRAINT fk_finance_refund_extension_refund
    FOREIGN KEY (refund_id) REFERENCES refund_orders(refund_id),
  CONSTRAINT fk_finance_refund_extension_creator
    FOREIGN KEY (created_by_user_id) REFERENCES user_accounts(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS finance_expense_extensions (
  expense_id BIGINT NOT NULL,
  expense_name VARCHAR(255) NULL,
  applicant_user_id BIGINT NOT NULL,
  department_id BIGINT NULL,
  department_name VARCHAR(255) NULL,
  payout_type VARCHAR(64) NULL,
  attachment_names TEXT NULL,
  invoice_type VARCHAR(64) NULL,
  audit_remark VARCHAR(1000) NULL,
  paid_by_user_id BIGINT NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (expense_id),
  KEY ix_finance_expense_applicant (applicant_user_id),
  CONSTRAINT fk_finance_expense_extension_expense
    FOREIGN KEY (expense_id) REFERENCES expense_orders(expense_id),
  CONSTRAINT fk_finance_expense_extension_applicant
    FOREIGN KEY (applicant_user_id) REFERENCES user_accounts(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS finance_material_budgets (
  budget_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  store_id BIGINT NOT NULL,
  budget_no VARCHAR(64) NOT NULL,
  budget_date DATE NOT NULL,
  department_id BIGINT NULL,
  department_name VARCHAR(255) NOT NULL,
  total_quantity DECIMAL(20,4) NOT NULL DEFAULT 0,
  total_amount DECIMAL(20,4) NOT NULL DEFAULT 0,
  status VARCHAR(32) NOT NULL DEFAULT '待提交',
  purchase_plan_no VARCHAR(64) NULL,
  remark VARCHAR(1000) NULL,
  created_by_user_id BIGINT NOT NULL,
  approved_by_user_id BIGINT NULL,
  approved_at DATETIME NULL,
  version BIGINT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP,
  deleted_at DATETIME NULL,
  PRIMARY KEY (budget_id),
  UNIQUE KEY uk_finance_material_budget_no (tenant_id, budget_no),
  KEY ix_finance_material_budget_store (tenant_id, store_id, status),
  CONSTRAINT fk_finance_material_budget_store
    FOREIGN KEY (store_id) REFERENCES stores(store_id),
  CONSTRAINT fk_finance_material_budget_creator
    FOREIGN KEY (created_by_user_id) REFERENCES user_accounts(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS finance_debt_audits (
  debt_audit_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  store_id BIGINT NOT NULL,
  booking_id BIGINT NULL,
  contract_id BIGINT NULL,
  customer_id BIGINT NOT NULL,
  room_id BIGINT NULL,
  reason VARCHAR(1000) NULL,
  audit_status VARCHAR(32) NOT NULL DEFAULT '待审核',
  audit_remark VARCHAR(1000) NULL,
  created_by_user_id BIGINT NOT NULL,
  approved_by_user_id BIGINT NULL,
  approved_at DATETIME NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (debt_audit_id),
  KEY ix_finance_debt_audit_store (tenant_id, store_id, audit_status),
  KEY ix_finance_debt_audit_customer (customer_id),
  CONSTRAINT fk_finance_debt_audit_store
    FOREIGN KEY (store_id) REFERENCES stores(store_id),
  CONSTRAINT fk_finance_debt_audit_customer
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS finance_exchange_audits (
  exchange_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  store_id BIGINT NOT NULL,
  exchange_no VARCHAR(64) NOT NULL,
  source_order_no VARCHAR(64) NULL,
  return_order_no VARCHAR(64) NULL,
  customer_id BIGINT NULL,
  exchange_type VARCHAR(64) NULL,
  applicant_user_id BIGINT NULL,
  applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  audit_status VARCHAR(32) NOT NULL DEFAULT '待审核',
  outbound_status VARCHAR(32) NOT NULL DEFAULT '未出库',
  warehouse_name VARCHAR(255) NULL,
  difference_amount DECIMAL(20,4) NOT NULL DEFAULT 0,
  approved_by_user_id BIGINT NULL,
  approved_at DATETIME NULL,
  audit_remark VARCHAR(1000) NULL,
  deleted_at DATETIME NULL,
  PRIMARY KEY (exchange_id),
  UNIQUE KEY uk_finance_exchange_no (tenant_id, exchange_no),
  KEY ix_finance_exchange_store (tenant_id, store_id, audit_status),
  CONSTRAINT fk_finance_exchange_store
    FOREIGN KEY (store_id) REFERENCES stores(store_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS finance_payments (
  payment_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  store_id BIGINT NOT NULL,
  payment_no VARCHAR(64) NOT NULL,
  project_name VARCHAR(255) NOT NULL,
  payee VARCHAR(255) NOT NULL,
  amount DECIMAL(20,4) NOT NULL,
  commission_standard VARCHAR(64) NULL,
  payment_status VARCHAR(32) NOT NULL DEFAULT '待打款',
  audit_status VARCHAR(32) NOT NULL DEFAULT '审核中',
  source_type VARCHAR(64) NULL,
  source_id BIGINT NULL,
  created_by_user_id BIGINT NOT NULL,
  approved_by_user_id BIGINT NULL,
  approved_at DATETIME NULL,
  paid_by_user_id BIGINT NULL,
  paid_at DATETIME NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP,
  deleted_at DATETIME NULL,
  PRIMARY KEY (payment_id),
  UNIQUE KEY uk_finance_payment_no (tenant_id, payment_no),
  KEY ix_finance_payment_store (tenant_id, store_id, payment_status),
  CONSTRAINT fk_finance_payment_store
    FOREIGN KEY (store_id) REFERENCES stores(store_id),
  CONSTRAINT fk_finance_payment_creator
    FOREIGN KEY (created_by_user_id) REFERENCES user_accounts(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

