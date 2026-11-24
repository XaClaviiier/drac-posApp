-- POS Bengkel AC Mobil: DB-02, DRAF REVIEW, 2026-11-17.
-- Target dialect: MySQL 8.4 / InnoDB. Compatibility test: see database-review.md.
-- Canonical physical draft attached to BSD; not a production migration.
-- Import ONLY into a NEW EMPTY database explicitly selected by the operator.
-- No CREATE DATABASE, USE, DROP, TRUNCATE, credentials, dummy business data,
-- disabled foreign keys, IF NOT EXISTS, or CREATE OR REPLACE are included.
-- DDL causes implicit commits; do not import into an existing application schema.
-- UUIDs and timestamps must be supplied by the server; timestamps are UTC.
-- STRICT mode is required: validate original precision BEFORE decimal conversion.
-- Head revision pointers may be NULL only inside the bootstrap transaction.
-- History/revisions/ledgers are append-only by writer privileges, NOT by FK alone.
-- Roles, locks, full-saldo payment, approval, stock availability and transitions
-- require Laravel services/policies/transactions; DDL alone is not the application.
-- HPP automation, profit and payment gateway are intentionally not implemented.
SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;
SET SESSION time_zone = '+00:00';
SET SESSION sql_mode = 'STRICT_ALL_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';


-- Module: Access
CREATE TABLE users (
    id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    username VARCHAR(100) NOT NULL,
    name VARCHAR(200) NOT NULL,
    password VARCHAR(255) NOT NULL,
    remember_token VARCHAR(100) NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    version BIGINT UNSIGNED NOT NULL DEFAULT 1,
    created_at DATETIME(6) NOT NULL,
    updated_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (username),
    CONSTRAINT ck_users_3 CHECK (CHAR_LENGTH(TRIM(username)) > 0),
    CONSTRAINT ck_users_4 CHECK (CHAR_LENGTH(TRIM(name)) > 0),
    CONSTRAINT ck_users_5 CHECK (is_active IN (0,1)),
    CONSTRAINT ck_users_6 CHECK (version > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE roles (
    id BIGINT UNSIGNED AUTO_INCREMENT NOT NULL,
    name VARCHAR(125) NOT NULL,
    guard_name VARCHAR(125) NOT NULL,
    created_at DATETIME(6) NULL,
    updated_at DATETIME(6) NULL,
    PRIMARY KEY (id),
    UNIQUE (name, guard_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE permissions (
    id BIGINT UNSIGNED AUTO_INCREMENT NOT NULL,
    name VARCHAR(125) NOT NULL,
    guard_name VARCHAR(125) NOT NULL,
    created_at DATETIME(6) NULL,
    updated_at DATETIME(6) NULL,
    PRIMARY KEY (id),
    UNIQUE (name, guard_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE model_has_roles (
    role_id BIGINT UNSIGNED NOT NULL,
    model_type VARCHAR(125) NOT NULL,
    model_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    PRIMARY KEY (role_id, model_id, model_type),
    INDEX (model_id, model_type),
    CONSTRAINT fk_model_has_roles_3 FOREIGN KEY (role_id) REFERENCES roles (id) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE model_has_permissions (
    permission_id BIGINT UNSIGNED NOT NULL,
    model_type VARCHAR(125) NOT NULL,
    model_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    PRIMARY KEY (permission_id, model_id, model_type),
    INDEX (model_id, model_type),
    CONSTRAINT fk_model_has_permissions_3 FOREIGN KEY (permission_id) REFERENCES permissions (id) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE role_has_permissions (
    permission_id BIGINT UNSIGNED NOT NULL,
    role_id BIGINT UNSIGNED NOT NULL,
    PRIMARY KEY (permission_id, role_id),
    CONSTRAINT fk_role_has_permissions_2 FOREIGN KEY (permission_id) REFERENCES permissions (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_role_has_permissions_3 FOREIGN KEY (role_id) REFERENCES roles (id) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE personal_access_tokens (
    id BIGINT UNSIGNED AUTO_INCREMENT NOT NULL,
    tokenable_type VARCHAR(125) NOT NULL,
    tokenable_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    name TEXT NOT NULL,
    token CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    abilities TEXT NULL,
    last_used_at DATETIME(6) NULL,
    expires_at DATETIME(6) NULL,
    created_at DATETIME(6) NULL,
    updated_at DATETIME(6) NULL,
    PRIMARY KEY (id),
    UNIQUE (token),
    INDEX (tokenable_type, tokenable_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- Module: Visits
CREATE TABLE customers (
    id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    name VARCHAR(200) NOT NULL,
    phone VARCHAR(40) NOT NULL,
    address TEXT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    version BIGINT UNSIGNED NOT NULL DEFAULT 1,
    created_at DATETIME(6) NOT NULL,
    updated_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    INDEX (phone),
    INDEX (name),
    CONSTRAINT ck_customers_4 CHECK (CHAR_LENGTH(TRIM(name)) > 0),
    CONSTRAINT ck_customers_5 CHECK (CHAR_LENGTH(TRIM(phone)) > 0),
    CONSTRAINT ck_customers_6 CHECK (is_active IN (0,1)),
    CONSTRAINT ck_customers_7 CHECK (version > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE vehicles (
    id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    plate_normalized VARCHAR(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    version BIGINT UNSIGNED NOT NULL DEFAULT 1,
    created_at DATETIME(6) NOT NULL,
    updated_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (plate_normalized),
    CONSTRAINT ck_vehicles_3 CHECK (CHAR_LENGTH(plate_normalized) > 0 AND BINARY plate_normalized = BINARY UPPER(REPLACE(plate_normalized, ' ', ''))),
    CONSTRAINT ck_vehicles_4 CHECK (is_active IN (0,1)),
    CONSTRAINT ck_vehicles_5 CHECK (version > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE vehicle_plate_changes (
    id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    vehicle_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    vehicle_version BIGINT UNSIGNED NOT NULL,
    old_plate VARCHAR(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    new_plate VARCHAR(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    changed_by CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    actor_name_snapshot VARCHAR(200) NOT NULL,
    changed_at DATETIME(6) NOT NULL,
    reason TEXT NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (vehicle_id, vehicle_version),
    CONSTRAINT ck_vehicle_plate_changes_3 CHECK (vehicle_version > 1),
    CONSTRAINT ck_vehicle_plate_changes_4 CHECK (old_plate <> new_plate),
    CONSTRAINT ck_vehicle_plate_changes_5 CHECK (CHAR_LENGTH(TRIM(reason)) > 0),
    CONSTRAINT fk_vehicle_plate_changes_6 FOREIGN KEY (vehicle_id) REFERENCES vehicles (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_vehicle_plate_changes_7 FOREIGN KEY (changed_by) REFERENCES users (id) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE visit_registrations (
    id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    customer_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    vehicle_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    customer_name_snapshot VARCHAR(200) NOT NULL,
    phone_snapshot VARCHAR(40) NOT NULL,
    address_snapshot TEXT NULL,
    plate_snapshot VARCHAR(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    initial_complaint TEXT NOT NULL,
    registered_at DATETIME(6) NOT NULL,
    created_by CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    version BIGINT UNSIGNED NOT NULL DEFAULT 1,
    PRIMARY KEY (id),
    CONSTRAINT fk_visit_registrations_2 FOREIGN KEY (customer_id) REFERENCES customers (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_visit_registrations_3 FOREIGN KEY (vehicle_id) REFERENCES vehicles (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_visit_registrations_4 FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    INDEX (vehicle_id, registered_at),
    INDEX (customer_id, registered_at),
    CONSTRAINT ck_visit_registrations_7 CHECK (version > 0),
    CONSTRAINT ck_visit_registrations_8 CHECK (CHAR_LENGTH(TRIM(customer_name_snapshot)) > 0),
    CONSTRAINT ck_visit_registrations_9 CHECK (CHAR_LENGTH(TRIM(phone_snapshot)) > 0),
    CONSTRAINT ck_visit_registrations_10 CHECK (CHAR_LENGTH(TRIM(plate_snapshot)) > 0),
    CONSTRAINT ck_visit_registrations_11 CHECK (CHAR_LENGTH(TRIM(initial_complaint)) > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE registration_revisions (
    id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    registration_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    revision_no BIGINT UNSIGNED NOT NULL,
    customer_name_snapshot VARCHAR(200) NOT NULL,
    phone_snapshot VARCHAR(40) NOT NULL,
    address_snapshot TEXT NULL,
    plate_snapshot VARCHAR(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    initial_complaint TEXT NOT NULL,
    created_by CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    created_at DATETIME(6) NOT NULL,
    reason TEXT NULL,
    PRIMARY KEY (id),
    UNIQUE (registration_id, revision_no),
    CONSTRAINT fk_registration_revisions_3 FOREIGN KEY (registration_id) REFERENCES visit_registrations (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_registration_revisions_4 FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_registration_revisions_5 CHECK (revision_no > 0),
    CONSTRAINT ck_registration_revisions_6 CHECK (revision_no = 1 OR (reason IS NOT NULL AND CHAR_LENGTH(TRIM(reason)) > 0)),
    CONSTRAINT ck_registration_revisions_7 CHECK (CHAR_LENGTH(TRIM(customer_name_snapshot)) > 0),
    CONSTRAINT ck_registration_revisions_8 CHECK (CHAR_LENGTH(TRIM(phone_snapshot)) > 0),
    CONSTRAINT ck_registration_revisions_9 CHECK (CHAR_LENGTH(TRIM(plate_snapshot)) > 0),
    CONSTRAINT ck_registration_revisions_10 CHECK (CHAR_LENGTH(TRIM(initial_complaint)) > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- Module: Catalog
CREATE TABLE services (
    id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    code VARCHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT NULL,
    unit_code VARCHAR(20) NOT NULL,
    quantity_scale TINYINT UNSIGNED NOT NULL,
    selling_price DECIMAL(18,0) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    version BIGINT UNSIGNED NOT NULL DEFAULT 1,
    created_at DATETIME(6) NOT NULL,
    updated_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (code),
    CONSTRAINT ck_services_3 CHECK (selling_price >= 0),
    CONSTRAINT ck_services_4 CHECK (CHAR_LENGTH(TRIM(name)) > 0),
    CONSTRAINT ck_services_5 CHECK ((unit_code IN ('pcs','unit','job') AND quantity_scale = 0) OR (unit_code IN ('kg','liter','meter','hour') AND quantity_scale = 3)),
    CONSTRAINT ck_services_6 CHECK (is_active IN (0,1)),
    CONSTRAINT ck_services_7 CHECK (version > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE spare_parts (
    id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    code VARCHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT NULL,
    unit_code VARCHAR(20) NOT NULL,
    quantity_scale TINYINT UNSIGNED NOT NULL,
    selling_price DECIMAL(18,0) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    version BIGINT UNSIGNED NOT NULL DEFAULT 1,
    created_at DATETIME(6) NOT NULL,
    updated_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (code),
    CONSTRAINT ck_spare_parts_3 CHECK (selling_price >= 0),
    CONSTRAINT ck_spare_parts_4 CHECK (CHAR_LENGTH(TRIM(name)) > 0),
    CONSTRAINT ck_spare_parts_5 CHECK ((unit_code IN ('pcs','unit','job') AND quantity_scale = 0) OR (unit_code IN ('kg','liter','meter','hour') AND quantity_scale = 3)),
    CONSTRAINT ck_spare_parts_6 CHECK (is_active IN (0,1)),
    CONSTRAINT ck_spare_parts_7 CHECK (version > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- Module: Diagnosis
CREATE TABLE diagnosis_estimates (
    id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    registration_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    current_revision_no BIGINT UNSIGNED NULL,
    created_by CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    created_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (registration_id),
    UNIQUE (registration_id, id),
    CONSTRAINT fk_diagnosis_estimates_4 FOREIGN KEY (registration_id) REFERENCES visit_registrations (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_diagnosis_estimates_5 FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE diagnosis_estimate_revisions (
    id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    estimate_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    revision_no BIGINT UNSIGNED NOT NULL,
    findings TEXT NULL,
    recommended_action TEXT NULL,
    created_by CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    created_at DATETIME(6) NOT NULL,
    actor_name_snapshot VARCHAR(200) NOT NULL,
    actor_role_snapshot VARCHAR(20) NOT NULL,
    reason TEXT NULL,
    PRIMARY KEY (id),
    UNIQUE (estimate_id, revision_no),
    CONSTRAINT fk_diagnosis_estimate_revisions_3 FOREIGN KEY (estimate_id) REFERENCES diagnosis_estimates (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_diagnosis_estimate_revisions_4 FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_diagnosis_estimate_revisions_5 CHECK (revision_no > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE diagnosis_estimate_items (
    id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    estimate_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    service_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NULL,
    spare_part_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NULL,
    PRIMARY KEY (id),
    UNIQUE (estimate_id, id),
    CONSTRAINT fk_diagnosis_estimate_items_3 FOREIGN KEY (estimate_id) REFERENCES diagnosis_estimates (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_diagnosis_estimate_items_4 FOREIGN KEY (service_id) REFERENCES services (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_diagnosis_estimate_items_5 FOREIGN KEY (spare_part_id) REFERENCES spare_parts (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_diagnosis_estimate_items_6 CHECK ((service_id IS NULL) <> (spare_part_id IS NULL))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE diagnosis_estimate_revision_items (
    id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    estimate_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    revision_no BIGINT UNSIGNED NOT NULL,
    item_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    position INT UNSIGNED NOT NULL,
    name_snapshot VARCHAR(200) NOT NULL,
    unit_code VARCHAR(20) NOT NULL,
    quantity_scale TINYINT UNSIGNED NOT NULL,
    qty DECIMAL(15,3) NOT NULL,
    master_unit_price_snapshot DECIMAL(18,0) NOT NULL,
    unit_price DECIMAL(18,0) NOT NULL,
    subtotal_rupiah DECIMAL(30,0) NOT NULL,
    price_change_reason TEXT NULL,
    PRIMARY KEY (id),
    UNIQUE (estimate_id, revision_no, item_id),
    UNIQUE (estimate_id, revision_no, position),
    CONSTRAINT fk_diagnosis_estimate_revision_items_4 FOREIGN KEY (estimate_id, revision_no) REFERENCES diagnosis_estimate_revisions (estimate_id, revision_no) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_diagnosis_estimate_revision_items_5 FOREIGN KEY (estimate_id, item_id) REFERENCES diagnosis_estimate_items (estimate_id, id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_diagnosis_estimate_revision_items_6 CHECK (position > 0),
    CONSTRAINT ck_diagnosis_estimate_revision_items_7 CHECK (CHAR_LENGTH(TRIM(name_snapshot)) > 0),
    CONSTRAINT ck_diagnosis_estimate_revision_items_8 CHECK ((unit_code IN ('pcs','unit','job') AND quantity_scale = 0) OR (unit_code IN ('kg','liter','meter','hour') AND quantity_scale = 3)),
    CONSTRAINT ck_diagnosis_estimate_revision_items_9 CHECK (qty > 0 AND (quantity_scale = 3 OR qty = TRUNCATE(qty,0))),
    CONSTRAINT ck_diagnosis_estimate_revision_items_10 CHECK (master_unit_price_snapshot >= 0 AND unit_price >= 0 AND subtotal_rupiah >= 0),
    CONSTRAINT ck_diagnosis_estimate_revision_items_11 CHECK (subtotal_rupiah = ROUND(qty * unit_price,0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- Module: Service
CREATE TABLE service_orders (
    id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    registration_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    estimate_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    approved_estimate_revision_no BIGINT UNSIGNED NOT NULL,
    approval_recorded_by CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    approval_recorded_at DATETIME(6) NOT NULL,
    current_revision_no BIGINT UNSIGNED NULL,
    previous_service_order_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NULL,
    reference VARCHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    created_by CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    created_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (registration_id),
    UNIQUE (estimate_id),
    UNIQUE (reference),
    CONSTRAINT fk_service_orders_5 FOREIGN KEY (registration_id) REFERENCES visit_registrations (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_service_orders_6 FOREIGN KEY (registration_id, estimate_id) REFERENCES diagnosis_estimates (registration_id, id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_service_orders_7 FOREIGN KEY (estimate_id, approved_estimate_revision_no) REFERENCES diagnosis_estimate_revisions (estimate_id, revision_no) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_service_orders_8 FOREIGN KEY (approval_recorded_by) REFERENCES users (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_service_orders_9 FOREIGN KEY (previous_service_order_id) REFERENCES service_orders (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_service_orders_10 FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_service_orders_11 CHECK (previous_service_order_id IS NULL OR previous_service_order_id <> id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE service_order_revisions (
    id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    service_order_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    revision_no BIGINT UNSIGNED NOT NULL,
    status VARCHAR(24) NOT NULL,
    created_by CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    created_at DATETIME(6) NOT NULL,
    actor_name_snapshot VARCHAR(200) NOT NULL,
    actor_role_snapshot VARCHAR(20) NOT NULL,
    reason TEXT NULL,
    customer_approval_recorded_by CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NULL,
    customer_approval_recorded_at DATETIME(6) NULL,
    customer_approval_note TEXT NULL,
    PRIMARY KEY (id),
    UNIQUE (service_order_id, revision_no),
    CONSTRAINT fk_service_order_revisions_3 FOREIGN KEY (service_order_id) REFERENCES service_orders (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_service_order_revisions_4 FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_service_order_revisions_5 FOREIGN KEY (customer_approval_recorded_by) REFERENCES users (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_service_order_revisions_6 CHECK (revision_no > 0),
    CONSTRAINT ck_service_order_revisions_7 CHECK (status IN ('not_started','in_progress','paused','completed','cancelled')),
    CONSTRAINT ck_service_order_revisions_8 CHECK ((customer_approval_recorded_by IS NULL) = (customer_approval_recorded_at IS NULL))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE service_order_items (
    id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    service_order_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    source_estimate_item_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NULL,
    service_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NULL,
    spare_part_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NULL,
    PRIMARY KEY (id),
    UNIQUE (service_order_id, id),
    UNIQUE (id, spare_part_id),
    CONSTRAINT fk_service_order_items_4 FOREIGN KEY (service_order_id) REFERENCES service_orders (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_service_order_items_5 FOREIGN KEY (source_estimate_item_id) REFERENCES diagnosis_estimate_items (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_service_order_items_6 FOREIGN KEY (service_id) REFERENCES services (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_service_order_items_7 FOREIGN KEY (spare_part_id) REFERENCES spare_parts (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_service_order_items_8 CHECK ((service_id IS NULL) <> (spare_part_id IS NULL))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE service_order_revision_items (
    id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    service_order_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    revision_no BIGINT UNSIGNED NOT NULL,
    item_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    position INT UNSIGNED NOT NULL,
    name_snapshot VARCHAR(200) NOT NULL,
    unit_code VARCHAR(20) NOT NULL,
    quantity_scale TINYINT UNSIGNED NOT NULL,
    qty DECIMAL(15,3) NOT NULL,
    master_unit_price_snapshot DECIMAL(18,0) NOT NULL,
    unit_price DECIMAL(18,0) NOT NULL,
    subtotal_rupiah DECIMAL(30,0) NOT NULL,
    price_change_reason TEXT NULL,
    PRIMARY KEY (id),
    UNIQUE (service_order_id, revision_no, item_id),
    UNIQUE (service_order_id, revision_no, position),
    CONSTRAINT fk_service_order_revision_items_4 FOREIGN KEY (service_order_id, revision_no) REFERENCES service_order_revisions (service_order_id, revision_no) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_service_order_revision_items_5 FOREIGN KEY (service_order_id, item_id) REFERENCES service_order_items (service_order_id, id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_service_order_revision_items_6 CHECK (position > 0),
    CONSTRAINT ck_service_order_revision_items_7 CHECK (CHAR_LENGTH(TRIM(name_snapshot)) > 0),
    CONSTRAINT ck_service_order_revision_items_8 CHECK ((unit_code IN ('pcs','unit','job') AND quantity_scale = 0) OR (unit_code IN ('kg','liter','meter','hour') AND quantity_scale = 3)),
    CONSTRAINT ck_service_order_revision_items_9 CHECK (qty > 0 AND (quantity_scale = 3 OR qty = TRUNCATE(qty,0))),
    CONSTRAINT ck_service_order_revision_items_10 CHECK (master_unit_price_snapshot >= 0 AND unit_price >= 0 AND subtotal_rupiah >= 0),
    CONSTRAINT ck_service_order_revision_items_11 CHECK (subtotal_rupiah = ROUND(qty * unit_price,0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE service_order_revision_technicians (
    id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    service_order_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    revision_no BIGINT UNSIGNED NOT NULL,
    technician_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    technician_name_snapshot VARCHAR(200) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (service_order_id, revision_no, technician_id),
    CONSTRAINT fk_service_order_revision_technicians_3 FOREIGN KEY (service_order_id, revision_no) REFERENCES service_order_revisions (service_order_id, revision_no) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_service_order_revision_technicians_4 FOREIGN KEY (technician_id) REFERENCES users (id) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- Module: Billing
CREATE TABLE service_order_handoffs (
    id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    service_order_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    sequence_no BIGINT UNSIGNED NOT NULL,
    service_order_revision_no BIGINT UNSIGNED NOT NULL,
    event_type VARCHAR(16) NOT NULL,
    queued_handoff_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NULL,
    created_by CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    created_at DATETIME(6) NOT NULL,
    reason TEXT NULL,
    PRIMARY KEY (id),
    UNIQUE (service_order_id, sequence_no),
    UNIQUE (service_order_id, id),
    UNIQUE (queued_handoff_id),
    CONSTRAINT fk_service_order_handoffs_5 FOREIGN KEY (service_order_id, service_order_revision_no) REFERENCES service_order_revisions (service_order_id, revision_no) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_service_order_handoffs_6 FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_service_order_handoffs_7 CHECK (sequence_no > 0),
    CONSTRAINT ck_service_order_handoffs_8 CHECK ((event_type = 'queued' AND queued_handoff_id IS NULL) OR (event_type = 'withdrawn' AND queued_handoff_id IS NOT NULL AND reason IS NOT NULL AND CHAR_LENGTH(TRIM(reason)) > 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE invoices (
    id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    service_order_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    reference VARCHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    current_revision_no BIGINT UNSIGNED NULL,
    issued_revision_no BIGINT UNSIGNED NULL,
    created_by CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    created_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (service_order_id),
    UNIQUE (reference),
    UNIQUE (id, service_order_id),
    CONSTRAINT fk_invoices_5 FOREIGN KEY (service_order_id) REFERENCES service_orders (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_invoices_6 FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE invoice_revisions (
    id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    invoice_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    revision_no BIGINT UNSIGNED NOT NULL,
    service_order_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    handoff_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    registration_revision_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    event_type VARCHAR(20) NOT NULL,
    customer_name_snapshot VARCHAR(200) NOT NULL,
    phone_snapshot VARCHAR(40) NOT NULL,
    address_snapshot TEXT NULL,
    plate_snapshot VARCHAR(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    created_by CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    created_at DATETIME(6) NOT NULL,
    reason TEXT NULL,
    PRIMARY KEY (id),
    UNIQUE (invoice_id, revision_no),
    CONSTRAINT fk_invoice_revisions_3 FOREIGN KEY (invoice_id, service_order_id) REFERENCES invoices (id, service_order_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_invoice_revisions_4 FOREIGN KEY (service_order_id, handoff_id) REFERENCES service_order_handoffs (service_order_id, id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_invoice_revisions_5 FOREIGN KEY (registration_revision_id) REFERENCES registration_revisions (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_invoice_revisions_6 FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_invoice_revisions_7 CHECK (revision_no > 0),
    CONSTRAINT ck_invoice_revisions_8 CHECK (event_type IN ('created','price','rebased','issued','corrected')),
    CONSTRAINT ck_invoice_revisions_9 CHECK (event_type NOT IN ('price','rebased','corrected') OR (reason IS NOT NULL AND CHAR_LENGTH(TRIM(reason)) > 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE invoice_revision_items (
    id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    invoice_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    revision_no BIGINT UNSIGNED NOT NULL,
    service_order_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    service_order_item_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    spare_part_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NULL,
    service_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NULL,
    position INT UNSIGNED NOT NULL,
    name_snapshot VARCHAR(200) NOT NULL,
    unit_code VARCHAR(20) NOT NULL,
    quantity_scale TINYINT UNSIGNED NOT NULL,
    qty DECIMAL(15,3) NOT NULL,
    master_unit_price_snapshot DECIMAL(18,0) NOT NULL,
    unit_price DECIMAL(18,0) NOT NULL,
    subtotal_rupiah DECIMAL(30,0) NOT NULL,
    price_change_reason TEXT NULL,
    PRIMARY KEY (id),
    UNIQUE (invoice_id, revision_no, service_order_item_id),
    UNIQUE (invoice_id, revision_no, position),
    UNIQUE (invoice_id, id),
    UNIQUE (id, spare_part_id),
    CONSTRAINT fk_invoice_revision_items_6 FOREIGN KEY (invoice_id, revision_no) REFERENCES invoice_revisions (invoice_id, revision_no) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_invoice_revision_items_7 FOREIGN KEY (invoice_id, service_order_id) REFERENCES invoices (id, service_order_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_invoice_revision_items_8 FOREIGN KEY (service_order_id, service_order_item_id) REFERENCES service_order_items (service_order_id, id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_invoice_revision_items_9 FOREIGN KEY (service_order_item_id, spare_part_id) REFERENCES service_order_items (id, spare_part_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_invoice_revision_items_10 FOREIGN KEY (spare_part_id) REFERENCES spare_parts (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_invoice_revision_items_11 FOREIGN KEY (service_id) REFERENCES services (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_invoice_revision_items_12 CHECK ((service_id IS NULL) <> (spare_part_id IS NULL)),
    CONSTRAINT ck_invoice_revision_items_13 CHECK (position > 0),
    CONSTRAINT ck_invoice_revision_items_14 CHECK (CHAR_LENGTH(TRIM(name_snapshot)) > 0),
    CONSTRAINT ck_invoice_revision_items_15 CHECK ((unit_code IN ('pcs','unit','job') AND quantity_scale = 0) OR (unit_code IN ('kg','liter','meter','hour') AND quantity_scale = 3)),
    CONSTRAINT ck_invoice_revision_items_16 CHECK (qty > 0 AND (quantity_scale = 3 OR qty = TRUNCATE(qty,0))),
    CONSTRAINT ck_invoice_revision_items_17 CHECK (master_unit_price_snapshot >= 0 AND unit_price >= 0 AND subtotal_rupiah >= 0),
    CONSTRAINT ck_invoice_revision_items_18 CHECK (subtotal_rupiah = ROUND(qty * unit_price,0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE payment_destinations (
    id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    method VARCHAR(16) NOT NULL,
    label VARCHAR(200) NOT NULL,
    bank_name VARCHAR(200) NULL,
    account_number VARCHAR(100) NULL,
    account_holder VARCHAR(200) NULL,
    qris_asset_path VARCHAR(500) NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    version BIGINT UNSIGNED NOT NULL DEFAULT 1,
    created_at DATETIME(6) NOT NULL,
    updated_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT ck_payment_destinations_2 CHECK (method IN ('qris','transfer')),
    CONSTRAINT ck_payment_destinations_3 CHECK ((method = 'qris' AND qris_asset_path IS NOT NULL) OR (method = 'transfer' AND bank_name IS NOT NULL AND account_number IS NOT NULL AND account_holder IS NOT NULL)),
    CONSTRAINT ck_payment_destinations_4 CHECK (is_active IN (0,1)),
    CONSTRAINT ck_payment_destinations_5 CHECK (version > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE payments (
    id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    invoice_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    invoice_revision_no BIGINT UNSIGNED NOT NULL,
    method VARCHAR(16) NOT NULL,
    amount_rupiah DECIMAL(30,0) NOT NULL,
    received_rupiah DECIMAL(30,0) NOT NULL,
    payment_reference VARCHAR(200) NULL,
    payment_destination_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NULL,
    destination_snapshot JSON NULL,
    funds_verified_by CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NULL,
    funds_verified_at DATETIME(6) NULL,
    received_by CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    received_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (invoice_id, invoice_revision_no),
    UNIQUE (invoice_id, id),
    CONSTRAINT fk_payments_4 FOREIGN KEY (invoice_id, invoice_revision_no) REFERENCES invoice_revisions (invoice_id, revision_no) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_payments_5 FOREIGN KEY (payment_destination_id) REFERENCES payment_destinations (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_payments_6 FOREIGN KEY (funds_verified_by) REFERENCES users (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_payments_7 FOREIGN KEY (received_by) REFERENCES users (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_payments_8 CHECK (amount_rupiah > 0 AND received_rupiah >= amount_rupiah),
    CONSTRAINT ck_payments_9 CHECK (method IN ('cash','qris','transfer')),
    CONSTRAINT ck_payments_10 CHECK ((method = 'cash' AND funds_verified_by IS NULL AND funds_verified_at IS NULL) OR (method IN ('qris','transfer') AND funds_verified_by IS NOT NULL AND funds_verified_at IS NOT NULL AND received_rupiah = amount_rupiah AND payment_destination_id IS NOT NULL AND destination_snapshot IS NOT NULL)),
    CONSTRAINT ck_payments_11 CHECK (method <> 'transfer' OR (payment_reference IS NOT NULL AND CHAR_LENGTH(TRIM(payment_reference)) > 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- Module: Purchasing
CREATE TABLE suppliers (
    id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    name VARCHAR(200) NOT NULL,
    phone VARCHAR(40) NULL,
    address TEXT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    version BIGINT UNSIGNED NOT NULL DEFAULT 1,
    created_at DATETIME(6) NOT NULL,
    updated_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT ck_suppliers_2 CHECK (CHAR_LENGTH(TRIM(name)) > 0),
    CONSTRAINT ck_suppliers_3 CHECK (is_active IN (0,1)),
    CONSTRAINT ck_suppliers_4 CHECK (version > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE purchases (
    id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    supplier_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    reference VARCHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    supplier_document_reference VARCHAR(100) NULL,
    supplier_name_snapshot VARCHAR(200) NOT NULL,
    ordered_at DATETIME(6) NOT NULL,
    document_discount_rupiah DECIMAL(30,0) NOT NULL DEFAULT 0,
    confirmed_at DATETIME(6) NULL,
    confirmed_by CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NULL,
    version BIGINT UNSIGNED NOT NULL DEFAULT 1,
    created_by CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    created_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (reference),
    CONSTRAINT fk_purchases_3 FOREIGN KEY (supplier_id) REFERENCES suppliers (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_purchases_4 FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_purchases_5 FOREIGN KEY (confirmed_by) REFERENCES users (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_purchases_6 CHECK (document_discount_rupiah >= 0),
    CONSTRAINT ck_purchases_7 CHECK (version > 0),
    CONSTRAINT ck_purchases_8 CHECK ((confirmed_at IS NULL) = (confirmed_by IS NULL))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE purchase_items (
    id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    purchase_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    spare_part_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    position INT UNSIGNED NOT NULL,
    name_snapshot VARCHAR(200) NOT NULL,
    unit_code VARCHAR(20) NOT NULL,
    quantity_scale TINYINT UNSIGNED NOT NULL,
    qty DECIMAL(15,3) NOT NULL,
    unit_purchase_price DECIMAL(18,0) NOT NULL,
    line_discount_rupiah DECIMAL(30,0) NOT NULL DEFAULT 0,
    allocated_document_discount_rupiah DECIMAL(30,0) NOT NULL DEFAULT 0,
    net_amount_rupiah DECIMAL(30,0) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (purchase_id, id),
    UNIQUE (id, spare_part_id),
    UNIQUE (purchase_id, position),
    CONSTRAINT fk_purchase_items_5 FOREIGN KEY (purchase_id) REFERENCES purchases (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_purchase_items_6 FOREIGN KEY (spare_part_id) REFERENCES spare_parts (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_purchase_items_7 CHECK (position > 0),
    CONSTRAINT ck_purchase_items_8 CHECK ((unit_code IN ('pcs','unit','job') AND quantity_scale = 0) OR (unit_code IN ('kg','liter','meter','hour') AND quantity_scale = 3)),
    CONSTRAINT ck_purchase_items_9 CHECK (qty > 0 AND (quantity_scale = 3 OR qty = TRUNCATE(qty,0))),
    CONSTRAINT ck_purchase_items_10 CHECK (unit_purchase_price >= 0 AND line_discount_rupiah >= 0 AND allocated_document_discount_rupiah >= 0 AND net_amount_rupiah >= 0),
    CONSTRAINT ck_purchase_items_11 CHECK (net_amount_rupiah = ROUND(qty * unit_purchase_price,0) - line_discount_rupiah - allocated_document_discount_rupiah)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE goods_receipts (
    id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    purchase_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    reference VARCHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    received_at DATETIME(6) NOT NULL,
    received_by CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    note TEXT NULL,
    PRIMARY KEY (id),
    UNIQUE (reference),
    UNIQUE (purchase_id, id),
    CONSTRAINT fk_goods_receipts_4 FOREIGN KEY (purchase_id) REFERENCES purchases (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_goods_receipts_5 FOREIGN KEY (received_by) REFERENCES users (id) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE goods_receipt_items (
    id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    receipt_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    purchase_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    purchase_item_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    spare_part_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    qty DECIMAL(15,3) NOT NULL,
    net_unit_cost_snapshot DECIMAL(24,6) NOT NULL,
    net_amount_rupiah DECIMAL(30,0) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (receipt_id, purchase_item_id),
    UNIQUE (id, spare_part_id),
    CONSTRAINT fk_goods_receipt_items_4 FOREIGN KEY (purchase_id, receipt_id) REFERENCES goods_receipts (purchase_id, id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_goods_receipt_items_5 FOREIGN KEY (purchase_id, purchase_item_id) REFERENCES purchase_items (purchase_id, id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_goods_receipt_items_6 FOREIGN KEY (purchase_item_id, spare_part_id) REFERENCES purchase_items (id, spare_part_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_goods_receipt_items_7 CHECK (qty > 0),
    CONSTRAINT ck_goods_receipt_items_8 CHECK (net_unit_cost_snapshot >= 0 AND net_amount_rupiah >= 0),
    UNIQUE (purchase_id, id, spare_part_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE purchase_payments (
    id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    purchase_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    amount_rupiah DECIMAL(30,0) NOT NULL,
    method VARCHAR(16) NOT NULL,
    payment_reference VARCHAR(200) NULL,
    paid_by CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    paid_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (purchase_id),
    CONSTRAINT fk_purchase_payments_3 FOREIGN KEY (purchase_id) REFERENCES purchases (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_purchase_payments_4 FOREIGN KEY (paid_by) REFERENCES users (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_purchase_payments_5 CHECK (amount_rupiah > 0),
    CONSTRAINT ck_purchase_payments_6 CHECK (method IN ('cash','transfer'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- Module: SupplierReturns
CREATE TABLE supplier_returns (
    id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    purchase_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    reference VARCHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    settlement_type VARCHAR(20) NOT NULL,
    reason TEXT NOT NULL,
    handed_over_at DATETIME(6) NULL,
    handed_over_by CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NULL,
    credit_applied_at DATETIME(6) NULL,
    credit_applied_by CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NULL,
    created_by CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    created_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (reference),
    UNIQUE (purchase_id, id),
    CONSTRAINT fk_supplier_returns_4 FOREIGN KEY (purchase_id) REFERENCES purchases (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_supplier_returns_5 FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_supplier_returns_6 FOREIGN KEY (handed_over_by) REFERENCES users (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_supplier_returns_7 FOREIGN KEY (credit_applied_by) REFERENCES users (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_supplier_returns_8 CHECK (settlement_type IN ('replacement','debt_credit','cash_refund')),
    CONSTRAINT ck_supplier_returns_9 CHECK (CHAR_LENGTH(TRIM(reason)) > 0),
    CONSTRAINT ck_supplier_returns_10 CHECK ((handed_over_at IS NULL) = (handed_over_by IS NULL)),
    CONSTRAINT ck_supplier_returns_11 CHECK ((credit_applied_at IS NULL) = (credit_applied_by IS NULL)),
    CONSTRAINT ck_supplier_returns_12 CHECK (credit_applied_at IS NULL OR (settlement_type = 'debt_credit' AND handed_over_at IS NOT NULL))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE supplier_return_items (
    id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    supplier_return_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    purchase_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    receipt_item_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    spare_part_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    qty DECIMAL(15,3) NOT NULL,
    source_unit_cost_snapshot DECIMAL(24,6) NOT NULL,
    return_value_rupiah DECIMAL(30,0) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (supplier_return_id, receipt_item_id),
    UNIQUE (id, spare_part_id),
    CONSTRAINT fk_supplier_return_items_4 FOREIGN KEY (purchase_id, supplier_return_id) REFERENCES supplier_returns (purchase_id, id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_supplier_return_items_5 FOREIGN KEY (receipt_item_id, spare_part_id) REFERENCES goods_receipt_items (id, spare_part_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_supplier_return_items_6 CHECK (qty > 0),
    CONSTRAINT ck_supplier_return_items_7 CHECK (source_unit_cost_snapshot >= 0 AND return_value_rupiah >= 0),
    CONSTRAINT fk_supplier_return_items_8 FOREIGN KEY (purchase_id, receipt_item_id, spare_part_id) REFERENCES goods_receipt_items (purchase_id, id, spare_part_id) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE supplier_refund_receipts (
    id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    supplier_return_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    amount_rupiah DECIMAL(30,0) NOT NULL,
    received_by CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    received_at DATETIME(6) NOT NULL,
    payment_reference VARCHAR(200) NULL,
    PRIMARY KEY (id),
    CONSTRAINT fk_supplier_refund_receipts_2 FOREIGN KEY (supplier_return_id) REFERENCES supplier_returns (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_supplier_refund_receipts_3 FOREIGN KEY (received_by) REFERENCES users (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_supplier_refund_receipts_4 CHECK (amount_rupiah > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE replacement_receipts (
    id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    supplier_return_item_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    spare_part_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    qty DECIMAL(15,3) NOT NULL,
    received_by CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    received_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (id, spare_part_id),
    CONSTRAINT fk_replacement_receipts_3 FOREIGN KEY (supplier_return_item_id, spare_part_id) REFERENCES supplier_return_items (id, spare_part_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_replacement_receipts_4 FOREIGN KEY (received_by) REFERENCES users (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_replacement_receipts_5 CHECK (qty > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- Module: CustomerReturns
CREATE TABLE customer_returns (
    id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    invoice_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    reference VARCHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    reason TEXT NOT NULL,
    created_by CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    created_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (reference),
    UNIQUE (invoice_id, id),
    CONSTRAINT fk_customer_returns_4 FOREIGN KEY (invoice_id) REFERENCES invoices (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_customer_returns_5 FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_customer_returns_6 CHECK (CHAR_LENGTH(TRIM(reason)) > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE customer_return_items (
    id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    customer_return_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    invoice_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    invoice_revision_item_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    spare_part_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    qty DECIMAL(15,3) NOT NULL,
    received_at DATETIME(6) NOT NULL,
    received_by CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    inspection_result VARCHAR(16) NOT NULL DEFAULT 'pending',
    inspected_at DATETIME(6) NULL,
    inspected_by CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NULL,
    inspection_note TEXT NULL,
    PRIMARY KEY (id),
    UNIQUE (customer_return_id, invoice_revision_item_id),
    UNIQUE (id, spare_part_id),
    CONSTRAINT fk_customer_return_items_4 FOREIGN KEY (invoice_id, customer_return_id) REFERENCES customer_returns (invoice_id, id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_customer_return_items_5 FOREIGN KEY (invoice_id, invoice_revision_item_id) REFERENCES invoice_revision_items (invoice_id, id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_customer_return_items_6 FOREIGN KEY (invoice_revision_item_id, spare_part_id) REFERENCES invoice_revision_items (id, spare_part_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_customer_return_items_7 FOREIGN KEY (received_by) REFERENCES users (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_customer_return_items_8 FOREIGN KEY (inspected_by) REFERENCES users (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_customer_return_items_9 CHECK (qty > 0),
    CONSTRAINT ck_customer_return_items_10 CHECK (inspection_result IN ('pending','ready','damaged')),
    CONSTRAINT ck_customer_return_items_11 CHECK ((inspection_result = 'pending' AND inspected_at IS NULL AND inspected_by IS NULL) OR (inspection_result IN ('ready','damaged') AND inspected_at IS NOT NULL AND inspected_by IS NOT NULL))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE refund_authorizations (
    id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    invoice_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    customer_return_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NULL,
    approved_amount_rupiah DECIMAL(30,0) NOT NULL,
    reason TEXT NOT NULL,
    approved_by CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    approved_at DATETIME(6) NOT NULL,
    credit_note_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NULL,
    PRIMARY KEY (id),
    UNIQUE (invoice_id, id),
    CONSTRAINT fk_refund_authorizations_3 FOREIGN KEY (invoice_id) REFERENCES invoices (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_refund_authorizations_4 FOREIGN KEY (invoice_id, customer_return_id) REFERENCES customer_returns (invoice_id, id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_refund_authorizations_5 FOREIGN KEY (approved_by) REFERENCES users (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_refund_authorizations_6 CHECK (approved_amount_rupiah > 0),
    CONSTRAINT ck_refund_authorizations_7 CHECK (CHAR_LENGTH(TRIM(reason)) > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE customer_refunds (
    id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    invoice_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    authorization_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    amount_rupiah DECIMAL(30,0) NOT NULL,
    method VARCHAR(16) NOT NULL,
    payment_reference VARCHAR(200) NULL,
    paid_by CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    paid_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (authorization_id),
    CONSTRAINT fk_customer_refunds_3 FOREIGN KEY (invoice_id, authorization_id) REFERENCES refund_authorizations (invoice_id, id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_customer_refunds_4 FOREIGN KEY (paid_by) REFERENCES users (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_customer_refunds_5 CHECK (amount_rupiah > 0),
    CONSTRAINT ck_customer_refunds_6 CHECK (method IN ('cash','transfer'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- Module: Stock
CREATE TABLE stock_openings (
    id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    spare_part_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    qty DECIMAL(15,3) NOT NULL,
    damaged_qty DECIMAL(15,3) NOT NULL DEFAULT 0,
    initial_unit_cost DECIMAL(24,6) NULL,
    counted_at DATETIME(6) NOT NULL,
    created_by CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    created_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (spare_part_id),
    UNIQUE (id, spare_part_id),
    CONSTRAINT fk_stock_openings_4 FOREIGN KEY (spare_part_id) REFERENCES spare_parts (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_stock_openings_5 FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_stock_openings_6 CHECK (qty > 0 AND damaged_qty >= 0 AND damaged_qty <= qty),
    CONSTRAINT ck_stock_openings_7 CHECK (initial_unit_cost IS NULL OR initial_unit_cost >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE stock_reservation_events (
    id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    service_order_item_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    spare_part_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    sequence_no BIGINT UNSIGNED NOT NULL,
    qty DECIMAL(15,3) NOT NULL,
    state VARCHAR(16) NOT NULL,
    reason TEXT NOT NULL,
    created_by CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    created_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (service_order_item_id, sequence_no),
    CONSTRAINT fk_stock_reservation_events_3 FOREIGN KEY (service_order_item_id, spare_part_id) REFERENCES service_order_items (id, spare_part_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_stock_reservation_events_4 FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_stock_reservation_events_5 CHECK (sequence_no > 0),
    CONSTRAINT ck_stock_reservation_events_6 CHECK ((state = 'active' AND qty > 0) OR (state IN ('released','converted') AND qty = 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE stock_blocks (
    id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    spare_part_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    block_type VARCHAR(16) NOT NULL,
    source_receipt_item_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NULL,
    customer_return_item_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NULL,
    opening_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NULL,
    original_qty DECIMAL(15,3) NOT NULL,
    remaining_qty DECIMAL(15,3) NOT NULL,
    reason TEXT NOT NULL,
    version BIGINT UNSIGNED NOT NULL DEFAULT 1,
    created_by CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    created_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (id, spare_part_id),
    CONSTRAINT fk_stock_blocks_3 FOREIGN KEY (spare_part_id) REFERENCES spare_parts (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_stock_blocks_4 FOREIGN KEY (source_receipt_item_id, spare_part_id) REFERENCES goods_receipt_items (id, spare_part_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_stock_blocks_5 FOREIGN KEY (customer_return_item_id, spare_part_id) REFERENCES customer_return_items (id, spare_part_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_stock_blocks_6 FOREIGN KEY (opening_id, spare_part_id) REFERENCES stock_openings (id, spare_part_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_stock_blocks_7 FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_stock_blocks_8 CHECK (block_type IN ('damaged','quarantine')),
    CONSTRAINT ck_stock_blocks_9 CHECK (original_qty > 0 AND remaining_qty >= 0 AND remaining_qty <= original_qty),
    CONSTRAINT ck_stock_blocks_10 CHECK (version > 0),
    CONSTRAINT ck_stock_blocks_11 CHECK ((source_receipt_item_id IS NOT NULL) + (customer_return_item_id IS NOT NULL) + (opening_id IS NOT NULL) <= 1)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE stock_block_events (
    id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    stock_block_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    sequence_no BIGINT UNSIGNED NOT NULL,
    old_qty DECIMAL(15,3) NOT NULL,
    new_qty DECIMAL(15,3) NOT NULL,
    reason TEXT NOT NULL,
    created_by CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    created_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (stock_block_id, sequence_no),
    CONSTRAINT fk_stock_block_events_3 FOREIGN KEY (stock_block_id) REFERENCES stock_blocks (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_stock_block_events_4 FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_stock_block_events_5 CHECK (sequence_no > 0 AND old_qty >= 0 AND new_qty >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE stock_movements (
    id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    spare_part_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    movement_type VARCHAR(24) NOT NULL,
    qty_delta DECIMAL(15,3) NOT NULL,
    opening_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NULL,
    receipt_item_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NULL,
    invoice_revision_item_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NULL,
    supplier_return_item_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NULL,
    replacement_receipt_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NULL,
    customer_return_item_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NULL,
    created_by CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    created_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT fk_stock_movements_2 FOREIGN KEY (spare_part_id) REFERENCES spare_parts (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_stock_movements_3 FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_stock_movements_4 CHECK (qty_delta <> 0),
    CONSTRAINT ck_stock_movements_5 CHECK ((opening_id IS NOT NULL) + (receipt_item_id IS NOT NULL) + (invoice_revision_item_id IS NOT NULL) + (supplier_return_item_id IS NOT NULL) + (replacement_receipt_id IS NOT NULL) + (customer_return_item_id IS NOT NULL) = 1),
    UNIQUE (opening_id),
    CONSTRAINT fk_stock_movements_7 FOREIGN KEY (opening_id, spare_part_id) REFERENCES stock_openings (id, spare_part_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    UNIQUE (receipt_item_id),
    CONSTRAINT fk_stock_movements_9 FOREIGN KEY (receipt_item_id, spare_part_id) REFERENCES goods_receipt_items (id, spare_part_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    UNIQUE (invoice_revision_item_id),
    CONSTRAINT fk_stock_movements_11 FOREIGN KEY (invoice_revision_item_id, spare_part_id) REFERENCES invoice_revision_items (id, spare_part_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    UNIQUE (supplier_return_item_id),
    CONSTRAINT fk_stock_movements_13 FOREIGN KEY (supplier_return_item_id, spare_part_id) REFERENCES supplier_return_items (id, spare_part_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    UNIQUE (replacement_receipt_id),
    CONSTRAINT fk_stock_movements_15 FOREIGN KEY (replacement_receipt_id, spare_part_id) REFERENCES replacement_receipts (id, spare_part_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    UNIQUE (customer_return_item_id),
    CONSTRAINT fk_stock_movements_17 FOREIGN KEY (customer_return_item_id, spare_part_id) REFERENCES customer_return_items (id, spare_part_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_stock_movements_18 CHECK ((movement_type = 'opening' AND opening_id IS NOT NULL AND qty_delta > 0) OR (movement_type = 'purchase_in' AND receipt_item_id IS NOT NULL AND qty_delta > 0) OR (movement_type = 'invoice_out' AND invoice_revision_item_id IS NOT NULL AND qty_delta < 0) OR (movement_type = 'supplier_return_out' AND supplier_return_item_id IS NOT NULL AND qty_delta < 0) OR (movement_type = 'replacement_in' AND replacement_receipt_id IS NOT NULL AND qty_delta > 0) OR (movement_type = 'customer_return_in' AND customer_return_item_id IS NOT NULL AND qty_delta > 0)),
    INDEX (spare_part_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- Module: Operations
CREATE TABLE expenses (
    id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    reference VARCHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    category VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    amount_rupiah DECIMAL(30,0) NOT NULL,
    purchase_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NULL,
    paid_by CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    paid_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (reference),
    CONSTRAINT fk_expenses_3 FOREIGN KEY (purchase_id) REFERENCES purchases (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_expenses_4 FOREIGN KEY (paid_by) REFERENCES users (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_expenses_5 CHECK (amount_rupiah > 0),
    CONSTRAINT ck_expenses_6 CHECK (CHAR_LENGTH(TRIM(description)) > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE audit_logs (
    id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    actor_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    actor_name_snapshot VARCHAR(200) NOT NULL,
    actor_role_snapshot VARCHAR(20) NOT NULL,
    action VARCHAR(100) NOT NULL,
    subject_type VARCHAR(100) NOT NULL,
    subject_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    old_values JSON NULL,
    new_values JSON NULL,
    reason TEXT NULL,
    occurred_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT fk_audit_logs_2 FOREIGN KEY (actor_id) REFERENCES users (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    INDEX (subject_type, subject_id, occurred_at),
    INDEX (actor_id, occurred_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE idempotency_requests (
    id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    actor_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    operation VARCHAR(100) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    idempotency_key VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    request_hash CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    state VARCHAR(16) NOT NULL,
    response_status SMALLINT UNSIGNED NULL,
    response_body JSON NULL,
    created_at DATETIME(6) NOT NULL,
    completed_at DATETIME(6) NULL,
    PRIMARY KEY (id),
    UNIQUE (actor_id, operation, idempotency_key),
    CONSTRAINT fk_idempotency_requests_3 FOREIGN KEY (actor_id) REFERENCES users (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_idempotency_requests_4 CHECK ((state = 'processing' AND completed_at IS NULL AND response_status IS NULL AND response_body IS NULL) OR (state = 'completed' AND completed_at IS NOT NULL AND response_status IS NOT NULL AND response_status BETWEEN 200 AND 599 AND response_body IS NOT NULL))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE document_counters (
    document_type VARCHAR(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    period_key VARCHAR(20) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    last_number BIGINT UNSIGNED NOT NULL,
    PRIMARY KEY (document_type, period_key),
    CONSTRAINT ck_document_counters_2 CHECK (last_number > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- Module: CustomerReturns
CREATE TABLE invoice_credit_notes (
    id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    invoice_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    invoice_revision_no BIGINT UNSIGNED NOT NULL,
    customer_return_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NULL,
    amount_rupiah DECIMAL(30,0) NOT NULL,
    reason TEXT NOT NULL,
    approved_by CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    approved_at DATETIME(6) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (invoice_id, id),
    CONSTRAINT fk_invoice_credit_notes_3 FOREIGN KEY (invoice_id, invoice_revision_no) REFERENCES invoice_revisions (invoice_id, revision_no) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_invoice_credit_notes_4 FOREIGN KEY (invoice_id, customer_return_id) REFERENCES customer_returns (invoice_id, id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_invoice_credit_notes_5 FOREIGN KEY (approved_by) REFERENCES users (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_invoice_credit_notes_6 CHECK (amount_rupiah > 0),
    CONSTRAINT ck_invoice_credit_notes_7 CHECK (CHAR_LENGTH(TRIM(reason)) > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

ALTER TABLE diagnosis_estimates
    ADD CONSTRAINT fk_late_1 FOREIGN KEY (id, current_revision_no) REFERENCES diagnosis_estimate_revisions (estimate_id, revision_no) ON DELETE RESTRICT ON UPDATE RESTRICT;
ALTER TABLE service_orders
    ADD CONSTRAINT fk_late_2 FOREIGN KEY (id, current_revision_no) REFERENCES service_order_revisions (service_order_id, revision_no) ON DELETE RESTRICT ON UPDATE RESTRICT;
ALTER TABLE service_order_handoffs
    ADD CONSTRAINT fk_late_3 FOREIGN KEY (service_order_id, queued_handoff_id) REFERENCES service_order_handoffs (service_order_id, id) ON DELETE RESTRICT ON UPDATE RESTRICT;
ALTER TABLE invoices
    ADD CONSTRAINT fk_late_4 FOREIGN KEY (id, current_revision_no) REFERENCES invoice_revisions (invoice_id, revision_no) ON DELETE RESTRICT ON UPDATE RESTRICT;
ALTER TABLE invoices
    ADD CONSTRAINT fk_late_5 FOREIGN KEY (id, issued_revision_no) REFERENCES invoice_revisions (invoice_id, revision_no) ON DELETE RESTRICT ON UPDATE RESTRICT;
ALTER TABLE refund_authorizations
    ADD CONSTRAINT fk_late_6 FOREIGN KEY (invoice_id, credit_note_id) REFERENCES invoice_credit_notes (invoice_id, id) ON DELETE RESTRICT ON UPDATE RESTRICT;

-- Read models: no mutable totals or second source of financial/stock truth.
-- These views are NOT an authorization boundary. Restrict access in Laravel.
CREATE VIEW v_current_stock_reservations AS
SELECT e.* FROM stock_reservation_events e
JOIN (SELECT service_order_item_id, MAX(sequence_no) AS sequence_no
      FROM stock_reservation_events GROUP BY service_order_item_id) latest
  ON latest.service_order_item_id = e.service_order_item_id
 AND latest.sequence_no = e.sequence_no;

CREATE VIEW v_stock_quantities AS
SELECT p.id AS spare_part_id,
       COALESCE(m.on_hand_qty,0) AS on_hand_qty,
       COALESCE(r.reserved_qty,0) AS reserved_qty,
       COALESCE(b.blocked_qty,0) AS blocked_qty,
       COALESCE(m.on_hand_qty,0) - COALESCE(r.reserved_qty,0)
         - COALESCE(b.blocked_qty,0) AS available_qty
FROM spare_parts p
LEFT JOIN (SELECT spare_part_id, SUM(qty_delta) AS on_hand_qty
           FROM stock_movements GROUP BY spare_part_id) m ON m.spare_part_id = p.id
LEFT JOIN (SELECT spare_part_id, SUM(qty) AS reserved_qty
           FROM v_current_stock_reservations WHERE state = 'active'
           GROUP BY spare_part_id) r ON r.spare_part_id = p.id
LEFT JOIN (SELECT spare_part_id, SUM(remaining_qty) AS blocked_qty
           FROM stock_blocks GROUP BY spare_part_id) b ON b.spare_part_id = p.id;

CREATE VIEW v_invoice_balances AS
SELECT i.id AS invoice_id, i.issued_revision_no,
       COALESCE(t.total_rupiah,0) AS total_rupiah,
       COALESCE(c.credit_rupiah,0) AS credit_rupiah,
       COALESCE(p.paid_rupiah,0) AS paid_rupiah,
       COALESCE(r.refunded_rupiah,0) AS refunded_rupiah,
       GREATEST(COALESCE(t.total_rupiah,0) - COALESCE(c.credit_rupiah,0)
         - COALESCE(p.paid_rupiah,0) + COALESCE(r.refunded_rupiah,0),0) AS outstanding_rupiah,
       GREATEST(COALESCE(p.paid_rupiah,0) - COALESCE(r.refunded_rupiah,0)
         - COALESCE(t.total_rupiah,0) + COALESCE(c.credit_rupiah,0),0) AS overpaid_rupiah,
       CASE WHEN i.issued_revision_no IS NULL THEN 'draft'
            WHEN COALESCE(t.total_rupiah,0) - COALESCE(c.credit_rupiah,0)
               - COALESCE(p.paid_rupiah,0) + COALESCE(r.refunded_rupiah,0) > 0
            THEN 'unpaid' ELSE 'paid' END AS payment_status
FROM invoices i
LEFT JOIN (SELECT invoice_id, revision_no, SUM(subtotal_rupiah) AS total_rupiah
           FROM invoice_revision_items GROUP BY invoice_id, revision_no) t
 ON t.invoice_id = i.id AND t.revision_no = i.current_revision_no
LEFT JOIN (SELECT invoice_id, SUM(amount_rupiah) AS paid_rupiah
           FROM payments GROUP BY invoice_id) p ON p.invoice_id = i.id
LEFT JOIN (SELECT invoice_id, SUM(amount_rupiah) AS refunded_rupiah
           FROM customer_refunds GROUP BY invoice_id) r ON r.invoice_id = i.id
LEFT JOIN (SELECT invoice_id, SUM(amount_rupiah) AS credit_rupiah
           FROM invoice_credit_notes GROUP BY invoice_id) c ON c.invoice_id = i.id;

CREATE VIEW v_supplier_balances AS
SELECT p.id AS purchase_id, p.supplier_id,
       COALESCE(t.total_rupiah,0) AS total_rupiah,
       COALESCE(c.credited_rupiah,0) AS credited_rupiah,
       COALESCE(m.amount_rupiah,0) AS paid_rupiah,
       GREATEST(COALESCE(t.total_rupiah,0) - COALESCE(c.credited_rupiah,0)
         - COALESCE(m.amount_rupiah,0),0) AS outstanding_rupiah
FROM purchases p
LEFT JOIN (SELECT purchase_id, SUM(net_amount_rupiah) AS total_rupiah
           FROM purchase_items GROUP BY purchase_id) t ON t.purchase_id = p.id
LEFT JOIN purchase_payments m ON m.purchase_id = p.id
LEFT JOIN (SELECT r.purchase_id, SUM(l.return_value_rupiah) AS credited_rupiah
           FROM supplier_returns r JOIN supplier_return_items l ON l.supplier_return_id = r.id
           WHERE r.settlement_type = 'debt_credit' AND r.credit_applied_at IS NOT NULL
           GROUP BY r.purchase_id) c ON c.purchase_id = p.id;

-- Seed only fixed application roles. No user/password or dummy prices.
INSERT INTO roles (name, guard_name) VALUES ('Owner','web'), ('Teknisi','web'), ('Kasir','web');
