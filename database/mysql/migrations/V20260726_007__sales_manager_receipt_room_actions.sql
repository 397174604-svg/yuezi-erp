-- MySQL 5.7
-- The observed legacy 销售经理 role can audit receipts and perform room
-- check-in actions from 房态管理/房态图.

INSERT IGNORE INTO role_permissions(role_id, permission_id, effect)
SELECT r.role_id, p.permission_id, 'ALLOW'
FROM roles r
JOIN permissions p
  ON p.code IN ('FINANCE.APPROVE', 'ROOM.EXECUTE')
WHERE r.tenant_id=1 AND r.code='SALES_MANAGER';

