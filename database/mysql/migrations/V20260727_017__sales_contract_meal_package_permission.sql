-- MySQL 5.7
-- The live Han Xin sales page exposes “膳食套餐”, but the imported legacy
-- button dictionary has no standalone id for it. Model the observed
-- write-capability explicitly instead of reusing the contract browse grant.

INSERT IGNORE INTO permissions(
  code, module_code, resource_type, action_code, name, sort_order, status
)
VALUES(
  'SALES.CONTRACT.MEAL_PACKAGE.UPDATE',
  'SALES',
  'CONTRACT',
  'UPDATE',
  '合同膳食套餐维护',
  117,
  'ACTIVE'
);

INSERT IGNORE INTO role_permissions(
  role_id, permission_id, effect
)
SELECT r.role_id, p.permission_id, 'ALLOW'
FROM roles r
JOIN permissions p
  ON p.code='SALES.CONTRACT.MEAL_PACKAGE.UPDATE'
WHERE r.code IN ('SALES_MANAGER', 'SYS_ADMIN');
