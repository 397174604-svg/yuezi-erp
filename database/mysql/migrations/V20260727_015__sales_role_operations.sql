-- MySQL 5.7
-- Sales-role operations and extension data. Legacy records are not copied.

CREATE TABLE IF NOT EXISTS sales_contract_extensions (
  contract_id BIGINT NOT NULL,
  due_date DATE NULL,
  room_type VARCHAR(128) NULL,
  nursing_type VARCHAR(64) NULL,
  meal_package VARCHAR(64) NULL,
  first_order TINYINT(1) NOT NULL DEFAULT 0,
  remote_sign TINYINT(1) NOT NULL DEFAULT 0,
  discount_audit_status VARCHAR(32) NULL,
  changed TINYINT(1) NOT NULL DEFAULT 0,
  created_by_user_id BIGINT NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (contract_id),
  CONSTRAINT fk_sales_contract_ext_contract
    FOREIGN KEY (contract_id) REFERENCES contracts(contract_id),
  CONSTRAINT fk_sales_contract_ext_creator
    FOREIGN KEY (created_by_user_id) REFERENCES user_accounts(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sales_order_extensions (
  order_no VARCHAR(255) NOT NULL,
  sales_type VARCHAR(64) NOT NULL,
  product_type VARCHAR(128) NULL,
  customer_status VARCHAR(64) NULL,
  sale_date DATE NOT NULL,
  salesperson_user_id BIGINT NULL,
  department_name VARCHAR(128) NULL,
  source VARCHAR(32) NOT NULL DEFAULT 'PC端',
  introducer VARCHAR(128) NULL,
  introducer_mobile VARCHAR(32) NULL,
  remark VARCHAR(1000) NULL,
  payment_remark VARCHAR(1000) NULL,
  finance_audit_status VARCHAR(32) NULL,
  discount_audit_status VARCHAR(32) NULL,
  enabled TINYINT(1) NOT NULL DEFAULT 1,
  attachment VARCHAR(1000) NULL,
  outbound_no VARCHAR(128) NULL,
  returned_at DATETIME NULL,
  created_by_user_id BIGINT NOT NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (order_no),
  KEY ix_sales_order_type (sales_type, sale_date),
  KEY ix_sales_order_salesperson (salesperson_user_id, sale_date),
  CONSTRAINT fk_sales_order_ext_order
    FOREIGN KEY (order_no) REFERENCES orders(order_no),
  CONSTRAINT fk_sales_order_ext_salesperson
    FOREIGN KEY (salesperson_user_id) REFERENCES user_accounts(user_id),
  CONSTRAINT fk_sales_order_ext_creator
    FOREIGN KEY (created_by_user_id) REFERENCES user_accounts(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sales_order_item_extensions (
  order_item_id BIGINT NOT NULL,
  item_code VARCHAR(64) NULL,
  product_type VARCHAR(128) NULL,
  unit VARCHAR(32) NULL,
  discount_price DECIMAL(20,4) NULL,
  valid_days INT NULL,
  warehouse VARCHAR(128) NULL,
  tax_rate DECIMAL(10,4) NOT NULL DEFAULT 0,
  remark VARCHAR(1000) NULL,
  PRIMARY KEY (order_item_id),
  CONSTRAINT fk_sales_order_item_ext_item
    FOREIGN KEY (order_item_id) REFERENCES order_items(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sales_bundle_extensions (
  bundle_id BIGINT NOT NULL,
  store_id BIGINT NOT NULL,
  bundle_no VARCHAR(128) NOT NULL,
  bundle_type VARCHAR(64) NOT NULL,
  days INT NULL,
  reference_price DECIMAL(20,4) NULL,
  room_type VARCHAR(128) NULL,
  audit_status VARCHAR(32) NOT NULL DEFAULT '待提交',
  enabled_at DATETIME NULL,
  recommended TINYINT(1) NOT NULL DEFAULT 0,
  recommended_at DATETIME NULL,
  visible TINYINT(1) NOT NULL DEFAULT 1,
  deadline DATE NULL,
  details TEXT NULL,
  room_info TEXT NULL,
  created_by_user_id BIGINT NOT NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (bundle_id),
  UNIQUE KEY uk_sales_bundle_no (bundle_no),
  KEY ix_sales_bundle_store (store_id, bundle_type, audit_status),
  CONSTRAINT fk_sales_bundle_ext_bundle
    FOREIGN KEY (bundle_id) REFERENCES item_bundles(bundle_id),
  CONSTRAINT fk_sales_bundle_ext_store
    FOREIGN KEY (store_id) REFERENCES stores(store_id),
  CONSTRAINT fk_sales_bundle_ext_creator
    FOREIGN KEY (created_by_user_id) REFERENCES user_accounts(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sales_gift_lists (
  gift_list_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  store_id BIGINT NULL,
  list_no VARCHAR(128) NOT NULL,
  list_name VARCHAR(255) NOT NULL,
  enabled TINYINT(1) NOT NULL DEFAULT 1,
  enabled_at DATETIME NULL,
  created_by_user_id BIGINT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP,
  deleted_at DATETIME NULL,
  PRIMARY KEY (gift_list_id),
  UNIQUE KEY uk_sales_gift_list_no (tenant_id, list_no),
  KEY ix_sales_gift_list_store (tenant_id, store_id, enabled),
  CONSTRAINT fk_sales_gift_list_store
    FOREIGN KEY (store_id) REFERENCES stores(store_id),
  CONSTRAINT fk_sales_gift_list_creator
    FOREIGN KEY (created_by_user_id) REFERENCES user_accounts(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sales_gift_list_lines (
  line_id BIGINT NOT NULL AUTO_INCREMENT,
  gift_list_id BIGINT NOT NULL,
  material_code VARCHAR(64) NULL,
  material_name VARCHAR(255) NOT NULL,
  material_type VARCHAR(128) NULL,
  specification VARCHAR(128) NULL,
  unit VARCHAR(32) NULL,
  price DECIMAL(20,4) NOT NULL DEFAULT 0,
  quantity DECIMAL(20,4) NOT NULL DEFAULT 1,
  remark VARCHAR(1000) NULL,
  PRIMARY KEY (line_id),
  KEY ix_sales_gift_list_line (gift_list_id),
  CONSTRAINT fk_sales_gift_list_line_list
    FOREIGN KEY (gift_list_id) REFERENCES sales_gift_lists(gift_list_id)
      ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sales_coupon_template_extensions (
  tpl_id BIGINT NOT NULL,
  coupon_no VARCHAR(128) NOT NULL,
  starts_at DATETIME NULL,
  ends_at DATETIME NULL,
  limit_per_customer INT NOT NULL DEFAULT 1,
  scope VARCHAR(64) NOT NULL DEFAULT '所有人',
  send_type VARCHAR(64) NOT NULL DEFAULT '店内发放',
  stackable TINYINT(1) NOT NULL DEFAULT 0,
  remark VARCHAR(1000) NULL,
  created_by_user_id BIGINT NOT NULL,
  PRIMARY KEY (tpl_id),
  UNIQUE KEY uk_sales_coupon_template_no (coupon_no),
  CONSTRAINT fk_sales_coupon_tpl_ext_tpl
    FOREIGN KEY (tpl_id) REFERENCES coupon_templates(tpl_id),
  CONSTRAINT fk_sales_coupon_tpl_ext_creator
    FOREIGN KEY (created_by_user_id) REFERENCES user_accounts(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sales_coupon_extensions (
  coupon_id BIGINT NOT NULL,
  audit_status VARCHAR(32) NOT NULL DEFAULT '待审核',
  audit_remark VARCHAR(1000) NULL,
  auditor_user_id BIGINT NULL,
  starts_at DATETIME NULL,
  remaining_amount DECIMAL(20,4) NOT NULL DEFAULT 0,
  valid_days INT NULL,
  remark VARCHAR(1000) NULL,
  disable_reason VARCHAR(1000) NULL,
  created_by_user_id BIGINT NOT NULL,
  PRIMARY KEY (coupon_id),
  CONSTRAINT fk_sales_coupon_ext_coupon
    FOREIGN KEY (coupon_id) REFERENCES coupons(coupon_id),
  CONSTRAINT fk_sales_coupon_ext_auditor
    FOREIGN KEY (auditor_user_id) REFERENCES user_accounts(user_id),
  CONSTRAINT fk_sales_coupon_ext_creator
    FOREIGN KEY (created_by_user_id) REFERENCES user_accounts(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sales_gift_applications (
  application_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  store_id BIGINT NOT NULL,
  application_no VARCHAR(128) NOT NULL,
  customer_id BIGINT NOT NULL,
  gift_type VARCHAR(64) NOT NULL,
  gift_reason VARCHAR(1000) NOT NULL,
  consume_amount DECIMAL(20,4) NOT NULL DEFAULT 0,
  audit_status VARCHAR(32) NOT NULL DEFAULT '待提交',
  outbound_status VARCHAR(32) NOT NULL DEFAULT '未出库',
  attachment VARCHAR(1000) NULL,
  created_by_user_id BIGINT NOT NULL,
  approved_by_user_id BIGINT NULL,
  approved_at DATETIME NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP,
  deleted_at DATETIME NULL,
  PRIMARY KEY (application_id),
  UNIQUE KEY uk_sales_gift_application_no (tenant_id, application_no),
  KEY ix_sales_gift_application_store
    (tenant_id, store_id, audit_status),
  CONSTRAINT fk_sales_gift_application_store
    FOREIGN KEY (store_id) REFERENCES stores(store_id),
  CONSTRAINT fk_sales_gift_application_customer
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
  CONSTRAINT fk_sales_gift_application_creator
    FOREIGN KEY (created_by_user_id) REFERENCES user_accounts(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sales_gift_application_lines (
  line_id BIGINT NOT NULL AUTO_INCREMENT,
  application_id BIGINT NOT NULL,
  item_code VARCHAR(64) NULL,
  item_name VARCHAR(255) NOT NULL,
  unit VARCHAR(32) NULL,
  price DECIMAL(20,4) NOT NULL DEFAULT 0,
  discount_price DECIMAL(20,4) NOT NULL DEFAULT 0,
  quantity DECIMAL(20,4) NOT NULL DEFAULT 1,
  valid_days INT NULL,
  warehouse VARCHAR(128) NULL,
  PRIMARY KEY (line_id),
  KEY ix_sales_gift_application_line (application_id),
  CONSTRAINT fk_sales_gift_application_line_application
    FOREIGN KEY (application_id)
    REFERENCES sales_gift_applications(application_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sales_operation_records (
  operation_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  store_id BIGINT NULL,
  resource_key VARCHAR(64) NOT NULL,
  record_key VARCHAR(255) NOT NULL,
  action_name VARCHAR(64) NOT NULL,
  before_status VARCHAR(64) NULL,
  after_status VARCHAR(64) NULL,
  detail_json TEXT NULL,
  actor_user_id BIGINT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (operation_id),
  KEY ix_sales_operation_record
    (tenant_id, resource_key, record_key, created_at),
  CONSTRAINT fk_sales_operation_actor
    FOREIGN KEY (actor_user_id) REFERENCES user_accounts(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
