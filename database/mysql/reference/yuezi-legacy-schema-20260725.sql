-- Schema-only backup generated before replacing disposable yuezi data.
-- Generated at 2026-07-25T14:46:51
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS=0;
CREATE DATABASE IF NOT EXISTS `yuezi` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `yuezi`;

CREATE TABLE `appointments` (
  `appt_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `store_id` bigint(20) DEFAULT NULL,
  `customer_id` bigint(20) DEFAULT NULL,
  `project` text COLLATE utf8mb4_unicode_ci,
  `tech` text COLLATE utf8mb4_unicode_ci,
  `time` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `status` text COLLATE utf8mb4_unicode_ci,
  `created_at` text COLLATE utf8mb4_unicode_ci,
  `deleted_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`appt_id`),
  KEY `ix_appt` (`tenant_id`,`store_id`,`time`),
  KEY `fk_appointments_1` (`store_id`),
  KEY `fk_appointments_0` (`customer_id`),
  CONSTRAINT `fk_appointments_0` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_appointments_1` FOREIGN KEY (`store_id`) REFERENCES `stores` (`store_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_appointments_2` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `approval_instances` (
  `instance_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `store_id` bigint(20) DEFAULT NULL,
  `biz_type` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `biz_id` bigint(20) DEFAULT NULL,
  `title` text COLLATE utf8mb4_unicode_ci,
  `amount` decimal(20,4) DEFAULT NULL,
  `submitter_id` bigint(20) DEFAULT NULL,
  `total_steps` bigint(20) NOT NULL DEFAULT '1',
  `current_step` bigint(20) NOT NULL DEFAULT '1',
  `status` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '待审核',
  `version` bigint(20) NOT NULL DEFAULT '0',
  `created_at` text COLLATE utf8mb4_unicode_ci,
  `deleted_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`instance_id`),
  KEY `ix_approval_inst` (`tenant_id`,`status`,`biz_type`),
  CONSTRAINT `fk_approval_instances_0` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `approval_records` (
  `record_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `instance_id` bigint(20) NOT NULL,
  `step` bigint(20) DEFAULT NULL,
  `approver_id` bigint(20) DEFAULT NULL,
  `action` text COLLATE utf8mb4_unicode_ci,
  `opinion` text COLLATE utf8mb4_unicode_ci,
  `created_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`record_id`),
  KEY `ix_approval_rec` (`tenant_id`,`instance_id`),
  CONSTRAINT `fk_approval_records_0` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `audit_logs` (
  `audit_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `actor_id` bigint(20) DEFAULT NULL,
  `action` text COLLATE utf8mb4_unicode_ci,
  `entity` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `entity_id` bigint(20) DEFAULT NULL,
  `ip` text COLLATE utf8mb4_unicode_ci,
  `detail` text COLLATE utf8mb4_unicode_ci,
  `created_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`audit_id`),
  KEY `ix_audit` (`tenant_id`,`entity`,`entity_id`),
  CONSTRAINT `fk_audit_logs_0` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `babies` (
  `baby_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `store_id` bigint(20) DEFAULT NULL,
  `customer_id` bigint(20) NOT NULL,
  `name` text COLLATE utf8mb4_unicode_ci,
  `gender` text COLLATE utf8mb4_unicode_ci,
  `birth_date` text COLLATE utf8mb4_unicode_ci,
  `birth_weight` decimal(20,4) DEFAULT NULL,
  `note` text COLLATE utf8mb4_unicode_ci,
  `version` bigint(20) NOT NULL DEFAULT '0',
  `created_at` text COLLATE utf8mb4_unicode_ci,
  `deleted_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`baby_id`),
  KEY `ix_babies` (`tenant_id`,`customer_id`),
  KEY `fk_babies_0` (`customer_id`),
  CONSTRAINT `fk_babies_0` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_babies_1` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `baby_logs` (
  `log_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `baby_id` bigint(20) NOT NULL,
  `kind` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `feed_type` text COLLATE utf8mb4_unicode_ci,
  `amount` decimal(20,4) DEFAULT NULL,
  `diaper_type` text COLLATE utf8mb4_unicode_ci,
  `metric` text COLLATE utf8mb4_unicode_ci,
  `metric_value` decimal(20,4) DEFAULT NULL,
  `care_type` text COLLATE utf8mb4_unicode_ci,
  `end_time` text COLLATE utf8mb4_unicode_ci,
  `duration_min` bigint(20) DEFAULT NULL,
  `amount_level` text COLLATE utf8mb4_unicode_ci,
  `note` text COLLATE utf8mb4_unicode_ci,
  `operator_id` bigint(20) DEFAULT NULL,
  `log_time` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`log_id`),
  KEY `ix_baby_logs` (`tenant_id`,`baby_id`,`log_time`),
  CONSTRAINT `fk_baby_logs_0` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `bills` (
  `bill_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `store_id` bigint(20) DEFAULT NULL,
  `bill_no` text COLLATE utf8mb4_unicode_ci,
  `contract_id` bigint(20) DEFAULT NULL,
  `customer_id` bigint(20) NOT NULL,
  `bill_type` text COLLATE utf8mb4_unicode_ci,
  `amount` decimal(20,4) NOT NULL DEFAULT '0.0000',
  `paid_amount` decimal(20,4) NOT NULL DEFAULT '0.0000',
  `pay_ref` text COLLATE utf8mb4_unicode_ci,
  `status` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '待支付',
  `version` bigint(20) NOT NULL DEFAULT '0',
  `remark` text COLLATE utf8mb4_unicode_ci,
  `created_at` text COLLATE utf8mb4_unicode_ci,
  `deleted_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`bill_id`),
  KEY `ix_bills` (`tenant_id`,`customer_id`),
  KEY `fk_bills_0` (`customer_id`),
  CONSTRAINT `fk_bills_0` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_bills_1` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `commission_rules` (
  `rule_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `store_id` bigint(20) DEFAULT NULL,
  `bonus_dim` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `channel` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `role` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `amount` decimal(20,4) NOT NULL DEFAULT '0.0000',
  `unit` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '固定',
  `created_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`rule_id`),
  KEY `ix_commission` (`tenant_id`,`store_id`,`bonus_dim`),
  CONSTRAINT `fk_commission_rules_0` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `contracts` (
  `contract_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `store_id` bigint(20) DEFAULT NULL,
  `customer_id` bigint(20) DEFAULT NULL,
  `contract_no` text COLLATE utf8mb4_unicode_ci,
  `package_name` text COLLATE utf8mb4_unicode_ci,
  `amount` decimal(20,4) DEFAULT NULL,
  `paid` decimal(20,4) DEFAULT NULL,
  `discount_rate` decimal(20,4) DEFAULT NULL,
  `days` bigint(20) DEFAULT NULL,
  `sign_date` text COLLATE utf8mb4_unicode_ci,
  `status` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `note` text COLLATE utf8mb4_unicode_ci,
  `created_at` text COLLATE utf8mb4_unicode_ci,
  `deleted_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`contract_id`),
  KEY `ix_contracts` (`tenant_id`,`store_id`,`status`),
  KEY `fk_contracts_1` (`store_id`),
  KEY `fk_contracts_0` (`customer_id`),
  CONSTRAINT `fk_contracts_0` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_contracts_1` FOREIGN KEY (`store_id`) REFERENCES `stores` (`store_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_contracts_2` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `count_cards` (
  `card_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `store_id` bigint(20) DEFAULT NULL,
  `customer_id` bigint(20) NOT NULL,
  `name` text COLLATE utf8mb4_unicode_ci,
  `item_id` bigint(20) DEFAULT NULL,
  `total_count` bigint(20) NOT NULL DEFAULT '0',
  `used_count` bigint(20) NOT NULL DEFAULT '0',
  `remain_count` bigint(20) NOT NULL DEFAULT '0',
  `valid_start` text COLLATE utf8mb4_unicode_ci,
  `valid_end` text COLLATE utf8mb4_unicode_ci,
  `total_amount` decimal(20,4) NOT NULL DEFAULT '0.0000',
  `unit_price` decimal(20,4) NOT NULL DEFAULT '0.0000',
  `status` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '生效',
  `version` bigint(20) NOT NULL DEFAULT '0',
  `created_at` text COLLATE utf8mb4_unicode_ci,
  `deleted_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`card_id`),
  KEY `ix_count_cards` (`tenant_id`,`customer_id`),
  KEY `fk_count_cards_0` (`customer_id`),
  CONSTRAINT `fk_count_cards_0` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_count_cards_1` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `count_card_logs` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `card_id` bigint(20) NOT NULL,
  `change_count` bigint(20) NOT NULL,
  `after_remain` bigint(20) DEFAULT NULL,
  `amount` decimal(20,4) NOT NULL DEFAULT '0.0000',
  `biz_ref` text COLLATE utf8mb4_unicode_ci,
  `operator_id` bigint(20) DEFAULT NULL,
  `remark` text COLLATE utf8mb4_unicode_ci,
  `created_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`id`),
  KEY `ix_count_card_logs` (`tenant_id`,`card_id`),
  CONSTRAINT `fk_count_card_logs_0` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `coupons` (
  `coupon_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `store_id` bigint(20) DEFAULT NULL,
  `tpl_id` bigint(20) DEFAULT NULL,
  `customer_id` bigint(20) DEFAULT NULL,
  `code` text COLLATE utf8mb4_unicode_ci,
  `type` text COLLATE utf8mb4_unicode_ci,
  `threshold` decimal(20,4) DEFAULT NULL,
  `benefit` decimal(20,4) DEFAULT NULL,
  `status` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '未使用',
  `expire_date` text COLLATE utf8mb4_unicode_ci,
  `used_at` text COLLATE utf8mb4_unicode_ci,
  `order_ref` text COLLATE utf8mb4_unicode_ci,
  `version` bigint(20) NOT NULL DEFAULT '0',
  `created_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`coupon_id`),
  KEY `ix_coupon` (`tenant_id`,`customer_id`,`status`),
  CONSTRAINT `fk_coupons_0` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `coupon_templates` (
  `tpl_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `store_id` bigint(20) DEFAULT NULL,
  `name` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `type` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `threshold` decimal(20,4) NOT NULL DEFAULT '0.0000',
  `benefit` decimal(20,4) NOT NULL DEFAULT '0.0000',
  `valid_days` bigint(20) NOT NULL DEFAULT '30',
  `benefit_kind` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '金额',
  `benefit_json` text COLLATE utf8mb4_unicode_ci,
  `total_qty` bigint(20) NOT NULL DEFAULT '0',
  `issued_qty` bigint(20) NOT NULL DEFAULT '0',
  `status` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '启用',
  `version` bigint(20) NOT NULL DEFAULT '0',
  `created_at` text COLLATE utf8mb4_unicode_ci,
  `deleted_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`tpl_id`),
  KEY `ix_coupon_tpl` (`tenant_id`,`status`),
  CONSTRAINT `fk_coupon_templates_0` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `customers` (
  `customer_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `store_id` bigint(20) DEFAULT NULL,
  `name` text COLLATE utf8mb4_unicode_ci,
  `gender` text COLLATE utf8mb4_unicode_ci,
  `phone` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `wechat` text COLLATE utf8mb4_unicode_ci,
  `id_no` text COLLATE utf8mb4_unicode_ci,
  `id_type` text COLLATE utf8mb4_unicode_ci,
  `age` bigint(20) DEFAULT NULL,
  `native` text COLLATE utf8mb4_unicode_ci,
  `source` text COLLATE utf8mb4_unicode_ci,
  `advisor` text COLLATE utf8mb4_unicode_ci,
  `status` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `domain_first` text COLLATE utf8mb4_unicode_ci,
  `edc` text COLLATE utf8mb4_unicode_ci,
  `parity` text COLLATE utf8mb4_unicode_ci,
  `delivery_type` text COLLATE utf8mb4_unicode_ci,
  `intent_room` text COLLATE utf8mb4_unicode_ci,
  `intent_package` text COLLATE utf8mb4_unicode_ci,
  `referrer` text COLLATE utf8mb4_unicode_ci,
  `referrer_relation` text COLLATE utf8mb4_unicode_ci,
  `referrer_phone` text COLLATE utf8mb4_unicode_ci,
  `review_date` text COLLATE utf8mb4_unicode_ci,
  `prenatal_hospital` text COLLATE utf8mb4_unicode_ci,
  `meal_package` text COLLATE utf8mb4_unicode_ci,
  `level` text COLLATE utf8mb4_unicode_ci,
  `visit_count` bigint(20) DEFAULT NULL,
  `last_consume` text COLLATE utf8mb4_unicode_ci,
  `wx_openid` text COLLATE utf8mb4_unicode_ci,
  `version` bigint(20) NOT NULL DEFAULT '0',
  `created_at` text COLLATE utf8mb4_unicode_ci,
  `updated_at` text COLLATE utf8mb4_unicode_ci,
  `created_by` text COLLATE utf8mb4_unicode_ci,
  `updated_by` text COLLATE utf8mb4_unicode_ci,
  `deleted_at` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`customer_id`),
  KEY `ix_cust_live` (`tenant_id`,`deleted_at`),
  KEY `ix_cust_status` (`tenant_id`,`status`),
  KEY `ix_cust_phone` (`tenant_id`,`phone`),
  KEY `ix_cust_tenant` (`tenant_id`,`store_id`),
  KEY `fk_customers_0` (`store_id`),
  CONSTRAINT `fk_customers_0` FOREIGN KEY (`store_id`) REFERENCES `stores` (`store_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_customers_1` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `customer_accounts` (
  `account_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `customer_id` bigint(20) NOT NULL,
  `phone` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `country_code` varchar(8) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '86',
  `password_hash` text COLLATE utf8mb4_unicode_ci,
  `wx_openid` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `wx_unionid` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `status` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '启用',
  `phone_verified_at` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `password_set_at` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `last_login_at` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `updated_at` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`account_id`),
  UNIQUE KEY `ux_customer_accounts_phone` (`tenant_id`,`phone`),
  UNIQUE KEY `ux_customer_accounts_customer` (`tenant_id`,`customer_id`),
  UNIQUE KEY `ux_customer_accounts_openid` (`tenant_id`,`wx_openid`),
  KEY `ix_customer_accounts_status` (`tenant_id`,`status`),
  KEY `fk_customer_accounts_customer` (`customer_id`),
  CONSTRAINT `fk_customer_accounts_customer` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`),
  CONSTRAINT `fk_customer_accounts_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `customer_agreements` (
  `agreement_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `customer_id` bigint(20) NOT NULL,
  `agreement_type` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `agreement_version` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `source` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'mom-weixin',
  `agreed_at` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`agreement_id`),
  UNIQUE KEY `ux_customer_agreements_version` (`tenant_id`,`customer_id`,`agreement_type`,`agreement_version`),
  KEY `ix_customer_agreements_customer` (`tenant_id`,`customer_id`,`agreed_at`),
  KEY `fk_customer_agreements_customer` (`customer_id`),
  CONSTRAINT `fk_customer_agreements_customer` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`),
  CONSTRAINT `fk_customer_agreements_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `customer_family_bindings` (
  `binding_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `owner_customer_id` bigint(20) NOT NULL,
  `member_customer_id` bigint(20) NOT NULL,
  `baby_id` bigint(20) DEFAULT NULL,
  `relationship` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `custom_identity` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `status` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '已验证',
  `verified_by` bigint(20) NOT NULL,
  `verified_at` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `updated_at` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`binding_id`),
  UNIQUE KEY `ux_customer_family_binding` (`tenant_id`,`owner_customer_id`,`member_customer_id`),
  KEY `ix_customer_family_member` (`tenant_id`,`member_customer_id`,`status`),
  KEY `fk_family_bindings_owner` (`owner_customer_id`),
  KEY `fk_family_bindings_member` (`member_customer_id`),
  KEY `fk_family_bindings_baby` (`baby_id`),
  KEY `fk_family_bindings_verified_by` (`verified_by`),
  CONSTRAINT `fk_family_bindings_baby` FOREIGN KEY (`baby_id`) REFERENCES `babies` (`baby_id`),
  CONSTRAINT `fk_family_bindings_member` FOREIGN KEY (`member_customer_id`) REFERENCES `customers` (`customer_id`),
  CONSTRAINT `fk_family_bindings_owner` FOREIGN KEY (`owner_customer_id`) REFERENCES `customers` (`customer_id`),
  CONSTRAINT `fk_family_bindings_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`),
  CONSTRAINT `fk_family_bindings_verified_by` FOREIGN KEY (`verified_by`) REFERENCES `customers` (`customer_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `customer_family_invites` (
  `invite_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `owner_customer_id` bigint(20) NOT NULL,
  `baby_id` bigint(20) DEFAULT NULL,
  `scene_code` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '待绑定',
  `expires_at` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `used_by` bigint(20) DEFAULT NULL,
  `used_at` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `updated_at` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`invite_id`),
  UNIQUE KEY `ux_customer_family_invites_scene` (`scene_code`),
  KEY `ix_customer_family_invites_owner` (`tenant_id`,`owner_customer_id`,`status`,`expires_at`),
  KEY `fk_family_invites_owner` (`owner_customer_id`),
  KEY `fk_family_invites_baby` (`baby_id`),
  KEY `fk_family_invites_used_by` (`used_by`),
  CONSTRAINT `fk_family_invites_baby` FOREIGN KEY (`baby_id`) REFERENCES `babies` (`baby_id`),
  CONSTRAINT `fk_family_invites_owner` FOREIGN KEY (`owner_customer_id`) REFERENCES `customers` (`customer_id`),
  CONSTRAINT `fk_family_invites_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`),
  CONSTRAINT `fk_family_invites_used_by` FOREIGN KEY (`used_by`) REFERENCES `customers` (`customer_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `customer_profiles` (
  `profile_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `customer_id` bigint(20) NOT NULL,
  `display_name` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `guardian_role` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'unknown',
  `service_stage` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'exploring',
  `baby_birth_date` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `feeding_mode` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `care_concerns_json` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `onboarding_status` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'pending',
  `onboarding_version` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '2026-07-21.1',
  `completed_at` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `updated_at` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`profile_id`),
  UNIQUE KEY `ux_customer_profiles_customer` (`tenant_id`,`customer_id`),
  KEY `fk_customer_profiles_customer` (`customer_id`),
  CONSTRAINT `fk_customer_profiles_customer` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`),
  CONSTRAINT `fk_customer_profiles_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `customer_segments` (
  `segment_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `store_id` bigint(20) DEFAULT NULL,
  `name` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `conditions` text COLLATE utf8mb4_unicode_ci,
  `created_by` bigint(20) DEFAULT NULL,
  `version` bigint(20) NOT NULL DEFAULT '0',
  `created_at` text COLLATE utf8mb4_unicode_ci,
  `deleted_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`segment_id`),
  KEY `ix_segment` (`tenant_id`),
  CONSTRAINT `fk_customer_segments_0` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `customer_service_requests` (
  `request_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `store_id` bigint(20) DEFAULT NULL,
  `customer_id` bigint(20) NOT NULL,
  `qr_code_id` bigint(20) DEFAULT NULL,
  `room_id` bigint(20) DEFAULT NULL,
  `request_type` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `content` text COLLATE utf8mb4_unicode_ci,
  `preferred_time` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `status` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '待接单',
  `assignee` bigint(20) DEFAULT NULL,
  `handled_note` text COLLATE utf8mb4_unicode_ci,
  `created_at` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `accepted_at` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `completed_at` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `updated_at` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `deleted_at` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`request_id`),
  KEY `ix_customer_service_requests_customer` (`tenant_id`,`customer_id`,`status`,`created_at`),
  KEY `ix_customer_service_requests_store` (`tenant_id`,`store_id`,`status`,`created_at`),
  KEY `fk_customer_service_requests_store` (`store_id`),
  KEY `fk_customer_service_requests_customer` (`customer_id`),
  KEY `fk_customer_service_requests_qr` (`qr_code_id`),
  KEY `fk_customer_service_requests_room` (`room_id`),
  CONSTRAINT `fk_customer_service_requests_customer` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`),
  CONSTRAINT `fk_customer_service_requests_qr` FOREIGN KEY (`qr_code_id`) REFERENCES `miniapp_qr_codes` (`qr_code_id`),
  CONSTRAINT `fk_customer_service_requests_room` FOREIGN KEY (`room_id`) REFERENCES `rooms` (`room_id`),
  CONSTRAINT `fk_customer_service_requests_store` FOREIGN KEY (`store_id`) REFERENCES `stores` (`store_id`),
  CONSTRAINT `fk_customer_service_requests_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `dictionaries` (
  `dict_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `dict_code` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `item_value` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `item_label` text COLLATE utf8mb4_unicode_ci,
  `sort` bigint(20) DEFAULT '0',
  `status` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`dict_id`),
  KEY `ix_dictionaries` (`tenant_id`,`dict_code`,`sort`),
  CONSTRAINT `fk_dictionaries_0` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `diet_plans` (
  `plan_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `store_id` bigint(20) DEFAULT NULL,
  `customer_id` bigint(20) DEFAULT NULL,
  `meal_date` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `meal_type` text COLLATE utf8mb4_unicode_ci,
  `dishes_json` text COLLATE utf8mb4_unicode_ci,
  `calorie` bigint(20) DEFAULT NULL,
  `status` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT '已发布',
  `delivery_status` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT '待配送',
  `created_at` text COLLATE utf8mb4_unicode_ci,
  `deleted_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`plan_id`),
  KEY `ix_diet` (`tenant_id`,`customer_id`,`meal_date`),
  KEY `ix_diet_delivery` (`tenant_id`,`store_id`,`meal_date`,`delivery_status`),
  KEY `fk_diet_plans_0` (`customer_id`),
  CONSTRAINT `fk_diet_plans_0` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_diet_plans_1` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `dispatch_rewards` (
  `reward_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `store_id` bigint(20) DEFAULT NULL,
  `dispatch_id` bigint(20) DEFAULT NULL,
  `nanny_id` bigint(20) DEFAULT NULL,
  `kind` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `amount` decimal(20,4) NOT NULL DEFAULT '0.0000',
  `reason` text COLLATE utf8mb4_unicode_ci,
  `created_at` text COLLATE utf8mb4_unicode_ci,
  `deleted_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`reward_id`),
  KEY `ix_dispatch_reward` (`tenant_id`,`dispatch_id`,`nanny_id`),
  CONSTRAINT `fk_dispatch_rewards_0` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `expense_orders` (
  `expense_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `store_id` bigint(20) DEFAULT NULL,
  `expense_no` text COLLATE utf8mb4_unicode_ci,
  `expense_type` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `apply_amount` decimal(20,4) NOT NULL DEFAULT '0.0000',
  `actual_amount` decimal(20,4) DEFAULT NULL,
  `pay_method` text COLLATE utf8mb4_unicode_ci,
  `status` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '待审核',
  `approval_id` bigint(20) DEFAULT NULL,
  `payee` text COLLATE utf8mb4_unicode_ci,
  `invoice_no` text COLLATE utf8mb4_unicode_ci,
  `reason` text COLLATE utf8mb4_unicode_ci,
  `apply_date` text COLLATE utf8mb4_unicode_ci,
  `audit_date` text COLLATE utf8mb4_unicode_ci,
  `pay_date` text COLLATE utf8mb4_unicode_ci,
  `version` bigint(20) NOT NULL DEFAULT '0',
  `created_at` text COLLATE utf8mb4_unicode_ci,
  `deleted_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`expense_id`),
  KEY `ix_expense` (`tenant_id`,`status`,`expense_type`),
  CONSTRAINT `fk_expense_orders_0` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `finance_records` (
  `finance_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `store_id` bigint(20) DEFAULT NULL,
  `direction` text COLLATE utf8mb4_unicode_ci,
  `category` text COLLATE utf8mb4_unicode_ci,
  `amount` decimal(20,4) DEFAULT NULL,
  `handler` text COLLATE utf8mb4_unicode_ci,
  `status` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `occurred_at` text COLLATE utf8mb4_unicode_ci,
  `note` text COLLATE utf8mb4_unicode_ci,
  `created_at` text COLLATE utf8mb4_unicode_ci,
  `deleted_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`finance_id`),
  KEY `ix_finance` (`tenant_id`,`store_id`,`status`),
  KEY `fk_finance_records_0` (`store_id`),
  CONSTRAINT `fk_finance_records_0` FOREIGN KEY (`store_id`) REFERENCES `stores` (`store_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_finance_records_1` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `handovers` (
  `handover_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `store_id` bigint(20) DEFAULT NULL,
  `customer_id` bigint(20) DEFAULT NULL,
  `kind` text COLLATE utf8mb4_unicode_ci,
  `items_json` text COLLATE utf8mb4_unicode_ci,
  `operator` text COLLATE utf8mb4_unicode_ci,
  `status` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT '待确认',
  `time` text COLLATE utf8mb4_unicode_ci,
  `deleted_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`handover_id`),
  KEY `ix_handovers` (`tenant_id`,`customer_id`),
  KEY `fk_handovers_0` (`store_id`),
  KEY `fk_handovers_1` (`customer_id`),
  CONSTRAINT `fk_handovers_0` FOREIGN KEY (`store_id`) REFERENCES `stores` (`store_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_handovers_1` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_handovers_2` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `health_profiles` (
  `profile_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `store_id` bigint(20) DEFAULT NULL,
  `customer_id` bigint(20) NOT NULL,
  `domain` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '月子',
  `fetus_type` text COLLATE utf8mb4_unicode_ci,
  `delivery_type` text COLLATE utf8mb4_unicode_ci,
  `gestational_weeks` decimal(20,4) DEFAULT NULL,
  `postpartum_day` bigint(20) DEFAULT NULL,
  `height` decimal(20,4) DEFAULT NULL,
  `weight` decimal(20,4) DEFAULT NULL,
  `pre_pregnancy_weight` decimal(20,4) DEFAULT NULL,
  `blood_type` text COLLATE utf8mb4_unicode_ci,
  `past_history` text COLLATE utf8mb4_unicode_ci,
  `allergy` text COLLATE utf8mb4_unicode_ci,
  `assess_stage` text COLLATE utf8mb4_unicode_ci,
  `notes` text COLLATE utf8mb4_unicode_ci,
  `created_by` text COLLATE utf8mb4_unicode_ci,
  `version` bigint(20) NOT NULL DEFAULT '0',
  `created_at` text COLLATE utf8mb4_unicode_ci,
  `updated_at` text COLLATE utf8mb4_unicode_ci,
  `deleted_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`profile_id`),
  KEY `ix_health` (`tenant_id`,`customer_id`,`domain`),
  CONSTRAINT `fk_health_profiles_0` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `idempotency_keys` (
  `tenant_id` bigint(20) NOT NULL,
  `key` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `result_json` text COLLATE utf8mb4_unicode_ci,
  `created_at` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`tenant_id`,`key`),
  KEY `ix_idem_created` (`created_at`),
  CONSTRAINT `fk_idempotency_keys_0` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `inventory` (
  `tenant_id` bigint(20) NOT NULL,
  `store_id` bigint(20) NOT NULL,
  `item_id` bigint(20) NOT NULL,
  `qty` bigint(20) NOT NULL DEFAULT '0',
  `warn_qty` bigint(20) NOT NULL DEFAULT '0',
  `avg_cost` decimal(20,4) NOT NULL DEFAULT '0.0000',
  `version` bigint(20) NOT NULL DEFAULT '0',
  PRIMARY KEY (`tenant_id`,`store_id`,`item_id`),
  KEY `ix_inv` (`tenant_id`,`store_id`),
  KEY `fk_inventory_0` (`item_id`),
  CONSTRAINT `fk_inventory_0` FOREIGN KEY (`item_id`) REFERENCES `items` (`item_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_inventory_1` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `inventory_batches` (
  `batch_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `store_id` bigint(20) NOT NULL,
  `item_id` bigint(20) NOT NULL,
  `batch_no` text COLLATE utf8mb4_unicode_ci,
  `qty` bigint(20) NOT NULL DEFAULT '0',
  `production_date` text COLLATE utf8mb4_unicode_ci,
  `expiry_date` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `ref` text COLLATE utf8mb4_unicode_ci,
  `version` bigint(20) NOT NULL DEFAULT '0',
  `created_at` text COLLATE utf8mb4_unicode_ci,
  `deleted_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`batch_id`),
  KEY `ix_batch` (`tenant_id`,`store_id`,`item_id`,`expiry_date`),
  KEY `fk_inventory_batches_0` (`item_id`),
  KEY `fk_inventory_batches_1` (`store_id`),
  CONSTRAINT `fk_inventory_batches_0` FOREIGN KEY (`item_id`) REFERENCES `items` (`item_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_inventory_batches_1` FOREIGN KEY (`store_id`) REFERENCES `stores` (`store_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_inventory_batches_2` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `invoices` (
  `invoice_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `store_id` bigint(20) DEFAULT NULL,
  `invoice_no` text COLLATE utf8mb4_unicode_ci,
  `invoice_type` text COLLATE utf8mb4_unicode_ci,
  `title` text COLLATE utf8mb4_unicode_ci,
  `tax_no` text COLLATE utf8mb4_unicode_ci,
  `reg_address` text COLLATE utf8mb4_unicode_ci,
  `reg_phone` text COLLATE utf8mb4_unicode_ci,
  `bank` text COLLATE utf8mb4_unicode_ci,
  `bank_account` text COLLATE utf8mb4_unicode_ci,
  `amount` decimal(20,4) NOT NULL DEFAULT '0.0000',
  `tax_rate` decimal(20,4) DEFAULT NULL,
  `tax_amount` decimal(20,4) DEFAULT NULL,
  `source_type` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `source_ref` text COLLATE utf8mb4_unicode_ci,
  `customer_id` bigint(20) DEFAULT NULL,
  `status` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '正常',
  `red_flush_of` bigint(20) DEFAULT NULL,
  `issue_date` text COLLATE utf8mb4_unicode_ci,
  `version` bigint(20) NOT NULL DEFAULT '0',
  `created_at` text COLLATE utf8mb4_unicode_ci,
  `deleted_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`invoice_id`),
  KEY `ix_invoice` (`tenant_id`,`status`,`source_type`),
  CONSTRAINT `fk_invoices_0` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `items` (
  `item_id` bigint(20) NOT NULL,
  `tenant_id` bigint(20) NOT NULL,
  `domain` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `name` text COLLATE utf8mb4_unicode_ci,
  `cat` text COLLATE utf8mb4_unicode_ci,
  `sale_price` decimal(20,4) DEFAULT NULL,
  `exp_price` decimal(20,4) DEFAULT NULL,
  `cost_price` decimal(20,4) DEFAULT '0.0000',
  `duration` bigint(20) DEFAULT NULL,
  `member_commission` decimal(20,4) DEFAULT NULL,
  `walkin_commission` decimal(20,4) DEFAULT NULL,
  `member_bonus` bigint(20) DEFAULT NULL,
  `status` text COLLATE utf8mb4_unicode_ci,
  `unit` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`item_id`),
  KEY `ix_items_tenant` (`tenant_id`,`domain`),
  CONSTRAINT `fk_items_0` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `item_bundles` (
  `bundle_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `domain` text COLLATE utf8mb4_unicode_ci,
  `name` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `price` decimal(20,4) NOT NULL DEFAULT '0.0000',
  `times` bigint(20) DEFAULT NULL,
  `note` text COLLATE utf8mb4_unicode_ci,
  `status` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '启用',
  `version` bigint(20) NOT NULL DEFAULT '0',
  `created_at` text COLLATE utf8mb4_unicode_ci,
  `deleted_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`bundle_id`),
  KEY `ix_bundles` (`tenant_id`,`status`),
  CONSTRAINT `fk_item_bundles_0` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `item_bundle_lines` (
  `line_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `bundle_id` bigint(20) NOT NULL,
  `tenant_id` bigint(20) NOT NULL,
  `item_id` bigint(20) NOT NULL,
  `qty` bigint(20) NOT NULL DEFAULT '1',
  PRIMARY KEY (`line_id`),
  KEY `ix_bundle_lines` (`tenant_id`,`bundle_id`),
  KEY `fk_item_bundle_lines_0` (`item_id`),
  KEY `fk_item_bundle_lines_1` (`bundle_id`),
  CONSTRAINT `fk_item_bundle_lines_0` FOREIGN KEY (`item_id`) REFERENCES `items` (`item_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_item_bundle_lines_1` FOREIGN KEY (`bundle_id`) REFERENCES `item_bundles` (`bundle_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `item_materials` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `item_id` bigint(20) NOT NULL,
  `material_item_id` bigint(20) NOT NULL,
  `qty` decimal(20,4) NOT NULL DEFAULT '0.0000',
  `unit` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`id`),
  KEY `ix_item_materials` (`tenant_id`,`item_id`),
  KEY `fk_item_materials_0` (`material_item_id`),
  KEY `fk_item_materials_1` (`item_id`),
  CONSTRAINT `fk_item_materials_0` FOREIGN KEY (`material_item_id`) REFERENCES `items` (`item_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_item_materials_1` FOREIGN KEY (`item_id`) REFERENCES `items` (`item_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_item_materials_2` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `leads` (
  `lead_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `store_id` bigint(20) DEFAULT NULL,
  `name` text COLLATE utf8mb4_unicode_ci,
  `phone` text COLLATE utf8mb4_unicode_ci,
  `wechat` text COLLATE utf8mb4_unicode_ci,
  `source` text COLLATE utf8mb4_unicode_ci,
  `status` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `assignee` text COLLATE utf8mb4_unicode_ci,
  `in_pool` bigint(20) NOT NULL DEFAULT '0',
  `edc` text COLLATE utf8mb4_unicode_ci,
  `note` text COLLATE utf8mb4_unicode_ci,
  `created_at` text COLLATE utf8mb4_unicode_ci,
  `deleted_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`lead_id`),
  KEY `ix_leads` (`tenant_id`,`status`,`in_pool`),
  KEY `fk_leads_0` (`store_id`),
  CONSTRAINT `fk_leads_0` FOREIGN KEY (`store_id`) REFERENCES `stores` (`store_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_leads_1` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `mall_orders` (
  `mall_order_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `customer_id` bigint(20) DEFAULT NULL,
  `product_id` bigint(20) DEFAULT NULL,
  `qty` bigint(20) DEFAULT NULL,
  `amount` decimal(20,4) DEFAULT NULL,
  `pay_kind` text COLLATE utf8mb4_unicode_ci,
  `created_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`mall_order_id`),
  KEY `fk_mall_orders_0` (`product_id`),
  KEY `fk_mall_orders_1` (`tenant_id`),
  CONSTRAINT `fk_mall_orders_0` FOREIGN KEY (`product_id`) REFERENCES `products` (`product_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_mall_orders_1` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `meal_dishes` (
  `dish_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `name` text COLLATE utf8mb4_unicode_ci,
  `category` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `nutrients` text COLLATE utf8mb4_unicode_ci,
  `status` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '启用',
  `note` text COLLATE utf8mb4_unicode_ci,
  `created_at` text COLLATE utf8mb4_unicode_ci,
  `deleted_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`dish_id`),
  KEY `ix_meal_dishes` (`tenant_id`,`category`),
  CONSTRAINT `fk_meal_dishes_0` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `meal_plans` (
  `plan_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `store_id` bigint(20) DEFAULT NULL,
  `name` text COLLATE utf8mb4_unicode_ci,
  `stage` text COLLATE utf8mb4_unicode_ci,
  `days` bigint(20) DEFAULT NULL,
  `status` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '启用',
  `note` text COLLATE utf8mb4_unicode_ci,
  `created_at` text COLLATE utf8mb4_unicode_ci,
  `deleted_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`plan_id`),
  KEY `ix_meal_plans` (`tenant_id`),
  CONSTRAINT `fk_meal_plans_0` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `meal_plan_items` (
  `item_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `plan_id` bigint(20) NOT NULL,
  `day_no` bigint(20) NOT NULL DEFAULT '1',
  `meal_type` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `dish_id` bigint(20) DEFAULT NULL,
  `dish_name` text COLLATE utf8mb4_unicode_ci,
  `created_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`item_id`),
  KEY `ix_meal_plan_items` (`tenant_id`,`plan_id`,`day_no`),
  CONSTRAINT `fk_meal_plan_items_0` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `media` (
  `media_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `ref_type` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ref_id` bigint(20) DEFAULT NULL,
  `tag` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `filename` text COLLATE utf8mb4_unicode_ci,
  `mime` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `bytes` longblob NOT NULL,
  `size` bigint(20) NOT NULL,
  `visibility` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'public',
  `sort` bigint(20) NOT NULL DEFAULT '0',
  `alt` text COLLATE utf8mb4_unicode_ci,
  `uploaded_by` text COLLATE utf8mb4_unicode_ci,
  `created_at` text COLLATE utf8mb4_unicode_ci,
  `deleted_at` text COLLATE utf8mb4_unicode_ci,
  `storage` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'local',
  `storage_key` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`media_id`),
  KEY `ix_media_tag` (`tenant_id`,`tag`,`sort`),
  KEY `ix_media` (`tenant_id`,`ref_type`,`ref_id`,`sort`),
  CONSTRAINT `fk_media_0` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `member_card` (
  `card_id` bigint(20) NOT NULL,
  `customer_id` bigint(20) NOT NULL,
  `card_no` text COLLATE utf8mb4_unicode_ci,
  `name` text COLLATE utf8mb4_unicode_ci,
  `total` bigint(20) DEFAULT NULL,
  `remain` bigint(20) DEFAULT NULL,
  `domain` text COLLATE utf8mb4_unicode_ci,
  `expired` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`card_id`),
  KEY `ix_card_cust` (`customer_id`),
  CONSTRAINT `fk_member_card_0` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `member_levels` (
  `tenant_id` bigint(20) NOT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `discount` decimal(20,4) NOT NULL DEFAULT '1.0000',
  `sort` bigint(20) DEFAULT '0',
  PRIMARY KEY (`tenant_id`,`name`),
  CONSTRAINT `fk_member_levels_0` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `member_wallet` (
  `customer_id` bigint(20) NOT NULL,
  `tenant_id` bigint(20) NOT NULL,
  `stored_card_balance` decimal(20,4) NOT NULL DEFAULT '0.0000',
  `points` bigint(20) NOT NULL DEFAULT '0',
  `version` bigint(20) NOT NULL DEFAULT '0',
  PRIMARY KEY (`customer_id`),
  KEY `ix_wallet_tenant` (`tenant_id`),
  CONSTRAINT `fk_member_wallet_0` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_member_wallet_1` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `miniapp_qr_codes` (
  `qr_code_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `store_id` bigint(20) DEFAULT NULL,
  `room_id` bigint(20) DEFAULT NULL,
  `scene_code` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `scene_type` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `title` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '启用',
  `expires_at` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `config_json` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_by` bigint(20) DEFAULT NULL,
  `created_at` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `updated_at` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`qr_code_id`),
  UNIQUE KEY `ux_miniapp_qr_scene` (`scene_code`),
  KEY `ix_miniapp_qr_scope` (`tenant_id`,`store_id`,`scene_type`,`status`),
  KEY `fk_miniapp_qr_store` (`store_id`),
  KEY `fk_miniapp_qr_room` (`room_id`),
  CONSTRAINT `fk_miniapp_qr_room` FOREIGN KEY (`room_id`) REFERENCES `rooms` (`room_id`),
  CONSTRAINT `fk_miniapp_qr_store` FOREIGN KEY (`store_id`) REFERENCES `stores` (`store_id`),
  CONSTRAINT `fk_miniapp_qr_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `nannies` (
  `nanny_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `name` text COLLATE utf8mb4_unicode_ci,
  `age` bigint(20) DEFAULT NULL,
  `type` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `level` text COLLATE utf8mb4_unicode_ci,
  `fee` decimal(20,4) DEFAULT NULL,
  `status` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT '可约',
  `phone` text COLLATE utf8mb4_unicode_ci,
  `note` text COLLATE utf8mb4_unicode_ci,
  `deleted_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`nanny_id`),
  KEY `ix_nannies` (`tenant_id`,`type`,`status`),
  CONSTRAINT `fk_nannies_0` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `nanny_dispatch` (
  `dispatch_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `store_id` bigint(20) DEFAULT NULL,
  `nanny_id` bigint(20) DEFAULT NULL,
  `customer_id` bigint(20) DEFAULT NULL,
  `start_date` text COLLATE utf8mb4_unicode_ci,
  `end_date` text COLLATE utf8mb4_unicode_ci,
  `fee` decimal(20,4) DEFAULT NULL,
  `status` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `checked_in` bigint(20) DEFAULT '0',
  `note` text COLLATE utf8mb4_unicode_ci,
  `created_at` text COLLATE utf8mb4_unicode_ci,
  `deleted_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`dispatch_id`),
  KEY `ix_dispatch` (`tenant_id`,`store_id`,`status`),
  KEY `fk_nanny_dispatch_1` (`nanny_id`),
  KEY `fk_nanny_dispatch_0` (`customer_id`),
  CONSTRAINT `fk_nanny_dispatch_0` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_nanny_dispatch_1` FOREIGN KEY (`nanny_id`) REFERENCES `nannies` (`nanny_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_nanny_dispatch_2` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `nanny_settlements` (
  `settlement_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `nanny_id` bigint(20) NOT NULL,
  `settle_no` text COLLATE utf8mb4_unicode_ci,
  `period_from` text COLLATE utf8mb4_unicode_ci,
  `period_to` text COLLATE utf8mb4_unicode_ci,
  `base_fee` decimal(20,4) NOT NULL DEFAULT '0.0000',
  `reward_total` decimal(20,4) NOT NULL DEFAULT '0.0000',
  `penalty` decimal(20,4) NOT NULL DEFAULT '0.0000',
  `net` decimal(20,4) NOT NULL DEFAULT '0.0000',
  `dispatch_count` bigint(20) NOT NULL DEFAULT '0',
  `status` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '已结算',
  `created_by` bigint(20) DEFAULT NULL,
  `created_at` text COLLATE utf8mb4_unicode_ci,
  `deleted_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`settlement_id`),
  KEY `ix_nsettle` (`tenant_id`,`nanny_id`),
  KEY `fk_nanny_settlements_0` (`nanny_id`),
  CONSTRAINT `fk_nanny_settlements_0` FOREIGN KEY (`nanny_id`) REFERENCES `nannies` (`nanny_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_nanny_settlements_1` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `notices` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `customer_id` bigint(20) DEFAULT NULL,
  `type` text COLLATE utf8mb4_unicode_ci,
  `title` text COLLATE utf8mb4_unicode_ci,
  `time` text COLLATE utf8mb4_unicode_ci,
  `read` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_notices_0` (`customer_id`),
  CONSTRAINT `fk_notices_0` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `ops_records` (
  `record_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `store_id` bigint(20) DEFAULT NULL,
  `kind` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `customer_id` bigint(20) DEFAULT NULL,
  `staff_name` text COLLATE utf8mb4_unicode_ci,
  `title` text COLLATE utf8mb4_unicode_ci,
  `category` text COLLATE utf8mb4_unicode_ci,
  `amount` decimal(20,4) DEFAULT NULL,
  `score` bigint(20) DEFAULT NULL,
  `status` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT '待处理',
  `ref_no` text COLLATE utf8mb4_unicode_ci,
  `handler` text COLLATE utf8mb4_unicode_ci,
  `expert` text COLLATE utf8mb4_unicode_ci,
  `ts` text COLLATE utf8mb4_unicode_ci,
  `note` text COLLATE utf8mb4_unicode_ci,
  `created_at` text COLLATE utf8mb4_unicode_ci,
  `deleted_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`record_id`),
  KEY `ix_ops` (`tenant_id`,`kind`,`status`),
  KEY `fk_ops_records_1` (`store_id`),
  KEY `fk_ops_records_0` (`customer_id`),
  CONSTRAINT `fk_ops_records_0` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_ops_records_1` FOREIGN KEY (`store_id`) REFERENCES `stores` (`store_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_ops_records_2` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `orders` (
  `order_no` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `tenant_id` bigint(20) NOT NULL,
  `store_id` bigint(20) DEFAULT NULL,
  `customer_id` bigint(20) DEFAULT NULL,
  `domain` text COLLATE utf8mb4_unicode_ci,
  `order_status` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `order_amount` decimal(20,4) DEFAULT NULL,
  `paid_amount` decimal(20,4) DEFAULT NULL,
  `due_amount` decimal(20,4) DEFAULT NULL,
  `pay_method` text COLLATE utf8mb4_unicode_ci,
  `created_at` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `version` bigint(20) NOT NULL DEFAULT '0',
  `updated_at` text COLLATE utf8mb4_unicode_ci,
  `created_by` text COLLATE utf8mb4_unicode_ci,
  `refund_reason` text COLLATE utf8mb4_unicode_ci,
  `deleted_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`order_no`),
  KEY `ix_orders_store_status` (`tenant_id`,`store_id`,`order_status`),
  KEY `ix_orders_cust` (`tenant_id`,`customer_id`),
  KEY `ix_orders_tenant` (`tenant_id`,`created_at`),
  KEY `fk_orders_1` (`store_id`),
  KEY `fk_orders_0` (`customer_id`),
  CONSTRAINT `fk_orders_0` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_orders_1` FOREIGN KEY (`store_id`) REFERENCES `stores` (`store_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_orders_2` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `order_items` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `order_no` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `tenant_id` bigint(20) DEFAULT NULL,
  `item_id` bigint(20) DEFAULT NULL,
  `name` text COLLATE utf8mb4_unicode_ci,
  `qty` bigint(20) DEFAULT NULL,
  `unit_price` decimal(20,4) DEFAULT NULL,
  `discount` decimal(20,4) DEFAULT NULL,
  `executor` text COLLATE utf8mb4_unicode_ci,
  `hand_fee` decimal(20,4) DEFAULT NULL,
  `performance` decimal(20,4) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_oi_tenant` (`tenant_id`),
  KEY `ix_oi_order` (`order_no`),
  CONSTRAINT `fk_order_items_0` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_order_items_1` FOREIGN KEY (`order_no`) REFERENCES `orders` (`order_no`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `pay_notify_logs` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `pay_no` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `raw` text COLLATE utf8mb4_unicode_ci,
  `result` text COLLATE utf8mb4_unicode_ci,
  `created_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`id`),
  KEY `ix_pay_notify` (`tenant_id`,`pay_no`),
  CONSTRAINT `fk_pay_notify_logs_0` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `pay_orders` (
  `pay_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `store_id` bigint(20) DEFAULT NULL,
  `pay_no` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `bill_id` bigint(20) DEFAULT NULL,
  `customer_id` bigint(20) DEFAULT NULL,
  `provider` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `amount` decimal(20,4) NOT NULL,
  `status` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '待支付',
  `prepay_id` text COLLATE utf8mb4_unicode_ci,
  `transaction_id` text COLLATE utf8mb4_unicode_ci,
  `version` bigint(20) NOT NULL DEFAULT '0',
  `notify_at` text COLLATE utf8mb4_unicode_ci,
  `created_at` text COLLATE utf8mb4_unicode_ci,
  `business_type` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `business_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`pay_id`),
  UNIQUE KEY `ix_pay_orders_no` (`pay_no`),
  KEY `ix_pay_business` (`tenant_id`,`business_type`,`business_id`),
  CONSTRAINT `fk_pay_orders_0` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `points_rules` (
  `rule_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `store_id` bigint(20) DEFAULT NULL,
  `channel` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `enabled` bigint(20) NOT NULL DEFAULT '1',
  `mode` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '固定',
  `value` decimal(20,4) NOT NULL DEFAULT '0.0000',
  `created_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`rule_id`),
  UNIQUE KEY `ux_points_rule` (`tenant_id`,`channel`),
  KEY `ix_points_rule` (`tenant_id`,`channel`),
  CONSTRAINT `fk_points_rules_0` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `point_ledger` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `customer_id` bigint(20) DEFAULT NULL,
  `delta` bigint(20) DEFAULT NULL,
  `balance_after` bigint(20) DEFAULT NULL,
  `reason` text COLLATE utf8mb4_unicode_ci,
  `created_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`id`),
  KEY `ix_pledger` (`tenant_id`,`customer_id`),
  KEY `fk_point_ledger_0` (`customer_id`),
  CONSTRAINT `fk_point_ledger_0` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_point_ledger_1` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `postpartum_assessments` (
  `assess_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `store_id` bigint(20) DEFAULT NULL,
  `customer_id` bigint(20) DEFAULT NULL,
  `nurse_id` bigint(20) DEFAULT NULL,
  `assess_date` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `postpartum_day` bigint(20) DEFAULT NULL,
  `lochia_color` text COLLATE utf8mb4_unicode_ci,
  `lochia_amount` text COLLATE utf8mb4_unicode_ci,
  `fundus` text COLLATE utf8mb4_unicode_ci,
  `perineum_heal` text COLLATE utf8mb4_unicode_ci,
  `perineum_type` text COLLATE utf8mb4_unicode_ci,
  `breast` text COLLATE utf8mb4_unicode_ci,
  `temperature` decimal(20,4) DEFAULT NULL,
  `blood_pressure` text COLLATE utf8mb4_unicode_ci,
  `pulse` bigint(20) DEFAULT NULL,
  `mood` text COLLATE utf8mb4_unicode_ci,
  `notes` text COLLATE utf8mb4_unicode_ci,
  `version` bigint(20) NOT NULL DEFAULT '0',
  `created_at` text COLLATE utf8mb4_unicode_ci,
  `deleted_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`assess_id`),
  KEY `ix_pp_assess` (`tenant_id`,`customer_id`,`assess_date`),
  CONSTRAINT `fk_postpartum_assessments_0` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `posts` (
  `post_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `customer_id` bigint(20) DEFAULT NULL,
  `title` text COLLATE utf8mb4_unicode_ci,
  `body` text COLLATE utf8mb4_unicode_ci,
  `kind` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `likes` bigint(20) NOT NULL DEFAULT '0',
  `status` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT '已发布',
  `created_at` text COLLATE utf8mb4_unicode_ci,
  `deleted_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`post_id`),
  KEY `ix_posts` (`tenant_id`,`kind`,`status`),
  CONSTRAINT `fk_posts_0` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `products` (
  `product_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `name` text COLLATE utf8mb4_unicode_ci,
  `cat` text COLLATE utf8mb4_unicode_ci,
  `price` decimal(20,4) DEFAULT NULL,
  `points_price` bigint(20) DEFAULT NULL,
  `stock` bigint(20) NOT NULL DEFAULT '0',
  `status` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT '在售',
  `version` bigint(20) NOT NULL DEFAULT '0',
  `created_at` text COLLATE utf8mb4_unicode_ci,
  `deleted_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`product_id`),
  KEY `ix_products` (`tenant_id`,`status`),
  CONSTRAINT `fk_products_0` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `promo_rules` (
  `rule_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `domain` text COLLATE utf8mb4_unicode_ci,
  `rule` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '启用',
  `created_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`rule_id`),
  KEY `ix_promo_rules` (`tenant_id`,`status`),
  CONSTRAINT `fk_promo_rules_0` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `purchase_lines` (
  `line_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `po_id` bigint(20) NOT NULL,
  `item_id` bigint(20) NOT NULL,
  `qty` bigint(20) NOT NULL,
  `unit_cost` decimal(20,4) NOT NULL DEFAULT '0.0000',
  `created_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`line_id`),
  KEY `ix_po_line` (`tenant_id`,`po_id`),
  KEY `fk_purchase_lines_0` (`item_id`),
  KEY `fk_purchase_lines_1` (`po_id`),
  CONSTRAINT `fk_purchase_lines_0` FOREIGN KEY (`item_id`) REFERENCES `items` (`item_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_purchase_lines_1` FOREIGN KEY (`po_id`) REFERENCES `purchase_orders` (`po_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_purchase_lines_2` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `purchase_orders` (
  `po_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `store_id` bigint(20) NOT NULL,
  `po_no` text COLLATE utf8mb4_unicode_ci,
  `supplier_id` bigint(20) DEFAULT NULL,
  `supplier` text COLLATE utf8mb4_unicode_ci,
  `status` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '待入库',
  `total_cost` decimal(20,4) NOT NULL DEFAULT '0.0000',
  `note` text COLLATE utf8mb4_unicode_ci,
  `created_by` bigint(20) DEFAULT NULL,
  `received_at` text COLLATE utf8mb4_unicode_ci,
  `version` bigint(20) NOT NULL DEFAULT '0',
  `created_at` text COLLATE utf8mb4_unicode_ci,
  `deleted_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`po_id`),
  KEY `ix_po` (`tenant_id`,`store_id`,`status`),
  KEY `fk_purchase_orders_0` (`store_id`),
  CONSTRAINT `fk_purchase_orders_0` FOREIGN KEY (`store_id`) REFERENCES `stores` (`store_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_purchase_orders_1` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `qa_entries` (
  `qa_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `category` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `question` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `answer` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `keywords` text COLLATE utf8mb4_unicode_ci,
  `source` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '调研',
  `status` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '启用',
  `hit_count` bigint(20) NOT NULL DEFAULT '0',
  `reviewed_by` text COLLATE utf8mb4_unicode_ci,
  `reviewed_at` text COLLATE utf8mb4_unicode_ci,
  `version` bigint(20) NOT NULL DEFAULT '0',
  `created_at` text COLLATE utf8mb4_unicode_ci,
  `deleted_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`qa_id`),
  KEY `ix_qa_entries` (`tenant_id`,`status`,`category`),
  CONSTRAINT `fk_qa_entries_0` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `qa_unanswered` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `customer_id` bigint(20) DEFAULT NULL,
  `query` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '待处理',
  `created_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`id`),
  KEY `ix_qa_unanswered` (`tenant_id`,`status`),
  CONSTRAINT `fk_qa_unanswered_0` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `qc_dept_scores` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `dept` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `year` bigint(20) NOT NULL,
  `month` bigint(20) NOT NULL,
  `score` decimal(20,4) DEFAULT NULL,
  `created_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`id`),
  KEY `ix_qc_dept_scores` (`tenant_id`,`dept`,`year`,`month`),
  CONSTRAINT `fk_qc_dept_scores_0` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `qc_records` (
  `qc_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `store_id` bigint(20) DEFAULT NULL,
  `tpl_id` bigint(20) DEFAULT NULL,
  `dept` text COLLATE utf8mb4_unicode_ci,
  `staff_id` bigint(20) DEFAULT NULL,
  `checker_id` bigint(20) DEFAULT NULL,
  `check_date` text COLLATE utf8mb4_unicode_ci,
  `score` bigint(20) NOT NULL DEFAULT '100',
  `remark` text COLLATE utf8mb4_unicode_ci,
  `status` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '已检查',
  `version` bigint(20) NOT NULL DEFAULT '0',
  `created_at` text COLLATE utf8mb4_unicode_ci,
  `deleted_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`qc_id`),
  KEY `ix_qc_records` (`tenant_id`,`store_id`,`staff_id`),
  CONSTRAINT `fk_qc_records_0` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `qc_record_details` (
  `qcd_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `qc_id` bigint(20) NOT NULL,
  `tenant_id` bigint(20) NOT NULL,
  `qti_id` bigint(20) DEFAULT NULL,
  `deduct` bigint(20) NOT NULL DEFAULT '0',
  `note` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`qcd_id`),
  KEY `ix_qc_rec_details` (`tenant_id`,`qc_id`),
  KEY `fk_qc_record_details_1` (`qc_id`),
  CONSTRAINT `fk_qc_record_details_0` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_qc_record_details_1` FOREIGN KEY (`qc_id`) REFERENCES `qc_records` (`qc_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `qc_templates` (
  `tpl_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `dept` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `deduct_rule` text COLLATE utf8mb4_unicode_ci,
  `status` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '启用',
  `version` bigint(20) NOT NULL DEFAULT '0',
  `created_at` text COLLATE utf8mb4_unicode_ci,
  `deleted_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`tpl_id`),
  KEY `ix_qc_tpl` (`tenant_id`,`dept`,`status`),
  CONSTRAINT `fk_qc_templates_0` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `qc_template_items` (
  `qti_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tpl_id` bigint(20) NOT NULL,
  `tenant_id` bigint(20) NOT NULL,
  `category` text COLLATE utf8mb4_unicode_ci,
  `weight_pct` bigint(20) DEFAULT NULL,
  `seq` bigint(20) DEFAULT NULL,
  `content` text COLLATE utf8mb4_unicode_ci,
  `base_score` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`qti_id`),
  KEY `ix_qc_tpl_items` (`tenant_id`,`tpl_id`),
  KEY `fk_qc_template_items_1` (`tpl_id`),
  CONSTRAINT `fk_qc_template_items_0` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_qc_template_items_1` FOREIGN KEY (`tpl_id`) REFERENCES `qc_templates` (`tpl_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `recharges` (
  `recharge_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `store_id` bigint(20) DEFAULT NULL,
  `customer_id` bigint(20) DEFAULT NULL,
  `tier_id` bigint(20) DEFAULT NULL,
  `amount` decimal(20,4) NOT NULL,
  `gift` decimal(20,4) NOT NULL DEFAULT '0.0000',
  `total` decimal(20,4) NOT NULL,
  `pay_method` text COLLATE utf8mb4_unicode_ci,
  `created_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`recharge_id`),
  KEY `ix_recharge` (`tenant_id`,`customer_id`),
  CONSTRAINT `fk_recharges_0` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `recharge_tiers` (
  `tier_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `store_id` bigint(20) DEFAULT NULL,
  `threshold` decimal(20,4) NOT NULL,
  `gift` decimal(20,4) NOT NULL DEFAULT '0.0000',
  `status` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '启用',
  `created_at` text COLLATE utf8mb4_unicode_ci,
  `deleted_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`tier_id`),
  KEY `ix_recharge_tier` (`tenant_id`,`status`),
  CONSTRAINT `fk_recharge_tiers_0` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `refund_orders` (
  `refund_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `store_id` bigint(20) DEFAULT NULL,
  `refund_no` text COLLATE utf8mb4_unicode_ci,
  `refund_type` text COLLATE utf8mb4_unicode_ci,
  `biz_ref` text COLLATE utf8mb4_unicode_ci,
  `customer_id` bigint(20) DEFAULT NULL,
  `apply_amount` decimal(20,4) NOT NULL DEFAULT '0.0000',
  `actual_amount` decimal(20,4) DEFAULT NULL,
  `pay_method` text COLLATE utf8mb4_unicode_ci,
  `status` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '待审核',
  `approval_id` bigint(20) DEFAULT NULL,
  `payee` text COLLATE utf8mb4_unicode_ci,
  `pay_date` text COLLATE utf8mb4_unicode_ci,
  `reason` text COLLATE utf8mb4_unicode_ci,
  `version` bigint(20) NOT NULL DEFAULT '0',
  `created_at` text COLLATE utf8mb4_unicode_ci,
  `deleted_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`refund_id`),
  KEY `ix_refund` (`tenant_id`,`status`,`customer_id`),
  CONSTRAINT `fk_refund_orders_0` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `roles` (
  `role_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `perms_json` text COLLATE utf8mb4_unicode_ci,
  `is_manager` bigint(20) DEFAULT '0',
  `is_system` bigint(20) DEFAULT '0',
  `data_scope` bigint(20) DEFAULT '4',
  `description` text COLLATE utf8mb4_unicode_ci,
  `created_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`role_id`),
  UNIQUE KEY `ix_roles_tenant` (`tenant_id`,`name`),
  CONSTRAINT `fk_roles_0` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `rooms` (
  `room_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `store_id` bigint(20) DEFAULT NULL,
  `customer_id` bigint(20) DEFAULT NULL,
  `room_no` text COLLATE utf8mb4_unicode_ci,
  `room_type` text COLLATE utf8mb4_unicode_ci,
  `floor` bigint(20) DEFAULT NULL,
  `direction` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '南',
  `layout_order` bigint(20) NOT NULL DEFAULT '0',
  `customer_visible` tinyint(4) NOT NULL DEFAULT '1',
  `price` decimal(20,4) DEFAULT NULL,
  `status` text COLLATE utf8mb4_unicode_ci,
  `note` text COLLATE utf8mb4_unicode_ci,
  `created_at` text COLLATE utf8mb4_unicode_ci,
  `deleted_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`room_id`),
  KEY `ix_rooms` (`tenant_id`,`store_id`,`floor`),
  KEY `fk_rooms_1` (`store_id`),
  KEY `fk_rooms_0` (`customer_id`),
  KEY `ix_rooms_customer_layout` (`tenant_id`,`store_id`,`floor`,`direction`,`layout_order`),
  CONSTRAINT `fk_rooms_0` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_rooms_1` FOREIGN KEY (`store_id`) REFERENCES `stores` (`store_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_rooms_2` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `room_bookings` (
  `booking_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `store_id` bigint(20) DEFAULT NULL,
  `room_id` bigint(20) NOT NULL,
  `customer_id` bigint(20) DEFAULT NULL,
  `check_in` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `check_out` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '预订',
  `note` text COLLATE utf8mb4_unicode_ci,
  `version` bigint(20) NOT NULL DEFAULT '0',
  `created_at` text COLLATE utf8mb4_unicode_ci,
  `deleted_at` text COLLATE utf8mb4_unicode_ci,
  `booking_no` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `amount` decimal(20,4) DEFAULT NULL,
  `payment_status` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '无需支付',
  `pay_id` bigint(20) DEFAULT NULL,
  `source` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `paid_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`booking_id`),
  UNIQUE KEY `ix_room_booking_no` (`booking_no`),
  KEY `ix_room_booking` (`tenant_id`,`room_id`,`status`),
  CONSTRAINT `fk_room_bookings_0` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `room_turnover_tasks` (
  `task_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `store_id` bigint(20) DEFAULT NULL,
  `room_id` bigint(20) NOT NULL,
  `booking_id` bigint(20) NOT NULL,
  `task_type` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `scheduled_date` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '待处理',
  `assignee_id` bigint(20) DEFAULT NULL,
  `checklist_json` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `result_note` text COLLATE utf8mb4_unicode_ci,
  `completed_at` text COLLATE utf8mb4_unicode_ci,
  `created_at` text COLLATE utf8mb4_unicode_ci,
  `updated_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`task_id`),
  UNIQUE KEY `ux_room_turnover_booking_type` (`tenant_id`,`booking_id`,`task_type`),
  KEY `ix_room_turnover_floor` (`tenant_id`,`store_id`,`scheduled_date`,`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sales_rewards` (
  `reward_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `domain` text COLLATE utf8mb4_unicode_ci,
  `name` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `amount` decimal(20,4) DEFAULT NULL,
  `cond_text` text COLLATE utf8mb4_unicode_ci,
  `status` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '启用',
  `created_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`reward_id`),
  KEY `ix_sales_rewards` (`tenant_id`,`status`),
  CONSTRAINT `fk_sales_rewards_0` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `schedules` (
  `schedule_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `store_id` bigint(20) DEFAULT NULL,
  `staff_id` bigint(20) DEFAULT NULL,
  `work_date` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `shift` text COLLATE utf8mb4_unicode_ci,
  `status` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT '正常',
  `note` text COLLATE utf8mb4_unicode_ci,
  `deleted_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`schedule_id`),
  KEY `ix_schedules` (`tenant_id`,`store_id`,`work_date`),
  KEY `fk_schedules_0` (`store_id`),
  KEY `fk_schedules_1` (`staff_id`),
  CONSTRAINT `fk_schedules_0` FOREIGN KEY (`store_id`) REFERENCES `stores` (`store_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_schedules_1` FOREIGN KEY (`staff_id`) REFERENCES `staff` (`staff_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_schedules_2` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `services` (
  `service_id` bigint(20) NOT NULL,
  `customer_id` bigint(20) DEFAULT NULL,
  `tenant_id` bigint(20) NOT NULL,
  `store_id` bigint(20) DEFAULT NULL,
  `domain` text COLLATE utf8mb4_unicode_ci,
  `time` text COLLATE utf8mb4_unicode_ci,
  `tech` text COLLATE utf8mb4_unicode_ci,
  `status` text COLLATE utf8mb4_unicode_ci,
  `type` text COLLATE utf8mb4_unicode_ci,
  `room_no` text COLLATE utf8mb4_unicode_ci,
  `baby_name` text COLLATE utf8mb4_unicode_ci,
  `abnormal` text COLLATE utf8mb4_unicode_ci,
  `rooming_in` bigint(20) DEFAULT NULL,
  `rehab_items` bigint(20) DEFAULT NULL,
  `care_items` bigint(20) DEFAULT NULL,
  `project` text COLLATE utf8mb4_unicode_ci,
  `consume` bigint(20) DEFAULT NULL,
  `record_kind` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`service_id`),
  KEY `ix_svc_tenant` (`tenant_id`,`store_id`,`customer_id`),
  KEY `fk_services_0` (`store_id`),
  KEY `fk_services_1` (`customer_id`),
  CONSTRAINT `fk_services_0` FOREIGN KEY (`store_id`) REFERENCES `stores` (`store_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_services_1` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_services_2` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `service_choices` (
  `choice_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `recommendation_id` bigint(20) NOT NULL,
  `recommendation_item_id` bigint(20) NOT NULL,
  `customer_id` bigint(20) NOT NULL,
  `choice_status` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `reject_reason_codes` text COLLATE utf8mb4_unicode_ci,
  `reject_reason_text` text COLLATE utf8mb4_unicode_ci,
  `chosen_by` bigint(20) NOT NULL,
  `chosen_at` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `updated_at` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`choice_id`),
  UNIQUE KEY `ux_service_choice_item_customer` (`tenant_id`,`recommendation_item_id`,`customer_id`),
  KEY `ix_service_choices_customer` (`tenant_id`,`customer_id`,`chosen_at`),
  KEY `fk_service_choices_rec` (`recommendation_id`),
  KEY `fk_service_choices_rec_item` (`recommendation_item_id`),
  KEY `fk_service_choices_customer` (`customer_id`),
  CONSTRAINT `fk_service_choices_customer` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`),
  CONSTRAINT `fk_service_choices_rec` FOREIGN KEY (`recommendation_id`) REFERENCES `service_recommendations` (`recommendation_id`),
  CONSTRAINT `fk_service_choices_rec_item` FOREIGN KEY (`recommendation_item_id`) REFERENCES `service_recommendation_items` (`recommendation_item_id`),
  CONSTRAINT `fk_service_choices_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `service_recommendations` (
  `recommendation_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `store_id` bigint(20) DEFAULT NULL,
  `customer_id` bigint(20) NOT NULL,
  `baby_id` bigint(20) DEFAULT NULL,
  `subject_type` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'mom',
  `title` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `summary` text COLLATE utf8mb4_unicode_ci,
  `status` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '待确认',
  `expert_id` bigint(20) NOT NULL,
  `sent_at` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `updated_at` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `deleted_at` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`recommendation_id`),
  KEY `ix_service_recommendations_customer` (`tenant_id`,`customer_id`,`status`,`created_at`),
  KEY `ix_service_recommendations_store` (`tenant_id`,`store_id`,`status`,`created_at`),
  KEY `fk_service_recommendations_store` (`store_id`),
  KEY `fk_service_recommendations_customer` (`customer_id`),
  KEY `fk_service_recommendations_baby` (`baby_id`),
  KEY `fk_service_recommendations_expert` (`expert_id`),
  CONSTRAINT `fk_service_recommendations_baby` FOREIGN KEY (`baby_id`) REFERENCES `babies` (`baby_id`),
  CONSTRAINT `fk_service_recommendations_customer` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`),
  CONSTRAINT `fk_service_recommendations_expert` FOREIGN KEY (`expert_id`) REFERENCES `staff` (`staff_id`),
  CONSTRAINT `fk_service_recommendations_store` FOREIGN KEY (`store_id`) REFERENCES `stores` (`store_id`),
  CONSTRAINT `fk_service_recommendations_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `service_recommendation_items` (
  `recommendation_item_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `recommendation_id` bigint(20) NOT NULL,
  `item_id` bigint(20) NOT NULL,
  `priority` int(11) NOT NULL DEFAULT '1',
  `reason` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `price_snapshot` decimal(12,2) DEFAULT NULL,
  `created_at` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`recommendation_item_id`),
  UNIQUE KEY `ux_service_recommendation_item` (`tenant_id`,`recommendation_id`,`item_id`),
  KEY `ix_service_recommendation_items_rec` (`tenant_id`,`recommendation_id`,`priority`),
  KEY `fk_service_recommendation_items_rec` (`recommendation_id`),
  KEY `fk_service_recommendation_items_item` (`item_id`),
  CONSTRAINT `fk_service_recommendation_items_item` FOREIGN KEY (`item_id`) REFERENCES `items` (`item_id`),
  CONSTRAINT `fk_service_recommendation_items_rec` FOREIGN KEY (`recommendation_id`) REFERENCES `service_recommendations` (`recommendation_id`),
  CONSTRAINT `fk_service_recommendation_items_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `settings` (
  `setting_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `sgroup` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `skey` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `svalue` text COLLATE utf8mb4_unicode_ci,
  `created_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`setting_id`),
  KEY `ix_settings` (`tenant_id`,`sgroup`,`skey`),
  CONSTRAINT `fk_settings_0` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sms_account` (
  `account_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `sign` text COLLATE utf8mb4_unicode_ci,
  `balance` bigint(20) DEFAULT '0',
  `warn_qty` bigint(20) DEFAULT '0',
  `created_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`account_id`),
  KEY `ix_sms_account` (`tenant_id`),
  CONSTRAINT `fk_sms_account_0` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `sms_records` (
  `sms_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `store_id` bigint(20) DEFAULT NULL,
  `scene` text COLLATE utf8mb4_unicode_ci,
  `content` text COLLATE utf8mb4_unicode_ci,
  `recipients` bigint(20) DEFAULT NULL,
  `cost` bigint(20) DEFAULT NULL,
  `status` text COLLATE utf8mb4_unicode_ci,
  `created_at` text COLLATE utf8mb4_unicode_ci,
  `deleted_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`sms_id`),
  KEY `ix_sms_records` (`tenant_id`,`store_id`),
  KEY `fk_sms_records_0` (`store_id`),
  CONSTRAINT `fk_sms_records_0` FOREIGN KEY (`store_id`) REFERENCES `stores` (`store_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_sms_records_1` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `staff` (
  `staff_id` bigint(20) NOT NULL,
  `tenant_id` bigint(20) NOT NULL,
  `store_id` bigint(20) DEFAULT NULL,
  `name` text COLLATE utf8mb4_unicode_ci,
  `phone` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `role` text COLLATE utf8mb4_unicode_ci,
  `position` text COLLATE utf8mb4_unicode_ci,
  `department` text COLLATE utf8mb4_unicode_ci,
  `wx_notify` bigint(20) DEFAULT NULL,
  `status` text COLLATE utf8mb4_unicode_ci,
  `password_hash` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`staff_id`),
  KEY `ix_staff_login` (`phone`),
  KEY `ix_staff_tenant` (`tenant_id`,`store_id`),
  KEY `fk_staff_0` (`store_id`),
  CONSTRAINT `fk_staff_0` FOREIGN KEY (`store_id`) REFERENCES `stores` (`store_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_staff_1` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `staff_points` (
  `staff_id` bigint(20) NOT NULL,
  `tenant_id` bigint(20) NOT NULL,
  `points` bigint(20) NOT NULL DEFAULT '0',
  `version` bigint(20) NOT NULL DEFAULT '0',
  PRIMARY KEY (`staff_id`),
  KEY `fk_staff_points_1` (`tenant_id`),
  CONSTRAINT `fk_staff_points_0` FOREIGN KEY (`staff_id`) REFERENCES `staff` (`staff_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_staff_points_1` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `staff_point_ledger` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `staff_id` bigint(20) DEFAULT NULL,
  `delta` bigint(20) DEFAULT NULL,
  `balance_after` bigint(20) DEFAULT NULL,
  `reason` text COLLATE utf8mb4_unicode_ci,
  `ref_no` text COLLATE utf8mb4_unicode_ci,
  `created_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`id`),
  KEY `ix_staff_pledger` (`tenant_id`,`staff_id`),
  KEY `fk_staff_point_ledger_0` (`staff_id`),
  CONSTRAINT `fk_staff_point_ledger_0` FOREIGN KEY (`staff_id`) REFERENCES `staff` (`staff_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_staff_point_ledger_1` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `stocktakes` (
  `stocktake_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `store_id` bigint(20) NOT NULL,
  `stocktake_no` text COLLATE utf8mb4_unicode_ci,
  `status` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '盘点中',
  `note` text COLLATE utf8mb4_unicode_ci,
  `created_by` bigint(20) DEFAULT NULL,
  `committed_at` text COLLATE utf8mb4_unicode_ci,
  `version` bigint(20) NOT NULL DEFAULT '0',
  `created_at` text COLLATE utf8mb4_unicode_ci,
  `deleted_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`stocktake_id`),
  KEY `ix_stocktake` (`tenant_id`,`store_id`,`status`),
  KEY `fk_stocktakes_0` (`store_id`),
  CONSTRAINT `fk_stocktakes_0` FOREIGN KEY (`store_id`) REFERENCES `stores` (`store_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_stocktakes_1` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `stocktake_lines` (
  `line_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `stocktake_id` bigint(20) NOT NULL,
  `item_id` bigint(20) NOT NULL,
  `book_qty` bigint(20) NOT NULL DEFAULT '0',
  `counted_qty` bigint(20) DEFAULT NULL,
  `variance` bigint(20) DEFAULT NULL,
  `created_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`line_id`),
  KEY `ix_stocktake_line` (`tenant_id`,`stocktake_id`),
  KEY `fk_stocktake_lines_0` (`item_id`),
  KEY `fk_stocktake_lines_1` (`stocktake_id`),
  CONSTRAINT `fk_stocktake_lines_0` FOREIGN KEY (`item_id`) REFERENCES `items` (`item_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_stocktake_lines_1` FOREIGN KEY (`stocktake_id`) REFERENCES `stocktakes` (`stocktake_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_stocktake_lines_2` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `stock_movements` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `store_id` bigint(20) DEFAULT NULL,
  `item_id` bigint(20) DEFAULT NULL,
  `type` text COLLATE utf8mb4_unicode_ci,
  `qty` bigint(20) DEFAULT NULL,
  `ref` text COLLATE utf8mb4_unicode_ci,
  `created_at` text COLLATE utf8mb4_unicode_ci,
  `created_by` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`id`),
  KEY `ix_mov` (`tenant_id`,`item_id`),
  KEY `fk_stock_movements_0` (`item_id`),
  CONSTRAINT `fk_stock_movements_0` FOREIGN KEY (`item_id`) REFERENCES `items` (`item_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_stock_movements_1` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `stock_transfers` (
  `transfer_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `from_store` bigint(20) NOT NULL,
  `to_store` bigint(20) NOT NULL,
  `item_id` bigint(20) NOT NULL,
  `qty` decimal(20,4) NOT NULL,
  `status` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '待收货',
  `transfer_no` text COLLATE utf8mb4_unicode_ci,
  `note` text COLLATE utf8mb4_unicode_ci,
  `created_by` bigint(20) DEFAULT NULL,
  `received_at` text COLLATE utf8mb4_unicode_ci,
  `version` bigint(20) NOT NULL DEFAULT '0',
  `created_at` text COLLATE utf8mb4_unicode_ci,
  `deleted_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`transfer_id`),
  KEY `ix_transfer` (`tenant_id`,`status`),
  CONSTRAINT `fk_stock_transfers_0` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `stores` (
  `store_id` bigint(20) NOT NULL,
  `tenant_id` bigint(20) NOT NULL,
  `name` text COLLATE utf8mb4_unicode_ci,
  `manager` text COLLATE utf8mb4_unicode_ci,
  `phone` text COLLATE utf8mb4_unicode_ci,
  `address` text COLLATE utf8mb4_unicode_ci,
  `industry` text COLLATE utf8mb4_unicode_ci,
  `domain` text COLLATE utf8mb4_unicode_ci,
  `region` text COLLATE utf8mb4_unicode_ci,
  `status` text COLLATE utf8mb4_unicode_ci,
  `sort_weight` bigint(20) DEFAULT '0',
  `parent_store_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`store_id`),
  KEY `ix_stores_tenant` (`tenant_id`),
  CONSTRAINT `fk_stores_0` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `subscribe_messages` (
  `msg_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `customer_id` bigint(20) DEFAULT NULL,
  `template_key` text COLLATE utf8mb4_unicode_ci,
  `scene` text COLLATE utf8mb4_unicode_ci,
  `payload` text COLLATE utf8mb4_unicode_ci,
  `status` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '待发送',
  `provider` text COLLATE utf8mb4_unicode_ci,
  `provider_msg_id` text COLLATE utf8mb4_unicode_ci,
  `err` text COLLATE utf8mb4_unicode_ci,
  `created_at` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `sent_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`msg_id`),
  KEY `ix_submsg` (`tenant_id`,`status`,`created_at`),
  CONSTRAINT `fk_subscribe_messages_0` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `suppliers` (
  `supplier_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `name` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `contact` text COLLATE utf8mb4_unicode_ci,
  `phone` text COLLATE utf8mb4_unicode_ci,
  `address` text COLLATE utf8mb4_unicode_ci,
  `status` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '启用',
  `note` text COLLATE utf8mb4_unicode_ci,
  `created_at` text COLLATE utf8mb4_unicode_ci,
  `deleted_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`supplier_id`),
  KEY `ix_supplier` (`tenant_id`,`status`),
  CONSTRAINT `fk_suppliers_0` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `tags` (
  `customer_id` bigint(20) NOT NULL,
  `tags_json` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`customer_id`),
  CONSTRAINT `fk_tags_0` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `talk_scripts` (
  `script_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `scene` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `title` text COLLATE utf8mb4_unicode_ci,
  `content` text COLLATE utf8mb4_unicode_ci,
  `sort` bigint(20) DEFAULT '0',
  `status` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT '启用',
  `created_at` text COLLATE utf8mb4_unicode_ci,
  `deleted_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`script_id`),
  KEY `ix_scripts` (`tenant_id`,`scene`),
  CONSTRAINT `fk_talk_scripts_0` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `targets` (
  `target_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `store_id` bigint(20) DEFAULT NULL,
  `staff_id` bigint(20) DEFAULT NULL,
  `target_type` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `period_type` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `period` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `target_value` decimal(20,4) NOT NULL DEFAULT '0.0000',
  `created_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`target_id`),
  KEY `ix_targets` (`tenant_id`,`store_id`,`period`),
  CONSTRAINT `fk_targets_0` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `tenants` (
  `tenant_id` bigint(20) NOT NULL,
  `name` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '正常',
  `expires_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`tenant_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `transfers` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `customer_id` bigint(20) DEFAULT NULL,
  `from_store` bigint(20) DEFAULT NULL,
  `to_store` bigint(20) DEFAULT NULL,
  `time` text COLLATE utf8mb4_unicode_ci,
  `reason` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`id`),
  KEY `fk_transfers_0` (`customer_id`),
  CONSTRAINT `fk_transfers_0` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `wallet_ledger` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint(20) NOT NULL,
  `customer_id` bigint(20) DEFAULT NULL,
  `delta` decimal(20,4) DEFAULT NULL,
  `balance_after` decimal(20,4) DEFAULT NULL,
  `reason` text COLLATE utf8mb4_unicode_ci,
  `ref_order` text COLLATE utf8mb4_unicode_ci,
  `created_at` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`id`),
  KEY `ix_wledger` (`tenant_id`,`customer_id`),
  KEY `fk_wallet_ledger_0` (`customer_id`),
  CONSTRAINT `fk_wallet_ledger_0` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_wallet_ledger_1` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`tenant_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS=1;
