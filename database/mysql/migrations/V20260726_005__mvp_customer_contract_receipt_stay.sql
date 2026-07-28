-- MySQL 5.7
-- Minimal integrated business loop:
-- customer -> contract approval -> receipt approval -> room booking -> check-in.

ALTER TABLE customers
  ADD COLUMN customer_no VARCHAR(32) DEFAULT NULL AFTER customer_id,
  ADD COLUMN sales_staff_id BIGINT DEFAULT NULL AFTER store_id,
  ADD COLUMN birthday DATE DEFAULT NULL AFTER age,
  ADD COLUMN remark VARCHAR(1000) DEFAULT NULL AFTER level,
  ADD COLUMN created_by_user_id BIGINT DEFAULT NULL AFTER created_by,
  ADD UNIQUE KEY uk_customer_tenant_no (tenant_id, customer_no),
  ADD KEY ix_customer_sales_staff (sales_staff_id),
  ADD KEY ix_customer_created_by_user (created_by_user_id),
  ADD CONSTRAINT fk_customer_sales_staff
    FOREIGN KEY (sales_staff_id) REFERENCES staff (staff_id),
  ADD CONSTRAINT fk_customer_created_by_user
    FOREIGN KEY (created_by_user_id) REFERENCES user_accounts (user_id);

ALTER TABLE contracts
  ADD COLUMN contract_type VARCHAR(32) NOT NULL DEFAULT '月子合同' AFTER contract_no,
  ADD COLUMN reference_amount DECIMAL(20,4) DEFAULT NULL AFTER package_name,
  ADD COLUMN expected_check_in DATE DEFAULT NULL AFTER days,
  ADD COLUMN expected_check_out DATE DEFAULT NULL AFTER expected_check_in,
  ADD COLUMN approved_at DATETIME DEFAULT NULL AFTER status,
  ADD COLUMN approved_by_user_id BIGINT DEFAULT NULL AFTER approved_at,
  ADD COLUMN created_by_user_id BIGINT DEFAULT NULL AFTER approved_by_user_id,
  ADD COLUMN version BIGINT NOT NULL DEFAULT 0 AFTER note,
  ADD UNIQUE KEY uk_contract_tenant_no (tenant_id, contract_no(64)),
  ADD KEY ix_contract_customer (customer_id, status),
  ADD KEY ix_contract_approved_by (approved_by_user_id),
  ADD KEY ix_contract_created_by (created_by_user_id),
  ADD CONSTRAINT fk_contract_approved_by
    FOREIGN KEY (approved_by_user_id) REFERENCES user_accounts (user_id),
  ADD CONSTRAINT fk_contract_created_by
    FOREIGN KEY (created_by_user_id) REFERENCES user_accounts (user_id);

CREATE TABLE finance_receipts (
  receipt_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  store_id BIGINT NOT NULL,
  receipt_no VARCHAR(64) NOT NULL,
  customer_id BIGINT NOT NULL,
  contract_id BIGINT DEFAULT NULL,
  receipt_type VARCHAR(32) NOT NULL,
  amount DECIMAL(20,4) NOT NULL,
  payment_method VARCHAR(32) NOT NULL,
  received_at DATETIME NOT NULL,
  receiver_user_id BIGINT NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT '待审核',
  remark VARCHAR(1000) DEFAULT NULL,
  approved_at DATETIME DEFAULT NULL,
  approved_by_user_id BIGINT DEFAULT NULL,
  version BIGINT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (receipt_id),
  UNIQUE KEY uk_finance_receipt_no (tenant_id, receipt_no),
  KEY ix_finance_receipt_customer (tenant_id, customer_id, status),
  KEY ix_finance_receipt_contract (contract_id, status),
  KEY ix_finance_receipt_store (store_id, received_at),
  CONSTRAINT fk_finance_receipt_tenant
    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id),
  CONSTRAINT fk_finance_receipt_store
    FOREIGN KEY (store_id) REFERENCES stores (store_id),
  CONSTRAINT fk_finance_receipt_customer
    FOREIGN KEY (customer_id) REFERENCES customers (customer_id),
  CONSTRAINT fk_finance_receipt_contract
    FOREIGN KEY (contract_id) REFERENCES contracts (contract_id),
  CONSTRAINT fk_finance_receipt_receiver
    FOREIGN KEY (receiver_user_id) REFERENCES user_accounts (user_id),
  CONSTRAINT fk_finance_receipt_approver
    FOREIGN KEY (approved_by_user_id) REFERENCES user_accounts (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

ALTER TABLE room_bookings
  ADD COLUMN contract_id BIGINT DEFAULT NULL AFTER customer_id,
  ADD COLUMN actual_check_in_at DATETIME DEFAULT NULL AFTER check_out,
  ADD COLUMN actual_check_out_at DATETIME DEFAULT NULL AFTER actual_check_in_at,
  ADD COLUMN created_by_user_id BIGINT DEFAULT NULL AFTER source,
  ADD KEY ix_room_booking_contract (contract_id, status),
  ADD KEY ix_room_booking_customer (customer_id, status),
  ADD KEY ix_room_booking_store (store_id, status),
  ADD CONSTRAINT fk_room_booking_store
    FOREIGN KEY (store_id) REFERENCES stores (store_id),
  ADD CONSTRAINT fk_room_booking_room
    FOREIGN KEY (room_id) REFERENCES rooms (room_id),
  ADD CONSTRAINT fk_room_booking_customer
    FOREIGN KEY (customer_id) REFERENCES customers (customer_id),
  ADD CONSTRAINT fk_room_booking_contract
    FOREIGN KEY (contract_id) REFERENCES contracts (contract_id),
  ADD CONSTRAINT fk_room_booking_created_by
    FOREIGN KEY (created_by_user_id) REFERENCES user_accounts (user_id);

CREATE TABLE mvp_audit_events (
  event_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  store_id BIGINT DEFAULT NULL,
  actor_user_id BIGINT NOT NULL,
  aggregate_type VARCHAR(32) NOT NULL,
  aggregate_id BIGINT NOT NULL,
  action_code VARCHAR(32) NOT NULL,
  before_status VARCHAR(32) DEFAULT NULL,
  after_status VARCHAR(32) DEFAULT NULL,
  detail_json TEXT DEFAULT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (event_id),
  KEY ix_mvp_audit_aggregate (aggregate_type, aggregate_id, created_at),
  KEY ix_mvp_audit_actor (actor_user_id, created_at),
  CONSTRAINT fk_mvp_audit_tenant
    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id),
  CONSTRAINT fk_mvp_audit_store
    FOREIGN KEY (store_id) REFERENCES stores (store_id),
  CONSTRAINT fk_mvp_audit_actor
    FOREIGN KEY (actor_user_id) REFERENCES user_accounts (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

