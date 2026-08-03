-- MySQL 5.7
-- Preserve the three price points and the stated effective date used by the
-- ERP package-management screen.  No package price is seeded by this change.

ALTER TABLE sales_bundle_extensions
  ADD COLUMN activity_price DECIMAL(20,4) DEFAULT NULL AFTER reference_price,
  ADD COLUMN effective_date DATE DEFAULT NULL AFTER activity_price;
