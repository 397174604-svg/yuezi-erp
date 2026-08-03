-- MySQL 5.7
-- A catalogue price rule previously held only the reference/original amount.
-- Keep the three confirmed commercial price points separate so a contract can
-- show original, campaign and actual deal prices without overwriting one with
-- another.  Existing rules remain valid; only rules with a profile row expose
-- all three values.

CREATE TABLE IF NOT EXISTS package_price_profiles (
  package_price_profile_id BIGINT NOT NULL AUTO_INCREMENT,
  tenant_id BIGINT NOT NULL,
  price_rule_id BIGINT NOT NULL,
  original_amount DECIMAL(20,4) NOT NULL,
  activity_amount DECIMAL(20,4) NOT NULL,
  deal_amount DECIMAL(20,4) NOT NULL,
  source_type VARCHAR(32) NOT NULL DEFAULT 'CLIENT_CONFIRMED',
  evidence_note VARCHAR(1000) DEFAULT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (package_price_profile_id),
  UNIQUE KEY uk_package_price_profile_rule (price_rule_id),
  KEY ix_package_price_profile_tenant (tenant_id, price_rule_id),
  CONSTRAINT fk_package_price_profile_tenant
    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id),
  CONSTRAINT fk_package_price_profile_rule
    FOREIGN KEY (price_rule_id) REFERENCES package_price_rules (price_rule_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
