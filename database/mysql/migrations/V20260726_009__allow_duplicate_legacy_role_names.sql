-- The legacy ERP has distinct role ids with the same display name (for
-- example role 8 and role 89 are both named 护士). Identity is carried by
-- code/legacy_role_id, so the role display name must not be unique.

ALTER TABLE roles
  DROP INDEX ix_roles_tenant,
  ADD KEY ix_roles_tenant_name (tenant_id, name);
