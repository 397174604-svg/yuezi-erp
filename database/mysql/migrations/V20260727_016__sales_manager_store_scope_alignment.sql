-- MySQL 5.7
-- The authenticated 韩新 legacy page exposes both store selectors and defaults
-- to the centre/建设路 store. Align the local role account with that evidence.

INSERT IGNORE INTO user_stores(user_id, store_id, access_level)
SELECT ua.user_id, s.store_id, 'WRITE'
FROM user_accounts ua
JOIN stores s
  ON s.tenant_id=ua.tenant_id
 AND (
   s.name LIKE '%中心广场%'
   OR s.name LIKE '%建设路%'
   OR s.name LIKE '%黄河路%'
 )
WHERE ua.username='韩新';

UPDATE user_accounts ua
JOIN stores s
  ON s.tenant_id=ua.tenant_id
 AND (s.name LIKE '%中心广场%' OR s.name LIKE '%建设路%')
SET ua.default_store_id=s.store_id
WHERE ua.username='韩新';
