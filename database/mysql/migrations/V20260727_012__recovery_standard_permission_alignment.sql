-- Restore normalized MVP permissions only when the same recovery role owns
-- the corresponding observed legacy page button permission.

INSERT IGNORE INTO role_permissions(role_id, permission_id, effect)
SELECT r.role_id, normalized.permission_id, 'ALLOW'
FROM roles r
JOIN role_permissions observed_rp
  ON observed_rp.role_id=r.role_id AND observed_rp.effect='ALLOW'
JOIN permissions observed
  ON observed.permission_id=observed_rp.permission_id
JOIN permissions normalized
  ON normalized.code=CASE observed.code
    WHEN 'LEGACY.WEB.N85.B1' THEN 'SALES.CREATE'
    WHEN 'LEGACY.WEB.N85.B10' THEN 'SALES.UPDATE'
    WHEN 'LEGACY.WEB.N90.B1' THEN 'FINANCE.CREATE'
    WHEN 'LEGACY.WEB.N90.B10' THEN 'FINANCE.UPDATE'
  END
WHERE r.code='RECOVERY_THERAPIST'
  AND observed.code IN (
    'LEGACY.WEB.N85.B1',
    'LEGACY.WEB.N85.B10',
    'LEGACY.WEB.N90.B1',
    'LEGACY.WEB.N90.B10'
  );
