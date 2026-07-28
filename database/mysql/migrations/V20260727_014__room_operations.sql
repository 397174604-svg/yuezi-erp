-- MySQL 5.7
-- Real room-department operations used by the legacy HOUSEKEEPER role.

CREATE TABLE IF NOT EXISTS room_stay_extensions (
  extension_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  store_id BIGINT NOT NULL,
  booking_id BIGINT NOT NULL,
  customer_id BIGINT NOT NULL,
  room_id BIGINT NOT NULL,
  extension_type VARCHAR(32) NOT NULL,
  start_at DATE NOT NULL,
  end_at DATE NOT NULL,
  extension_days INT NOT NULL,
  extension_amount DECIMAL(20,4) NOT NULL DEFAULT 0,
  received_amount DECIMAL(20,4) NOT NULL DEFAULT 0,
  status VARCHAR(32) NOT NULL DEFAULT '待续住',
  audit_status VARCHAR(32) NOT NULL DEFAULT '待审核',
  remark VARCHAR(1000) NULL,
  extension_salesperson VARCHAR(128) NULL,
  created_by_user_id BIGINT NOT NULL,
  approved_by_user_id BIGINT NULL,
  approved_at DATETIME NULL,
  cancelled_at DATETIME NULL,
  version BIGINT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP,
  deleted_at DATETIME NULL,
  PRIMARY KEY (extension_id),
  KEY ix_room_extension_store (tenant_id, store_id, audit_status),
  KEY ix_room_extension_booking (booking_id, status),
  CONSTRAINT fk_room_extension_store
    FOREIGN KEY (store_id) REFERENCES stores(store_id),
  CONSTRAINT fk_room_extension_booking
    FOREIGN KEY (booking_id) REFERENCES room_bookings(booking_id),
  CONSTRAINT fk_room_extension_customer
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
  CONSTRAINT fk_room_extension_room
    FOREIGN KEY (room_id) REFERENCES rooms(room_id),
  CONSTRAINT fk_room_extension_creator
    FOREIGN KEY (created_by_user_id) REFERENCES user_accounts(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS room_change_applications (
  change_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  store_id BIGINT NOT NULL,
  booking_id BIGINT NOT NULL,
  customer_id BIGINT NOT NULL,
  source_room_id BIGINT NOT NULL,
  target_store_id BIGINT NOT NULL,
  target_room_id BIGINT NOT NULL,
  changed_at DATETIME NOT NULL,
  reason VARCHAR(1000) NOT NULL,
  audit_status VARCHAR(32) NOT NULL DEFAULT '待审核',
  audit_opinion VARCHAR(1000) NULL,
  applicant_user_id BIGINT NOT NULL,
  approved_by_user_id BIGINT NULL,
  approved_at DATETIME NULL,
  version BIGINT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP,
  deleted_at DATETIME NULL,
  PRIMARY KEY (change_id),
  KEY ix_room_change_store (tenant_id, store_id, audit_status),
  KEY ix_room_change_booking (booking_id, audit_status),
  CONSTRAINT fk_room_change_store
    FOREIGN KEY (store_id) REFERENCES stores(store_id),
  CONSTRAINT fk_room_change_target_store
    FOREIGN KEY (target_store_id) REFERENCES stores(store_id),
  CONSTRAINT fk_room_change_booking
    FOREIGN KEY (booking_id) REFERENCES room_bookings(booking_id),
  CONSTRAINT fk_room_change_customer
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
  CONSTRAINT fk_room_change_source_room
    FOREIGN KEY (source_room_id) REFERENCES rooms(room_id),
  CONSTRAINT fk_room_change_target_room
    FOREIGN KEY (target_room_id) REFERENCES rooms(room_id),
  CONSTRAINT fk_room_change_applicant
    FOREIGN KEY (applicant_user_id) REFERENCES user_accounts(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS room_service_requests (
  service_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  store_id BIGINT NOT NULL,
  booking_id BIGINT NULL,
  customer_id BIGINT NULL,
  room_id BIGINT NOT NULL,
  service_type VARCHAR(128) NOT NULL,
  applied_at DATETIME NOT NULL,
  scheduled_at DATETIME NULL,
  service_status VARCHAR(32) NOT NULL DEFAULT '未完成服务',
  remark VARCHAR(1000) NULL,
  service_staff_id BIGINT NULL,
  created_by_user_id BIGINT NOT NULL,
  confirmed_by_user_id BIGINT NULL,
  completed_by_user_id BIGINT NULL,
  completed_at DATETIME NULL,
  cancelled_at DATETIME NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP,
  deleted_at DATETIME NULL,
  PRIMARY KEY (service_id),
  KEY ix_room_service_store (tenant_id, store_id, service_status),
  KEY ix_room_service_room (room_id, applied_at),
  CONSTRAINT fk_room_service_store
    FOREIGN KEY (store_id) REFERENCES stores(store_id),
  CONSTRAINT fk_room_service_booking
    FOREIGN KEY (booking_id) REFERENCES room_bookings(booking_id),
  CONSTRAINT fk_room_service_customer
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
  CONSTRAINT fk_room_service_room
    FOREIGN KEY (room_id) REFERENCES rooms(room_id),
  CONSTRAINT fk_room_service_creator
    FOREIGN KEY (created_by_user_id) REFERENCES user_accounts(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS room_outing_applications (
  outing_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  store_id BIGINT NOT NULL,
  booking_id BIGINT NULL,
  customer_id BIGINT NOT NULL,
  person_type VARCHAR(32) NOT NULL,
  start_at DATETIME NOT NULL,
  expected_return_at DATETIME NOT NULL,
  outing_days INT NOT NULL DEFAULT 0,
  escort VARCHAR(128) NULL,
  reason VARCHAR(1000) NOT NULL,
  outing_status VARCHAR(32) NOT NULL DEFAULT '从未被审核',
  returned_at DATETIME NULL,
  created_by_user_id BIGINT NOT NULL,
  approved_by_user_id BIGINT NULL,
  approved_at DATETIME NULL,
  version BIGINT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP,
  deleted_at DATETIME NULL,
  PRIMARY KEY (outing_id),
  KEY ix_room_outing_store (tenant_id, store_id, outing_status),
  KEY ix_room_outing_customer (customer_id, start_at),
  CONSTRAINT fk_room_outing_store
    FOREIGN KEY (store_id) REFERENCES stores(store_id),
  CONSTRAINT fk_room_outing_booking
    FOREIGN KEY (booking_id) REFERENCES room_bookings(booking_id),
  CONSTRAINT fk_room_outing_customer
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
  CONSTRAINT fk_room_outing_creator
    FOREIGN KEY (created_by_user_id) REFERENCES user_accounts(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS room_borrowed_items (
  borrow_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  store_id BIGINT NOT NULL,
  booking_id BIGINT NULL,
  customer_id BIGINT NOT NULL,
  room_id BIGINT NOT NULL,
  item_name VARCHAR(255) NOT NULL,
  borrowed_at DATETIME NOT NULL,
  expected_return_at DATETIME NULL,
  deposit DECIMAL(20,4) NOT NULL DEFAULT 0,
  deposit_paid VARCHAR(32) NOT NULL DEFAULT '未收款',
  rent DECIMAL(20,4) NOT NULL DEFAULT 0,
  rent_paid VARCHAR(32) NOT NULL DEFAULT '未收款',
  return_status VARCHAR(32) NOT NULL DEFAULT '未还',
  signed_at DATETIME NULL,
  signer VARCHAR(128) NULL,
  remark VARCHAR(1000) NULL,
  created_by_user_id BIGINT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP,
  deleted_at DATETIME NULL,
  PRIMARY KEY (borrow_id),
  KEY ix_room_borrow_store (tenant_id, store_id, return_status),
  KEY ix_room_borrow_room (room_id, borrowed_at),
  CONSTRAINT fk_room_borrow_store
    FOREIGN KEY (store_id) REFERENCES stores(store_id),
  CONSTRAINT fk_room_borrow_booking
    FOREIGN KEY (booking_id) REFERENCES room_bookings(booking_id),
  CONSTRAINT fk_room_borrow_customer
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
  CONSTRAINT fk_room_borrow_room
    FOREIGN KEY (room_id) REFERENCES rooms(room_id),
  CONSTRAINT fk_room_borrow_creator
    FOREIGN KEY (created_by_user_id) REFERENCES user_accounts(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS room_laundry_records (
  laundry_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  store_id BIGINT NOT NULL,
  booking_id BIGINT NULL,
  customer_id BIGINT NOT NULL,
  room_id BIGINT NOT NULL,
  department VARCHAR(128) NOT NULL,
  sent_at DATETIME NOT NULL,
  special_requirement VARCHAR(1000) NULL,
  sign_status VARCHAR(32) NOT NULL DEFAULT '未签收',
  signed_at DATETIME NULL,
  signer VARCHAR(128) NULL,
  remark VARCHAR(1000) NULL,
  created_by_user_id BIGINT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP,
  deleted_at DATETIME NULL,
  PRIMARY KEY (laundry_id),
  KEY ix_room_laundry_store (tenant_id, store_id, sign_status),
  KEY ix_room_laundry_room (room_id, sent_at),
  CONSTRAINT fk_room_laundry_store
    FOREIGN KEY (store_id) REFERENCES stores(store_id),
  CONSTRAINT fk_room_laundry_booking
    FOREIGN KEY (booking_id) REFERENCES room_bookings(booking_id),
  CONSTRAINT fk_room_laundry_customer
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
  CONSTRAINT fk_room_laundry_room
    FOREIGN KEY (room_id) REFERENCES rooms(room_id),
  CONSTRAINT fk_room_laundry_creator
    FOREIGN KEY (created_by_user_id) REFERENCES user_accounts(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS room_gift_distributions (
  distribution_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  store_id BIGINT NOT NULL,
  booking_id BIGINT NULL,
  customer_id BIGINT NOT NULL,
  contract_id BIGINT NULL,
  room_id BIGINT NULL,
  gift_items TEXT NOT NULL,
  gift_status VARCHAR(32) NOT NULL DEFAULT '未赠送',
  issued_at DATETIME NULL,
  issued_by_user_id BIGINT NULL,
  remark VARCHAR(1000) NULL,
  created_by_user_id BIGINT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP,
  deleted_at DATETIME NULL,
  PRIMARY KEY (distribution_id),
  KEY ix_room_gift_store (tenant_id, store_id, gift_status),
  KEY ix_room_gift_customer (customer_id, contract_id),
  CONSTRAINT fk_room_gift_store
    FOREIGN KEY (store_id) REFERENCES stores(store_id),
  CONSTRAINT fk_room_gift_booking
    FOREIGN KEY (booking_id) REFERENCES room_bookings(booking_id),
  CONSTRAINT fk_room_gift_customer
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
  CONSTRAINT fk_room_gift_contract
    FOREIGN KEY (contract_id) REFERENCES contracts(contract_id),
  CONSTRAINT fk_room_gift_room
    FOREIGN KEY (room_id) REFERENCES rooms(room_id),
  CONSTRAINT fk_room_gift_creator
    FOREIGN KEY (created_by_user_id) REFERENCES user_accounts(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS room_operation_records (
  operation_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  store_id BIGINT NOT NULL,
  booking_id BIGINT NULL,
  customer_id BIGINT NULL,
  room_id BIGINT NULL,
  operation_type VARCHAR(64) NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT '已记录',
  payload_json TEXT NULL,
  created_by_user_id BIGINT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (operation_id),
  KEY ix_room_operation_store (tenant_id, store_id, operation_type, created_at),
  KEY ix_room_operation_booking (booking_id, created_at),
  CONSTRAINT fk_room_operation_store
    FOREIGN KEY (store_id) REFERENCES stores(store_id),
  CONSTRAINT fk_room_operation_booking
    FOREIGN KEY (booking_id) REFERENCES room_bookings(booking_id),
  CONSTRAINT fk_room_operation_customer
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
  CONSTRAINT fk_room_operation_room
    FOREIGN KEY (room_id) REFERENCES rooms(room_id),
  CONSTRAINT fk_room_operation_creator
    FOREIGN KEY (created_by_user_id) REFERENCES user_accounts(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
