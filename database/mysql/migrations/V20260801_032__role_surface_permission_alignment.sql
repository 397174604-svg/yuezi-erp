-- MySQL 5.7
-- Keep role landing pages, notification reads and F017 appointment operations
-- usable after the legacy permission-resource tables were retired.
-- Passwords are intentionally not stored in migrations.

-- NotificationCenter reads customer, contract, receipt, booking and appointment
-- summaries in one request group.  Each operational role therefore needs the
-- standard read permissions for those five resources; store scope still limits
-- every query to the user's granted stores.
INSERT IGNORE INTO role_permissions(role_id, permission_id, effect)
SELECT r.role_id, p.permission_id, 'ALLOW'
FROM roles r
JOIN permissions p
  ON p.code IN (
    'CUSTOMER.VIEW', 'CUSTOMER.QUERY',
    'SALES.VIEW', 'SALES.QUERY',
    'FINANCE.VIEW', 'FINANCE.QUERY',
    'ROOM.VIEW', 'ROOM.QUERY',
    'RECOVERY.VIEW', 'RECOVERY.QUERY'
  )
WHERE r.tenant_id=1
  AND r.code IN ('SALES_MANAGER', 'RECOVERY_THERAPIST', 'HOUSEKEEPER');

-- F017 is a sales/appointment entry point.  Sales can create appointments and
-- progress/cancel them, but cannot edit recovery assessments or service records.
INSERT IGNORE INTO role_permissions(role_id, permission_id, effect)
SELECT r.role_id, p.permission_id, 'ALLOW'
FROM roles r
JOIN permissions p
  ON p.code IN ('RECOVERY.CREATE', 'RECOVERY.EXECUTE')
WHERE r.tenant_id=1 AND r.code='SALES_MANAGER';

INSERT INTO role_data_scopes(
  role_id, module_code, scope_type, allow_cross_store,
  allow_cross_department, condition_json
)
SELECT r.role_id, modules.module_code,
       CASE WHEN r.code='SALES_MANAGER' THEN 'STORE' ELSE 'DEPARTMENT' END,
       0, 0, NULL
FROM roles r
JOIN (
  SELECT 'CUSTOMER' AS module_code
  UNION ALL SELECT 'SALES'
  UNION ALL SELECT 'FINANCE'
  UNION ALL SELECT 'ROOM'
  UNION ALL SELECT 'RECOVERY'
) modules
WHERE r.tenant_id=1
  AND r.code IN ('SALES_MANAGER', 'RECOVERY_THERAPIST', 'HOUSEKEEPER')
ON DUPLICATE KEY UPDATE
  allow_cross_store=0;
