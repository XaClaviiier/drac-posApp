# ERD database POS — DB-02 (draf review)

Sumber fisik: [pos-schema.sql](pos-schema.sql). Status, keputusan teknis dan batas
penegakan: [database-review.md](database-review.md). Draf seluruh sistem, bukan
skema produksi yang telah disahkan. Tidak ada relasi kepemilikan permanen antara
pelanggan dan kendaraan; hubungan berasal dari kunjungan.

Diagram dipisah per modul agar terbaca. Atribut lengkap hanya ditampilkan pada
modul pemilik tabel; entitas luar muncul sebagai referensi. Semua FK fisik,
termasuk FK komposit dan pointer revisi, ditampilkan. Label relasi menyebut kolom
anak. Kardinalitas diturunkan dari nullability dan kunci unik SQL, bukan jaminan
jumlah minimum baris lintas tabel. Minimum satu revisi/Teknisi tertentu tetap
invariant transaksi server. Relasi polimorfik paket dan audit tidak memiliki FK
fisik; jangan menganggapnya telah ditegakkan database.

## Access

```mermaid
erDiagram
    users {
        char(36) id PK "NOT NULL"
        varchar(100) username UK "NOT NULL; UK may be composite"
        varchar(200) name "NOT NULL"
        varchar(255) password "NOT NULL"
        varchar(100) remember_token "NULL"
        boolean is_active "NOT NULL"
        bigint version "NOT NULL"
        datetime(6) created_at "NOT NULL"
        datetime(6) updated_at "NOT NULL"
    }
    roles {
        bigint id PK "NOT NULL"
        varchar(125) name UK "NOT NULL; UK may be composite"
        varchar(125) guard_name UK "NOT NULL; UK may be composite"
        datetime(6) created_at "NULL"
        datetime(6) updated_at "NULL"
    }
    permissions {
        bigint id PK "NOT NULL"
        varchar(125) name UK "NOT NULL; UK may be composite"
        varchar(125) guard_name UK "NOT NULL; UK may be composite"
        datetime(6) created_at "NULL"
        datetime(6) updated_at "NULL"
    }
    model_has_roles {
        bigint role_id PK,FK "NOT NULL"
        varchar(125) model_type PK "NOT NULL"
        char(36) model_id PK "NOT NULL"
    }
    model_has_permissions {
        bigint permission_id PK,FK "NOT NULL"
        varchar(125) model_type PK "NOT NULL"
        char(36) model_id PK "NOT NULL"
    }
    role_has_permissions {
        bigint permission_id PK,FK "NOT NULL"
        bigint role_id PK,FK "NOT NULL"
    }
    personal_access_tokens {
        bigint id PK "NOT NULL"
        varchar(125) tokenable_type "NOT NULL"
        char(36) tokenable_id "NOT NULL"
        text name "NOT NULL"
        char(64) token UK "NOT NULL; UK may be composite"
        text abilities "NULL"
        datetime(6) last_used_at "NULL"
        datetime(6) expires_at "NULL"
        datetime(6) created_at "NULL"
        datetime(6) updated_at "NULL"
    }
    roles ||--o{ model_has_roles : "role_id"
    permissions ||--o{ model_has_permissions : "permission_id"
    permissions ||--o{ role_has_permissions : "permission_id"
    roles ||--o{ role_has_permissions : "role_id"
```

## Visits

```mermaid
erDiagram
    customers {
        char(36) id PK "NOT NULL"
        varchar(200) name "NOT NULL"
        varchar(40) phone "NOT NULL"
        text address "NULL"
        boolean is_active "NOT NULL"
        bigint version "NOT NULL"
        datetime(6) created_at "NOT NULL"
        datetime(6) updated_at "NOT NULL"
    }
    vehicles {
        char(36) id PK "NOT NULL"
        varchar(32) plate_normalized UK "NOT NULL; UK may be composite"
        boolean is_active "NOT NULL"
        bigint version "NOT NULL"
        datetime(6) created_at "NOT NULL"
        datetime(6) updated_at "NOT NULL"
    }
    vehicle_plate_changes {
        char(36) id PK "NOT NULL"
        char(36) vehicle_id FK,UK "NOT NULL; UK may be composite"
        bigint vehicle_version UK "NOT NULL; UK may be composite"
        varchar(32) old_plate "NOT NULL"
        varchar(32) new_plate "NOT NULL"
        char(36) changed_by FK "NOT NULL"
        varchar(200) actor_name_snapshot "NOT NULL"
        datetime(6) changed_at "NOT NULL"
        text reason "NOT NULL"
    }
    visit_registrations {
        char(36) id PK "NOT NULL"
        char(36) customer_id FK "NOT NULL"
        char(36) vehicle_id FK "NOT NULL"
        varchar(200) customer_name_snapshot "NOT NULL"
        varchar(40) phone_snapshot "NOT NULL"
        text address_snapshot "NULL"
        varchar(32) plate_snapshot "NOT NULL"
        text initial_complaint "NOT NULL"
        datetime(6) registered_at "NOT NULL"
        char(36) created_by FK "NOT NULL"
        bigint version "NOT NULL"
    }
    registration_revisions {
        char(36) id PK "NOT NULL"
        char(36) registration_id FK,UK "NOT NULL; UK may be composite"
        bigint revision_no UK "NOT NULL; UK may be composite"
        varchar(200) customer_name_snapshot "NOT NULL"
        varchar(40) phone_snapshot "NOT NULL"
        text address_snapshot "NULL"
        varchar(32) plate_snapshot "NOT NULL"
        text initial_complaint "NOT NULL"
        char(36) created_by FK "NOT NULL"
        datetime(6) created_at "NOT NULL"
        text reason "NULL"
    }
    vehicles ||--o{ vehicle_plate_changes : "vehicle_id"
    users ||--o{ vehicle_plate_changes : "changed_by"
    customers ||--o{ visit_registrations : "customer_id"
    vehicles ||--o{ visit_registrations : "vehicle_id"
    users ||--o{ visit_registrations : "created_by"
    visit_registrations ||--o{ registration_revisions : "registration_id"
    users ||--o{ registration_revisions : "created_by"
```

## Catalog

```mermaid
erDiagram
    services {
        char(36) id PK "NOT NULL"
        varchar(64) code UK "NOT NULL; UK may be composite"
        varchar(200) name "NOT NULL"
        text description "NULL"
        varchar(20) unit_code "NOT NULL"
        tinyint quantity_scale "NOT NULL"
        decimal(18_0) selling_price "NOT NULL"
        boolean is_active "NOT NULL"
        bigint version "NOT NULL"
        datetime(6) created_at "NOT NULL"
        datetime(6) updated_at "NOT NULL"
    }
    spare_parts {
        char(36) id PK "NOT NULL"
        varchar(64) code UK "NOT NULL; UK may be composite"
        varchar(200) name "NOT NULL"
        text description "NULL"
        varchar(20) unit_code "NOT NULL"
        tinyint quantity_scale "NOT NULL"
        decimal(18_0) selling_price "NOT NULL"
        boolean is_active "NOT NULL"
        bigint version "NOT NULL"
        datetime(6) created_at "NOT NULL"
        datetime(6) updated_at "NOT NULL"
    }
```

## Diagnosis

```mermaid
erDiagram
    diagnosis_estimates {
        char(36) id PK,FK,UK "NOT NULL; UK may be composite"
        char(36) registration_id FK,UK "NOT NULL; UK may be composite"
        bigint current_revision_no FK "NULL"
        char(36) created_by FK "NOT NULL"
        datetime(6) created_at "NOT NULL"
    }
    diagnosis_estimate_revisions {
        char(36) id PK "NOT NULL"
        char(36) estimate_id FK,UK "NOT NULL; UK may be composite"
        bigint revision_no UK "NOT NULL; UK may be composite"
        text findings "NULL"
        text recommended_action "NULL"
        char(36) created_by FK "NOT NULL"
        datetime(6) created_at "NOT NULL"
        varchar(200) actor_name_snapshot "NOT NULL"
        varchar(20) actor_role_snapshot "NOT NULL"
        text reason "NULL"
    }
    diagnosis_estimate_items {
        char(36) id PK,UK "NOT NULL; UK may be composite"
        char(36) estimate_id FK,UK "NOT NULL; UK may be composite"
        char(36) service_id FK "NULL"
        char(36) spare_part_id FK "NULL"
    }
    diagnosis_estimate_revision_items {
        char(36) id PK "NOT NULL"
        char(36) estimate_id FK,UK "NOT NULL; UK may be composite"
        bigint revision_no FK,UK "NOT NULL; UK may be composite"
        char(36) item_id FK,UK "NOT NULL; UK may be composite"
        int position UK "NOT NULL; UK may be composite"
        varchar(200) name_snapshot "NOT NULL"
        varchar(20) unit_code "NOT NULL"
        tinyint quantity_scale "NOT NULL"
        decimal(15_3) qty "NOT NULL"
        decimal(18_0) master_unit_price_snapshot "NOT NULL"
        decimal(18_0) unit_price "NOT NULL"
        decimal(30_0) subtotal_rupiah "NOT NULL"
        text price_change_reason "NULL"
    }
    visit_registrations ||--o| diagnosis_estimates : "registration_id"
    users ||--o{ diagnosis_estimates : "created_by"
    diagnosis_estimates ||--o{ diagnosis_estimate_revisions : "estimate_id"
    users ||--o{ diagnosis_estimate_revisions : "created_by"
    diagnosis_estimates ||--o{ diagnosis_estimate_items : "estimate_id"
    services |o--o{ diagnosis_estimate_items : "service_id"
    spare_parts |o--o{ diagnosis_estimate_items : "spare_part_id"
    diagnosis_estimate_revisions ||--o{ diagnosis_estimate_revision_items : "estimate_id, revision_no"
    diagnosis_estimate_items ||--o{ diagnosis_estimate_revision_items : "estimate_id, item_id"
    diagnosis_estimate_revisions |o--o| diagnosis_estimates : "id, current_revision_no"
```

## Service

```mermaid
erDiagram
    service_orders {
        char(36) id PK,FK "NOT NULL"
        char(36) registration_id FK,UK "NOT NULL; UK may be composite"
        char(36) estimate_id FK,UK "NOT NULL; UK may be composite"
        bigint approved_estimate_revision_no FK "NOT NULL"
        char(36) approval_recorded_by FK "NOT NULL"
        datetime(6) approval_recorded_at "NOT NULL"
        bigint current_revision_no FK "NULL"
        char(36) previous_service_order_id FK "NULL"
        varchar(64) reference UK "NOT NULL; UK may be composite"
        char(36) created_by FK "NOT NULL"
        datetime(6) created_at "NOT NULL"
    }
    service_order_revisions {
        char(36) id PK "NOT NULL"
        char(36) service_order_id FK,UK "NOT NULL; UK may be composite"
        bigint revision_no UK "NOT NULL; UK may be composite"
        varchar(24) status "NOT NULL"
        char(36) created_by FK "NOT NULL"
        datetime(6) created_at "NOT NULL"
        varchar(200) actor_name_snapshot "NOT NULL"
        varchar(20) actor_role_snapshot "NOT NULL"
        text reason "NULL"
        char(36) customer_approval_recorded_by FK "NULL"
        datetime(6) customer_approval_recorded_at "NULL"
        text customer_approval_note "NULL"
    }
    service_order_items {
        char(36) id PK,UK "NOT NULL; UK may be composite"
        char(36) service_order_id FK,UK "NOT NULL; UK may be composite"
        char(36) source_estimate_item_id FK "NULL"
        char(36) service_id FK "NULL"
        char(36) spare_part_id FK,UK "NULL; UK may be composite"
    }
    service_order_revision_items {
        char(36) id PK "NOT NULL"
        char(36) service_order_id FK,UK "NOT NULL; UK may be composite"
        bigint revision_no FK,UK "NOT NULL; UK may be composite"
        char(36) item_id FK,UK "NOT NULL; UK may be composite"
        int position UK "NOT NULL; UK may be composite"
        varchar(200) name_snapshot "NOT NULL"
        varchar(20) unit_code "NOT NULL"
        tinyint quantity_scale "NOT NULL"
        decimal(15_3) qty "NOT NULL"
        decimal(18_0) master_unit_price_snapshot "NOT NULL"
        decimal(18_0) unit_price "NOT NULL"
        decimal(30_0) subtotal_rupiah "NOT NULL"
        text price_change_reason "NULL"
    }
    service_order_revision_technicians {
        char(36) id PK "NOT NULL"
        char(36) service_order_id FK,UK "NOT NULL; UK may be composite"
        bigint revision_no FK,UK "NOT NULL; UK may be composite"
        char(36) technician_id FK,UK "NOT NULL; UK may be composite"
        varchar(200) technician_name_snapshot "NOT NULL"
    }
    visit_registrations ||--o| service_orders : "registration_id"
    diagnosis_estimates ||--o| service_orders : "registration_id, estimate_id"
    diagnosis_estimate_revisions ||--o| service_orders : "estimate_id, approved_estimate_revision_no"
    users ||--o{ service_orders : "approval_recorded_by"
    service_orders |o--o{ service_orders : "previous_service_order_id"
    users ||--o{ service_orders : "created_by"
    service_orders ||--o{ service_order_revisions : "service_order_id"
    users ||--o{ service_order_revisions : "created_by"
    users |o--o{ service_order_revisions : "customer_approval_recorded_by"
    service_orders ||--o{ service_order_items : "service_order_id"
    diagnosis_estimate_items |o--o{ service_order_items : "source_estimate_item_id"
    services |o--o{ service_order_items : "service_id"
    spare_parts |o--o{ service_order_items : "spare_part_id"
    service_order_revisions ||--o{ service_order_revision_items : "service_order_id, revision_no"
    service_order_items ||--o{ service_order_revision_items : "service_order_id, item_id"
    service_order_revisions ||--o{ service_order_revision_technicians : "service_order_id, revision_no"
    users ||--o{ service_order_revision_technicians : "technician_id"
    service_order_revisions |o--o| service_orders : "id, current_revision_no"
```

## Billing

```mermaid
erDiagram
    service_order_handoffs {
        char(36) id PK,UK "NOT NULL; UK may be composite"
        char(36) service_order_id FK,UK "NOT NULL; UK may be composite"
        bigint sequence_no UK "NOT NULL; UK may be composite"
        bigint service_order_revision_no FK "NOT NULL"
        varchar(16) event_type "NOT NULL"
        char(36) queued_handoff_id FK,UK "NULL; UK may be composite"
        char(36) created_by FK "NOT NULL"
        datetime(6) created_at "NOT NULL"
        text reason "NULL"
    }
    invoices {
        char(36) id PK,FK,UK "NOT NULL; UK may be composite"
        char(36) service_order_id FK,UK "NOT NULL; UK may be composite"
        varchar(64) reference UK "NOT NULL; UK may be composite"
        bigint current_revision_no FK "NULL"
        bigint issued_revision_no FK "NULL"
        char(36) created_by FK "NOT NULL"
        datetime(6) created_at "NOT NULL"
    }
    invoice_revisions {
        char(36) id PK "NOT NULL"
        char(36) invoice_id FK,UK "NOT NULL; UK may be composite"
        bigint revision_no UK "NOT NULL; UK may be composite"
        char(36) service_order_id FK "NOT NULL"
        char(36) handoff_id FK "NOT NULL"
        char(36) registration_revision_id FK "NOT NULL"
        varchar(20) event_type "NOT NULL"
        varchar(200) customer_name_snapshot "NOT NULL"
        varchar(40) phone_snapshot "NOT NULL"
        text address_snapshot "NULL"
        varchar(32) plate_snapshot "NOT NULL"
        char(36) created_by FK "NOT NULL"
        datetime(6) created_at "NOT NULL"
        text reason "NULL"
    }
    invoice_revision_items {
        char(36) id PK,UK "NOT NULL; UK may be composite"
        char(36) invoice_id FK,UK "NOT NULL; UK may be composite"
        bigint revision_no FK,UK "NOT NULL; UK may be composite"
        char(36) service_order_id FK "NOT NULL"
        char(36) service_order_item_id FK,UK "NOT NULL; UK may be composite"
        char(36) spare_part_id FK,UK "NULL; UK may be composite"
        char(36) service_id FK "NULL"
        int position UK "NOT NULL; UK may be composite"
        varchar(200) name_snapshot "NOT NULL"
        varchar(20) unit_code "NOT NULL"
        tinyint quantity_scale "NOT NULL"
        decimal(15_3) qty "NOT NULL"
        decimal(18_0) master_unit_price_snapshot "NOT NULL"
        decimal(18_0) unit_price "NOT NULL"
        decimal(30_0) subtotal_rupiah "NOT NULL"
        text price_change_reason "NULL"
    }
    payment_destinations {
        char(36) id PK "NOT NULL"
        varchar(16) method "NOT NULL"
        varchar(200) label "NOT NULL"
        varchar(200) bank_name "NULL"
        varchar(100) account_number "NULL"
        varchar(200) account_holder "NULL"
        varchar(500) qris_asset_path "NULL"
        boolean is_active "NOT NULL"
        bigint version "NOT NULL"
        datetime(6) created_at "NOT NULL"
        datetime(6) updated_at "NOT NULL"
    }
    payments {
        char(36) id PK,UK "NOT NULL; UK may be composite"
        char(36) invoice_id FK,UK "NOT NULL; UK may be composite"
        bigint invoice_revision_no FK,UK "NOT NULL; UK may be composite"
        varchar(16) method "NOT NULL"
        decimal(30_0) amount_rupiah "NOT NULL"
        decimal(30_0) received_rupiah "NOT NULL"
        varchar(200) payment_reference "NULL"
        char(36) payment_destination_id FK "NULL"
        json destination_snapshot "NULL"
        char(36) funds_verified_by FK "NULL"
        datetime(6) funds_verified_at "NULL"
        char(36) received_by FK "NOT NULL"
        datetime(6) received_at "NOT NULL"
    }
    service_order_revisions ||--o{ service_order_handoffs : "service_order_id, service_order_revision_no"
    users ||--o{ service_order_handoffs : "created_by"
    service_orders ||--o| invoices : "service_order_id"
    users ||--o{ invoices : "created_by"
    invoices ||--o{ invoice_revisions : "invoice_id, service_order_id"
    service_order_handoffs ||--o{ invoice_revisions : "service_order_id, handoff_id"
    registration_revisions ||--o{ invoice_revisions : "registration_revision_id"
    users ||--o{ invoice_revisions : "created_by"
    invoice_revisions ||--o{ invoice_revision_items : "invoice_id, revision_no"
    invoices ||--o{ invoice_revision_items : "invoice_id, service_order_id"
    service_order_items ||--o{ invoice_revision_items : "service_order_id, service_order_item_id"
    service_order_items |o--o{ invoice_revision_items : "service_order_item_id, spare_part_id"
    spare_parts |o--o{ invoice_revision_items : "spare_part_id"
    services |o--o{ invoice_revision_items : "service_id"
    invoice_revisions ||--o| payments : "invoice_id, invoice_revision_no"
    payment_destinations |o--o{ payments : "payment_destination_id"
    users |o--o{ payments : "funds_verified_by"
    users ||--o{ payments : "received_by"
    service_order_handoffs |o--o| service_order_handoffs : "service_order_id, queued_handoff_id"
    invoice_revisions |o--o| invoices : "id, current_revision_no"
    invoice_revisions |o--o| invoices : "id, issued_revision_no"
```

## Purchasing

```mermaid
erDiagram
    suppliers {
        char(36) id PK "NOT NULL"
        varchar(200) name "NOT NULL"
        varchar(40) phone "NULL"
        text address "NULL"
        boolean is_active "NOT NULL"
        bigint version "NOT NULL"
        datetime(6) created_at "NOT NULL"
        datetime(6) updated_at "NOT NULL"
    }
    purchases {
        char(36) id PK "NOT NULL"
        char(36) supplier_id FK "NOT NULL"
        varchar(64) reference UK "NOT NULL; UK may be composite"
        varchar(100) supplier_document_reference "NULL"
        varchar(200) supplier_name_snapshot "NOT NULL"
        datetime(6) ordered_at "NOT NULL"
        decimal(30_0) document_discount_rupiah "NOT NULL"
        datetime(6) confirmed_at "NULL"
        char(36) confirmed_by FK "NULL"
        bigint version "NOT NULL"
        char(36) created_by FK "NOT NULL"
        datetime(6) created_at "NOT NULL"
    }
    purchase_items {
        char(36) id PK,UK "NOT NULL; UK may be composite"
        char(36) purchase_id FK,UK "NOT NULL; UK may be composite"
        char(36) spare_part_id FK,UK "NOT NULL; UK may be composite"
        int position UK "NOT NULL; UK may be composite"
        varchar(200) name_snapshot "NOT NULL"
        varchar(20) unit_code "NOT NULL"
        tinyint quantity_scale "NOT NULL"
        decimal(15_3) qty "NOT NULL"
        decimal(18_0) unit_purchase_price "NOT NULL"
        decimal(30_0) line_discount_rupiah "NOT NULL"
        decimal(30_0) allocated_document_discount_rupiah "NOT NULL"
        decimal(30_0) net_amount_rupiah "NOT NULL"
    }
    goods_receipts {
        char(36) id PK,UK "NOT NULL; UK may be composite"
        char(36) purchase_id FK,UK "NOT NULL; UK may be composite"
        varchar(64) reference UK "NOT NULL; UK may be composite"
        datetime(6) received_at "NOT NULL"
        char(36) received_by FK "NOT NULL"
        text note "NULL"
    }
    goods_receipt_items {
        char(36) id PK,UK "NOT NULL; UK may be composite"
        char(36) receipt_id FK,UK "NOT NULL; UK may be composite"
        char(36) purchase_id FK,UK "NOT NULL; UK may be composite"
        char(36) purchase_item_id FK,UK "NOT NULL; UK may be composite"
        char(36) spare_part_id FK,UK "NOT NULL; UK may be composite"
        decimal(15_3) qty "NOT NULL"
        decimal(24_6) net_unit_cost_snapshot "NOT NULL"
        decimal(30_0) net_amount_rupiah "NOT NULL"
    }
    purchase_payments {
        char(36) id PK "NOT NULL"
        char(36) purchase_id FK,UK "NOT NULL; UK may be composite"
        decimal(30_0) amount_rupiah "NOT NULL"
        varchar(16) method "NOT NULL"
        varchar(200) payment_reference "NULL"
        char(36) paid_by FK "NOT NULL"
        datetime(6) paid_at "NOT NULL"
    }
    suppliers ||--o{ purchases : "supplier_id"
    users ||--o{ purchases : "created_by"
    users |o--o{ purchases : "confirmed_by"
    purchases ||--o{ purchase_items : "purchase_id"
    spare_parts ||--o{ purchase_items : "spare_part_id"
    purchases ||--o{ goods_receipts : "purchase_id"
    users ||--o{ goods_receipts : "received_by"
    goods_receipts ||--o{ goods_receipt_items : "purchase_id, receipt_id"
    purchase_items ||--o{ goods_receipt_items : "purchase_id, purchase_item_id"
    purchase_items ||--o{ goods_receipt_items : "purchase_item_id, spare_part_id"
    purchases ||--o| purchase_payments : "purchase_id"
    users ||--o{ purchase_payments : "paid_by"
```

## SupplierReturns

```mermaid
erDiagram
    supplier_returns {
        char(36) id PK,UK "NOT NULL; UK may be composite"
        char(36) purchase_id FK,UK "NOT NULL; UK may be composite"
        varchar(64) reference UK "NOT NULL; UK may be composite"
        varchar(20) settlement_type "NOT NULL"
        text reason "NOT NULL"
        datetime(6) handed_over_at "NULL"
        char(36) handed_over_by FK "NULL"
        datetime(6) credit_applied_at "NULL"
        char(36) credit_applied_by FK "NULL"
        char(36) created_by FK "NOT NULL"
        datetime(6) created_at "NOT NULL"
    }
    supplier_return_items {
        char(36) id PK,UK "NOT NULL; UK may be composite"
        char(36) supplier_return_id FK,UK "NOT NULL; UK may be composite"
        char(36) purchase_id FK "NOT NULL"
        char(36) receipt_item_id FK,UK "NOT NULL; UK may be composite"
        char(36) spare_part_id FK,UK "NOT NULL; UK may be composite"
        decimal(15_3) qty "NOT NULL"
        decimal(24_6) source_unit_cost_snapshot "NOT NULL"
        decimal(30_0) return_value_rupiah "NOT NULL"
    }
    supplier_refund_receipts {
        char(36) id PK "NOT NULL"
        char(36) supplier_return_id FK "NOT NULL"
        decimal(30_0) amount_rupiah "NOT NULL"
        char(36) received_by FK "NOT NULL"
        datetime(6) received_at "NOT NULL"
        varchar(200) payment_reference "NULL"
    }
    replacement_receipts {
        char(36) id PK,UK "NOT NULL; UK may be composite"
        char(36) supplier_return_item_id FK "NOT NULL"
        char(36) spare_part_id FK,UK "NOT NULL; UK may be composite"
        decimal(15_3) qty "NOT NULL"
        char(36) received_by FK "NOT NULL"
        datetime(6) received_at "NOT NULL"
    }
    purchases ||--o{ supplier_returns : "purchase_id"
    users ||--o{ supplier_returns : "created_by"
    users |o--o{ supplier_returns : "handed_over_by"
    users |o--o{ supplier_returns : "credit_applied_by"
    supplier_returns ||--o{ supplier_return_items : "purchase_id, supplier_return_id"
    goods_receipt_items ||--o{ supplier_return_items : "receipt_item_id, spare_part_id"
    goods_receipt_items ||--o{ supplier_return_items : "purchase_id, receipt_item_id, spare_part_id"
    supplier_returns ||--o{ supplier_refund_receipts : "supplier_return_id"
    users ||--o{ supplier_refund_receipts : "received_by"
    supplier_return_items ||--o{ replacement_receipts : "supplier_return_item_id, spare_part_id"
    users ||--o{ replacement_receipts : "received_by"
```

## CustomerReturns

```mermaid
erDiagram
    customer_returns {
        char(36) id PK,UK "NOT NULL; UK may be composite"
        char(36) invoice_id FK,UK "NOT NULL; UK may be composite"
        varchar(64) reference UK "NOT NULL; UK may be composite"
        text reason "NOT NULL"
        char(36) created_by FK "NOT NULL"
        datetime(6) created_at "NOT NULL"
    }
    customer_return_items {
        char(36) id PK,UK "NOT NULL; UK may be composite"
        char(36) customer_return_id FK,UK "NOT NULL; UK may be composite"
        char(36) invoice_id FK "NOT NULL"
        char(36) invoice_revision_item_id FK,UK "NOT NULL; UK may be composite"
        char(36) spare_part_id FK,UK "NOT NULL; UK may be composite"
        decimal(15_3) qty "NOT NULL"
        datetime(6) received_at "NOT NULL"
        char(36) received_by FK "NOT NULL"
        varchar(16) inspection_result "NOT NULL"
        datetime(6) inspected_at "NULL"
        char(36) inspected_by FK "NULL"
        text inspection_note "NULL"
    }
    refund_authorizations {
        char(36) id PK,UK "NOT NULL; UK may be composite"
        char(36) invoice_id FK,UK "NOT NULL; UK may be composite"
        char(36) customer_return_id FK "NULL"
        decimal(30_0) approved_amount_rupiah "NOT NULL"
        text reason "NOT NULL"
        char(36) approved_by FK "NOT NULL"
        datetime(6) approved_at "NOT NULL"
        char(36) credit_note_id FK "NULL"
    }
    customer_refunds {
        char(36) id PK "NOT NULL"
        char(36) invoice_id FK "NOT NULL"
        char(36) authorization_id FK,UK "NOT NULL; UK may be composite"
        decimal(30_0) amount_rupiah "NOT NULL"
        varchar(16) method "NOT NULL"
        varchar(200) payment_reference "NULL"
        char(36) paid_by FK "NOT NULL"
        datetime(6) paid_at "NOT NULL"
    }
    invoice_credit_notes {
        char(36) id PK,UK "NOT NULL; UK may be composite"
        char(36) invoice_id FK,UK "NOT NULL; UK may be composite"
        bigint invoice_revision_no FK "NOT NULL"
        char(36) customer_return_id FK "NULL"
        decimal(30_0) amount_rupiah "NOT NULL"
        text reason "NOT NULL"
        char(36) approved_by FK "NOT NULL"
        datetime(6) approved_at "NOT NULL"
    }
    invoices ||--o{ customer_returns : "invoice_id"
    users ||--o{ customer_returns : "created_by"
    customer_returns ||--o{ customer_return_items : "invoice_id, customer_return_id"
    invoice_revision_items ||--o{ customer_return_items : "invoice_id, invoice_revision_item_id"
    invoice_revision_items ||--o{ customer_return_items : "invoice_revision_item_id, spare_part_id"
    users ||--o{ customer_return_items : "received_by"
    users |o--o{ customer_return_items : "inspected_by"
    invoices ||--o{ refund_authorizations : "invoice_id"
    customer_returns |o--o{ refund_authorizations : "invoice_id, customer_return_id"
    users ||--o{ refund_authorizations : "approved_by"
    refund_authorizations ||--o| customer_refunds : "invoice_id, authorization_id"
    users ||--o{ customer_refunds : "paid_by"
    invoice_revisions ||--o{ invoice_credit_notes : "invoice_id, invoice_revision_no"
    customer_returns |o--o{ invoice_credit_notes : "invoice_id, customer_return_id"
    users ||--o{ invoice_credit_notes : "approved_by"
    invoice_credit_notes |o--o{ refund_authorizations : "invoice_id, credit_note_id"
```

## Stock

```mermaid
erDiagram
    stock_openings {
        char(36) id PK,UK "NOT NULL; UK may be composite"
        char(36) spare_part_id FK,UK "NOT NULL; UK may be composite"
        decimal(15_3) qty "NOT NULL"
        decimal(15_3) damaged_qty "NOT NULL"
        decimal(24_6) initial_unit_cost "NULL"
        datetime(6) counted_at "NOT NULL"
        char(36) created_by FK "NOT NULL"
        datetime(6) created_at "NOT NULL"
    }
    stock_reservation_events {
        char(36) id PK "NOT NULL"
        char(36) service_order_item_id FK,UK "NOT NULL; UK may be composite"
        char(36) spare_part_id FK "NOT NULL"
        bigint sequence_no UK "NOT NULL; UK may be composite"
        decimal(15_3) qty "NOT NULL"
        varchar(16) state "NOT NULL"
        text reason "NOT NULL"
        char(36) created_by FK "NOT NULL"
        datetime(6) created_at "NOT NULL"
    }
    stock_blocks {
        char(36) id PK,UK "NOT NULL; UK may be composite"
        char(36) spare_part_id FK,UK "NOT NULL; UK may be composite"
        varchar(16) block_type "NOT NULL"
        char(36) source_receipt_item_id FK "NULL"
        char(36) customer_return_item_id FK "NULL"
        char(36) opening_id FK "NULL"
        decimal(15_3) original_qty "NOT NULL"
        decimal(15_3) remaining_qty "NOT NULL"
        text reason "NOT NULL"
        bigint version "NOT NULL"
        char(36) created_by FK "NOT NULL"
        datetime(6) created_at "NOT NULL"
    }
    stock_block_events {
        char(36) id PK "NOT NULL"
        char(36) stock_block_id FK,UK "NOT NULL; UK may be composite"
        bigint sequence_no UK "NOT NULL; UK may be composite"
        decimal(15_3) old_qty "NOT NULL"
        decimal(15_3) new_qty "NOT NULL"
        text reason "NOT NULL"
        char(36) created_by FK "NOT NULL"
        datetime(6) created_at "NOT NULL"
    }
    stock_movements {
        char(36) id PK "NOT NULL"
        char(36) spare_part_id FK "NOT NULL"
        varchar(24) movement_type "NOT NULL"
        decimal(15_3) qty_delta "NOT NULL"
        char(36) opening_id FK,UK "NULL; UK may be composite"
        char(36) receipt_item_id FK,UK "NULL; UK may be composite"
        char(36) invoice_revision_item_id FK,UK "NULL; UK may be composite"
        char(36) supplier_return_item_id FK,UK "NULL; UK may be composite"
        char(36) replacement_receipt_id FK,UK "NULL; UK may be composite"
        char(36) customer_return_item_id FK,UK "NULL; UK may be composite"
        char(36) created_by FK "NOT NULL"
        datetime(6) created_at "NOT NULL"
    }
    spare_parts ||--o| stock_openings : "spare_part_id"
    users ||--o{ stock_openings : "created_by"
    service_order_items ||--o{ stock_reservation_events : "service_order_item_id, spare_part_id"
    users ||--o{ stock_reservation_events : "created_by"
    spare_parts ||--o{ stock_blocks : "spare_part_id"
    goods_receipt_items |o--o{ stock_blocks : "source_receipt_item_id, spare_part_id"
    customer_return_items |o--o{ stock_blocks : "customer_return_item_id, spare_part_id"
    stock_openings |o--o{ stock_blocks : "opening_id, spare_part_id"
    users ||--o{ stock_blocks : "created_by"
    stock_blocks ||--o{ stock_block_events : "stock_block_id"
    users ||--o{ stock_block_events : "created_by"
    spare_parts ||--o{ stock_movements : "spare_part_id"
    users ||--o{ stock_movements : "created_by"
    stock_openings |o--o| stock_movements : "opening_id, spare_part_id"
    goods_receipt_items |o--o| stock_movements : "receipt_item_id, spare_part_id"
    invoice_revision_items |o--o| stock_movements : "invoice_revision_item_id, spare_part_id"
    supplier_return_items |o--o| stock_movements : "supplier_return_item_id, spare_part_id"
    replacement_receipts |o--o| stock_movements : "replacement_receipt_id, spare_part_id"
    customer_return_items |o--o| stock_movements : "customer_return_item_id, spare_part_id"
```

## Operations

```mermaid
erDiagram
    expenses {
        char(36) id PK "NOT NULL"
        varchar(64) reference UK "NOT NULL; UK may be composite"
        varchar(100) category "NOT NULL"
        text description "NOT NULL"
        decimal(30_0) amount_rupiah "NOT NULL"
        char(36) purchase_id FK "NULL"
        char(36) paid_by FK "NOT NULL"
        datetime(6) paid_at "NOT NULL"
    }
    audit_logs {
        char(36) id PK "NOT NULL"
        char(36) actor_id FK "NOT NULL"
        varchar(200) actor_name_snapshot "NOT NULL"
        varchar(20) actor_role_snapshot "NOT NULL"
        varchar(100) action "NOT NULL"
        varchar(100) subject_type "NOT NULL"
        char(36) subject_id "NOT NULL"
        json old_values "NULL"
        json new_values "NULL"
        text reason "NULL"
        datetime(6) occurred_at "NOT NULL"
    }
    idempotency_requests {
        char(36) id PK "NOT NULL"
        char(36) actor_id FK,UK "NOT NULL; UK may be composite"
        varchar(100) operation UK "NOT NULL; UK may be composite"
        varchar(128) idempotency_key UK "NOT NULL; UK may be composite"
        char(64) request_hash "NOT NULL"
        varchar(16) state "NOT NULL"
        smallint response_status "NULL"
        json response_body "NULL"
        datetime(6) created_at "NOT NULL"
        datetime(6) completed_at "NULL"
    }
    document_counters {
        varchar(32) document_type PK "NOT NULL"
        varchar(20) period_key PK "NOT NULL"
        bigint last_number "NOT NULL"
    }
    purchases |o--o{ expenses : "purchase_id"
    users ||--o{ expenses : "paid_by"
    users ||--o{ audit_logs : "actor_id"
    users ||--o{ idempotency_requests : "actor_id"
```

## Proyeksi, bukan tabel transaksi tambahan

- `v_current_stock_reservations`: event reservasi terakhir per baris SO.
- `v_stock_quantities`: stok tercatat, reservasi, blokir dan stok tersedia.
- `v_invoice_balances`: total revisi aktif, kredit, pembayaran, refund dan saldo.
- `v_supplier_balances`: nilai pembelian, pengurangan utang, pembayaran dan sisa.

Dashboard, laporan dan pencarian global membaca data tersebut/dokumen sumber;
tidak membuat tabel saldo laporan atau tabel riwayat pelanggan kedua.
