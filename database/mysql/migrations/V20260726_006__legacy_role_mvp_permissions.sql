-- MySQL 5.7
-- Align the normalized MVP permissions with the observed legacy roles:
-- role 5 销售经理, role 74 产后修复师, role 21 客房管家.

-- 产后修复师：旧系统可查看/维护客户，可新增合同和收款，但没有
-- 合同审核、收款审核和客房办理按钮。
INSERT IGNORE INTO role_permissions(role_id, permission_id, effect)
SELECT r.role_id, p.permission_id, 'ALLOW'
FROM roles r
JOIN permissions p
  ON p.code IN (
    'CUSTOMER.CREATE', 'CUSTOMER.UPDATE',
    'SALES.VIEW', 'SALES.QUERY', 'SALES.CREATE', 'SALES.UPDATE',
    'SALES.EXPORT', 'SALES.PRINT',
    'FINANCE.VIEW', 'FINANCE.QUERY', 'FINANCE.CREATE',
    'FINANCE.UPDATE', 'FINANCE.PRINT'
  )
WHERE r.tenant_id=1 AND r.code='RECOVERY_THERAPIST';

INSERT INTO role_data_scopes(
  role_id, module_code, scope_type, allow_cross_store,
  allow_cross_department, condition_json
)
SELECT r.role_id, modules.module_code, 'SELF', 0, 0, NULL
FROM roles r
JOIN (
  SELECT 'SALES' AS module_code
  UNION ALL SELECT 'FINANCE'
) modules
WHERE r.tenant_id=1 AND r.code='RECOVERY_THERAPIST'
ON DUPLICATE KEY UPDATE
  scope_type=VALUES(scope_type),
  allow_cross_store=VALUES(allow_cross_store),
  allow_cross_department=VALUES(allow_cross_department);

-- 客房管家：旧系统可维护客户、办理订房/入住，并在“收款审核”
-- 页面拥有审核按钮；没有合同管理菜单。
INSERT IGNORE INTO role_permissions(role_id, permission_id, effect)
SELECT r.role_id, p.permission_id, 'ALLOW'
FROM roles r
JOIN permissions p
  ON p.code IN (
    'CUSTOMER.CREATE', 'CUSTOMER.UPDATE',
    'FINANCE.VIEW', 'FINANCE.QUERY', 'FINANCE.APPROVE'
  )
WHERE r.tenant_id=1 AND r.code='HOUSEKEEPER';

INSERT INTO role_data_scopes(
  role_id, module_code, scope_type, allow_cross_store,
  allow_cross_department, condition_json
)
SELECT r.role_id, 'FINANCE', 'DEPARTMENT', 0, 0, NULL
FROM roles r
WHERE r.tenant_id=1 AND r.code='HOUSEKEEPER'
ON DUPLICATE KEY UPDATE
  scope_type=VALUES(scope_type),
  allow_cross_store=VALUES(allow_cross_store),
  allow_cross_department=VALUES(allow_cross_department);

