-- MySQL 5.7
-- Complete the customer coupon closed loop in the real database runtime.

ALTER TABLE sales_coupon_extensions
  ADD COLUMN coupon_name VARCHAR(100) NULL AFTER coupon_id;

INSERT IGNORE INTO permissions(
  code, module_code, resource_type, action_code, name, sort_order, status
)
VALUES(
  'SALES.DISCOUNT.CONSUME',
  'SALES',
  'DISCOUNT',
  'CONSUME',
  '客户优惠券核销',
  118,
  'ACTIVE'
);

INSERT IGNORE INTO role_permissions(
  role_id, permission_id, effect
)
SELECT r.role_id, p.permission_id, 'ALLOW'
FROM roles r
JOIN permissions p
  ON p.code='SALES.DISCOUNT.CONSUME'
WHERE r.code IN ('SALES_MANAGER', 'SYS_ADMIN');
