ALTER TABLE wallet_ledger
  ADD COLUMN store_id BIGINT NULL AFTER tenant_id,
  ADD COLUMN payment_method VARCHAR(64) NULL AFTER reason,
  ADD COLUMN operator_user_id BIGINT NULL AFTER ref_order,
  ADD KEY ix_wallet_ledger_store (tenant_id, store_id, id),
  ADD KEY ix_wallet_ledger_operator (operator_user_id),
  ADD CONSTRAINT fk_wallet_ledger_store
    FOREIGN KEY (store_id) REFERENCES stores(store_id),
  ADD CONSTRAINT fk_wallet_ledger_operator
    FOREIGN KEY (operator_user_id) REFERENCES user_accounts(user_id);

UPDATE wallet_ledger ledger
JOIN customers customer ON customer.customer_id=ledger.customer_id
SET ledger.store_id=customer.store_id
WHERE ledger.store_id IS NULL;
