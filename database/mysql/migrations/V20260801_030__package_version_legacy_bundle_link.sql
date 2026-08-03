-- MySQL 5.7
-- One package family can contain multiple stay-length versions.  The legacy
-- sales bundle is therefore linked to the version, not only to the family.
ALTER TABLE package_versions
  ADD COLUMN legacy_bundle_id BIGINT DEFAULT NULL AFTER package_id,
  ADD KEY ix_package_version_legacy_bundle (legacy_bundle_id);
