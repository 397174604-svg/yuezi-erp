-- MySQL 5.7
-- Yellow River store room-type catalog and initial verified room inventory.
-- Room numbers follow the agreed floor-number convention:
-- 301-308, 401-408, 501-507 and 601.

CREATE TABLE room_types (
  room_type_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  type_code VARCHAR(64) NOT NULL,
  name VARCHAR(100) NOT NULL,
  layout_name VARCHAR(100) NOT NULL,
  bedrooms TINYINT UNSIGNED NOT NULL DEFAULT 0,
  living_rooms TINYINT UNSIGNED NOT NULL DEFAULT 0,
  bed_type VARCHAR(64) DEFAULT NULL,
  package_name VARCHAR(100) NOT NULL,
  status VARCHAR(16) NOT NULL DEFAULT '启用',
  sort_order INT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (room_type_id),
  UNIQUE KEY uk_room_type_tenant_code (tenant_id, type_code),
  KEY ix_room_type_tenant_status (tenant_id, status, sort_order),
  CONSTRAINT fk_room_type_tenant
    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

ALTER TABLE rooms
  ADD COLUMN room_type_id BIGINT DEFAULT NULL AFTER room_type,
  ADD KEY ix_rooms_room_type (room_type_id),
  ADD CONSTRAINT fk_rooms_room_type
    FOREIGN KEY (room_type_id) REFERENCES room_types (room_type_id);

INSERT INTO room_types(
  tenant_id, type_code, name, layout_name, bedrooms, living_rooms,
  bed_type, package_name, status, sort_order
) VALUES
  (1, 'YH_REPAIR_1B1L', '一房一厅（修复套餐）', '一房一厅', 1, 1, NULL, '修复套餐', '启用', 10),
  (1, 'YH_BASIC_KING', '大床（基础大床）', '大床房', 1, 0, '大床', '基础大床', '启用', 20),
  (1, 'YH_BASIC_PACKAGE_KING', '大床（基础套餐）', '大床房', 1, 0, '大床', '基础套餐', '启用', 30),
  (1, 'YH_PRESIDENT_3B3L', '三室三厅（总统套）', '三室三厅', 3, 3, NULL, '总统套', '启用', 40),
  (1, 'YH_QUEEN_2B2L', '两室两厅（女王套）', '两室两厅', 2, 2, NULL, '女王套', '启用', 50);

DELETE r
FROM rooms r
JOIN stores s ON s.store_id = r.store_id
WHERE r.tenant_id = 1
  AND s.name = '奇德芬芳·黄河路店'
  AND r.room_no IN ('201', '202')
  AND r.status = '空闲'
  AND NOT EXISTS (
    SELECT 1
    FROM room_bookings rb
    WHERE rb.room_id = r.room_id
  );

INSERT INTO rooms(
  tenant_id, store_id, room_no, room_type, room_type_id, floor,
  direction, layout_order, price, status, note, created_at
)
SELECT
  1,
  s.store_id,
  inventory.room_no,
  rt.name,
  rt.room_type_id,
  inventory.floor,
  inventory.direction,
  inventory.layout_order,
  0,
  '空闲',
  inventory.note,
  NOW()
FROM stores s
JOIN (
  SELECT '301' AS room_no, 3 AS floor, '待核实' AS direction, 1 AS layout_order, 'YH_REPAIR_1B1L' AS type_code, NULL AS note
  UNION ALL SELECT '302', 3, '待核实', 2, 'YH_REPAIR_1B1L', NULL
  UNION ALL SELECT '303', 3, '待核实', 3, 'YH_REPAIR_1B1L', NULL
  UNION ALL SELECT '304', 3, '待核实', 4, 'YH_REPAIR_1B1L', NULL
  UNION ALL SELECT '305', 3, '待核实', 5, 'YH_REPAIR_1B1L', NULL
  UNION ALL SELECT '306', 3, '待核实', 6, 'YH_REPAIR_1B1L', NULL
  UNION ALL SELECT '307', 3, '待核实', 7, 'YH_REPAIR_1B1L', NULL
  UNION ALL SELECT '308', 3, '待核实', 8, 'YH_REPAIR_1B1L', NULL
  UNION ALL SELECT '401', 4, '北', 1, 'YH_BASIC_KING', '北侧从东向西第1间'
  UNION ALL SELECT '402', 4, '北', 2, 'YH_BASIC_KING', '北侧从东向西第2间'
  UNION ALL SELECT '403', 4, '北', 3, 'YH_BASIC_KING', '北侧从东向西第3间'
  UNION ALL SELECT '404', 4, '待核实', 4, 'YH_REPAIR_1B1L', NULL
  UNION ALL SELECT '405', 4, '待核实', 5, 'YH_REPAIR_1B1L', NULL
  UNION ALL SELECT '406', 4, '待核实', 6, 'YH_REPAIR_1B1L', NULL
  UNION ALL SELECT '407', 4, '待核实', 7, 'YH_REPAIR_1B1L', NULL
  UNION ALL SELECT '408', 4, '待核实', 8, 'YH_REPAIR_1B1L', NULL
  UNION ALL SELECT '501', 5, '北', 1, 'YH_BASIC_PACKAGE_KING', '北侧从东向西第1间'
  UNION ALL SELECT '502', 5, '北', 2, 'YH_BASIC_PACKAGE_KING', '北侧从东向西第2间'
  UNION ALL SELECT '503', 5, '北', 3, 'YH_BASIC_PACKAGE_KING', '北侧从东向西第3间'
  UNION ALL SELECT '504', 5, '待核实', 4, 'YH_REPAIR_1B1L', NULL
  UNION ALL SELECT '505', 5, '待核实', 5, 'YH_REPAIR_1B1L', NULL
  UNION ALL SELECT '506', 5, '待核实', 6, 'YH_REPAIR_1B1L', NULL
  UNION ALL SELECT '507', 5, '北', 7, 'YH_PRESIDENT_3B3L', '五楼最北侧'
  UNION ALL SELECT '601', 6, '待核实', 1, 'YH_QUEEN_2B2L', '六楼单独一间'
) inventory
JOIN room_types rt
  ON rt.tenant_id = 1
 AND rt.type_code = inventory.type_code
WHERE s.tenant_id = 1
  AND s.name = '奇德芬芳·黄河路店'
  AND NOT EXISTS (
    SELECT 1
    FROM rooms existing_room
    WHERE existing_room.tenant_id = 1
      AND existing_room.store_id = s.store_id
      AND existing_room.room_no = inventory.room_no
      AND existing_room.deleted_at IS NULL
  );

INSERT INTO user_stores(user_id, store_id, access_level)
SELECT u.user_id, s.store_id, 'READ'
FROM user_accounts u
JOIN stores s
  ON s.tenant_id = u.tenant_id
 AND s.name = '奇德芬芳·黄河路店'
WHERE u.username = 'test_sales_manager'
ON DUPLICATE KEY UPDATE access_level = VALUES(access_level);
