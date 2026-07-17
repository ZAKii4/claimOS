-- =============================================================================
-- Migration 001v2: Tenant Schema Template
-- Enterprise AI Claims Processing Platform v2
-- =============================================================================
-- This script is NOT run directly. It is the TEMPLATE used by the tenant
-- provisioning service to create a new tenant's schema.
--
-- The provisioning service:
--   1. Creates a new PostgreSQL schema (e.g., CREATE SCHEMA tenant_acme)
--   2. Sets search_path to the new schema
--   3. Executes this template
--   4. Registers the tenant in platform.tenant
--
-- All FKs to lookup tables reference platform.<table> explicitly.
-- All FKs within the tenant schema are local (no cross-schema domain FKs).
-- =============================================================================

BEGIN;

-- =========================================================================
-- OPERATORS (Per-Tenant: each insurer has their own reviewers)
-- =========================================================================

CREATE TABLE operator (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id    VARCHAR(32) UNIQUE NOT NULL,
    full_name      VARCHAR(256) NOT NULL,
    email          VARCHAR(256) UNIQUE NOT NULL,
    role_id        UUID NOT NULL REFERENCES platform.operator_role(id),
    is_active      BOOLEAN NOT NULL DEFAULT TRUE,
    accuracy_score NUMERIC(5,4),
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_operator_active ON operator(is_active) WHERE is_active = TRUE;

-- =========================================================================
-- INSURANCE POLICY
-- =========================================================================

CREATE TABLE insurance_policy (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_number         VARCHAR(64) UNIQUE NOT NULL,
    insurer_id            UUID NOT NULL REFERENCES platform.insurer(id),
    product_type_id       UUID NOT NULL REFERENCES platform.product_type(id),
    effective_date        DATE NOT NULL,
    expiry_date           DATE NOT NULL,
    status                VARCHAR(16) NOT NULL DEFAULT 'ACTIVE'
                          CHECK (status IN ('ACTIVE','EXPIRED','CANCELLED','SUSPENDED')),
    policyholder_party_id UUID,  -- FK added after claim_party is created
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_policy_dates CHECK (expiry_date > effective_date)
);

CREATE INDEX idx_policy_number ON insurance_policy(policy_number);
CREATE INDEX idx_policy_status ON insurance_policy(status);
CREATE INDEX idx_policy_dates  ON insurance_policy(effective_date, expiry_date);

-- =========================================================================
-- CLAIM FILE (Root Aggregate)
-- =========================================================================

CREATE TABLE claim_file (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_ref          VARCHAR(64) UNIQUE NOT NULL,
    policy_id             UUID REFERENCES insurance_policy(id),
    claim_type_id         UUID NOT NULL REFERENCES platform.claim_type(id),
    date_of_loss          DATE NOT NULL,
    date_received         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    composite_confidence  NUMERIC(5,4) CHECK (composite_confidence BETWEEN 0 AND 1),
    status_id             UUID NOT NULL REFERENCES platform.claim_status(id),
    stp_eligible          BOOLEAN NOT NULL DEFAULT FALSE,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_claim_status_date ON claim_file(status_id, date_received DESC);
CREATE INDEX idx_claim_policy      ON claim_file(policy_id);
CREATE INDEX idx_claim_loss_date   ON claim_file(date_of_loss);

-- =========================================================================
-- DOCUMENTS & PAGES
-- =========================================================================

CREATE TABLE claim_document (
    id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id                  UUID NOT NULL REFERENCES claim_file(id) ON DELETE CASCADE,
    document_type_id          UUID NOT NULL REFERENCES platform.document_type(id),
    classification_confidence NUMERIC(5,4) CHECK (classification_confidence BETWEEN 0 AND 1),
    page_range_start          INTEGER NOT NULL CHECK (page_range_start >= 1),
    page_range_end            INTEGER NOT NULL CHECK (page_range_end >= 1),
    language                  VARCHAR(8) NOT NULL DEFAULT 'fr',
    is_duplicate              BOOLEAN NOT NULL DEFAULT FALSE,
    duplicate_of_id           UUID REFERENCES claim_document(id),
    storage_uri               TEXT NOT NULL,
    created_at                TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_page_range CHECK (page_range_end >= page_range_start),
    CONSTRAINT chk_dup_self   CHECK (duplicate_of_id IS DISTINCT FROM id)
);

CREATE INDEX idx_doc_claim ON claim_document(claim_id);

CREATE TABLE document_page (
    id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id               UUID NOT NULL REFERENCES claim_document(id) ON DELETE CASCADE,
    page_number               INTEGER NOT NULL CHECK (page_number >= 1),
    original_page_number      INTEGER NOT NULL CHECK (original_page_number >= 1),
    image_uri                 TEXT NOT NULL,
    ocr_hocr_uri              TEXT NOT NULL,
    orientation_corrected_deg INTEGER DEFAULT 0,
    resolution_dpi            INTEGER NOT NULL,
    quality_score             NUMERIC(5,4) CHECK (quality_score BETWEEN 0 AND 1),
    is_missing_detected       BOOLEAN NOT NULL DEFAULT FALSE,
    created_at                TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_doc_page UNIQUE (document_id, page_number)
);

CREATE INDEX idx_page_quality ON document_page(quality_score) WHERE quality_score < 0.5;

-- =========================================================================
-- PARTIES (with Temporal Versioning)
-- =========================================================================

CREATE TABLE claim_party (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id   UUID NOT NULL REFERENCES claim_file(id) ON DELETE CASCADE,
    role_id    UUID NOT NULL REFERENCES platform.party_role(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_party_claim ON claim_party(claim_id);

-- Deferred FK from insurance_policy
ALTER TABLE insurance_policy
    ADD CONSTRAINT fk_policy_holder
    FOREIGN KEY (policyholder_party_id) REFERENCES claim_party(id);

CREATE TABLE party_version (
    id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    party_id                 UUID NOT NULL REFERENCES claim_party(id) ON DELETE CASCADE,
    version                  INTEGER NOT NULL CHECK (version >= 1),
    is_current               BOOLEAN NOT NULL DEFAULT TRUE,
    origin                   VARCHAR(16) NOT NULL
                             CHECK (origin IN ('AI_EXTRACTION','HUMAN_CORRECTION','DB_ENRICHMENT')),
    operator_id              UUID REFERENCES operator(id),
    last_name                VARCHAR(128),
    first_name               VARCHAR(128),
    date_of_birth            DATE,
    national_id_encrypted    BYTEA,          -- pgcrypto AES-256 encrypted
    phone_encrypted          BYTEA,          -- pgcrypto AES-256 encrypted
    address_line_1           VARCHAR(256),
    address_city             VARCHAR(128),
    address_postal_code      VARCHAR(16),
    address_country_iso      CHAR(2),
    driving_license_number   VARCHAR(32),
    driving_license_category VARCHAR(8),
    created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_party_version UNIQUE (party_id, version)
);

-- Enforce exactly one current version per party
CREATE UNIQUE INDEX idx_party_current
    ON party_version(party_id) WHERE is_current = TRUE;

-- =========================================================================
-- PARTY FIELD PROVENANCE (Real FK — replaces polymorphic field_provenance)
-- =========================================================================

CREATE TABLE party_field_provenance (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_id           UUID NOT NULL REFERENCES party_version(id) ON DELETE CASCADE,
    field_name           VARCHAR(64) NOT NULL,
    confidence           NUMERIC(5,4) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    source_page_id       UUID REFERENCES document_page(id),
    bbox_x1              INTEGER,
    bbox_y1              INTEGER,
    bbox_x2              INTEGER,
    bbox_y2              INTEGER,
    extraction_method_id UUID NOT NULL REFERENCES platform.extraction_method(id),
    model_version        VARCHAR(32),
    raw_ocr_token        VARCHAR(512),
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_party_prov UNIQUE (version_id, field_name),
    CONSTRAINT chk_bbox_complete CHECK (
        (bbox_x1 IS NULL AND bbox_y1 IS NULL AND bbox_x2 IS NULL AND bbox_y2 IS NULL)
        OR (bbox_x1 IS NOT NULL AND bbox_y1 IS NOT NULL AND bbox_x2 IS NOT NULL AND bbox_y2 IS NOT NULL)
    ),
    CONSTRAINT chk_bbox_valid CHECK (
        bbox_x1 IS NULL OR (bbox_x2 > bbox_x1 AND bbox_y2 > bbox_y1)
    )
);

CREATE INDEX idx_party_prov_conf ON party_field_provenance(confidence) WHERE confidence < 0.85;

-- =========================================================================
-- VEHICLES (with Temporal Versioning)
-- =========================================================================

CREATE TABLE claim_vehicle (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id           UUID NOT NULL REFERENCES claim_file(id) ON DELETE CASCADE,
    party_id           UUID REFERENCES claim_party(id),
    is_insured_vehicle BOOLEAN NOT NULL DEFAULT FALSE,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_vehicle_claim ON claim_vehicle(claim_id);

CREATE TABLE vehicle_version (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vehicle_id         UUID NOT NULL REFERENCES claim_vehicle(id) ON DELETE CASCADE,
    version            INTEGER NOT NULL CHECK (version >= 1),
    is_current         BOOLEAN NOT NULL DEFAULT TRUE,
    origin             VARCHAR(16) NOT NULL
                       CHECK (origin IN ('AI_EXTRACTION','HUMAN_CORRECTION','DB_ENRICHMENT')),
    operator_id        UUID REFERENCES operator(id),
    registration_plate VARCHAR(20),
    vin                VARCHAR(17),
    make               VARCHAR(64),
    model              VARCHAR(64),
    year               INTEGER CHECK (year BETWEEN 1900 AND 2100),
    color              VARCHAR(32),
    fuel_type          VARCHAR(16)
                       CHECK (fuel_type IN ('GASOLINE','DIESEL','ELECTRIC','HYBRID','LPG','UNKNOWN')),
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_vehicle_version UNIQUE (vehicle_id, version)
);

CREATE UNIQUE INDEX idx_vehicle_current
    ON vehicle_version(vehicle_id) WHERE is_current = TRUE;

CREATE TABLE vehicle_field_provenance (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_id           UUID NOT NULL REFERENCES vehicle_version(id) ON DELETE CASCADE,
    field_name           VARCHAR(64) NOT NULL,
    confidence           NUMERIC(5,4) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    source_page_id       UUID REFERENCES document_page(id),
    bbox_x1              INTEGER,
    bbox_y1              INTEGER,
    bbox_x2              INTEGER,
    bbox_y2              INTEGER,
    extraction_method_id UUID NOT NULL REFERENCES platform.extraction_method(id),
    model_version        VARCHAR(32),
    raw_ocr_token        VARCHAR(512),
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_vehicle_prov UNIQUE (version_id, field_name),
    CONSTRAINT chk_bbox_complete CHECK (
        (bbox_x1 IS NULL AND bbox_y1 IS NULL AND bbox_x2 IS NULL AND bbox_y2 IS NULL)
        OR (bbox_x1 IS NOT NULL AND bbox_y1 IS NOT NULL AND bbox_x2 IS NOT NULL AND bbox_y2 IS NOT NULL)
    ),
    CONSTRAINT chk_bbox_valid CHECK (
        bbox_x1 IS NULL OR (bbox_x2 > bbox_x1 AND bbox_y2 > bbox_y1)
    )
);

CREATE INDEX idx_vehicle_prov_conf ON vehicle_field_provenance(confidence) WHERE confidence < 0.85;

CREATE TABLE vehicle_damage (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vehicle_id     UUID NOT NULL REFERENCES claim_vehicle(id) ON DELETE CASCADE,
    damage_zone_id UUID NOT NULL REFERENCES platform.damage_zone(id),
    severity_id    UUID NOT NULL REFERENCES platform.damage_severity(id),
    description    TEXT,
    estimated_cost NUMERIC(12,2),
    currency       CHAR(3) NOT NULL DEFAULT 'MAD',
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =========================================================================
-- MEDICAL (with Temporal Versioning)
-- =========================================================================

CREATE TABLE medical_certificate (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id    UUID NOT NULL REFERENCES claim_file(id) ON DELETE CASCADE,
    party_id    UUID NOT NULL REFERENCES claim_party(id),
    document_id UUID NOT NULL REFERENCES claim_document(id),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE medical_cert_version (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    certificate_id          UUID NOT NULL REFERENCES medical_certificate(id) ON DELETE CASCADE,
    version                 INTEGER NOT NULL CHECK (version >= 1),
    is_current              BOOLEAN NOT NULL DEFAULT TRUE,
    origin                  VARCHAR(16) NOT NULL
                            CHECK (origin IN ('AI_EXTRACTION','HUMAN_CORRECTION','DB_ENRICHMENT')),
    operator_id             UUID REFERENCES operator(id),
    issuing_facility        VARCHAR(256),
    issuing_doctor          VARCHAR(256),
    issue_date              DATE,
    initial_disability_days INTEGER CHECK (initial_disability_days >= 0),
    hospitalization_days    INTEGER CHECK (hospitalization_days >= 0),
    is_final                BOOLEAN,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_medcert_version UNIQUE (certificate_id, version)
);

CREATE UNIQUE INDEX idx_medcert_current
    ON medical_cert_version(certificate_id) WHERE is_current = TRUE;

CREATE TABLE medical_field_provenance (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_id           UUID NOT NULL REFERENCES medical_cert_version(id) ON DELETE CASCADE,
    field_name           VARCHAR(64) NOT NULL,
    confidence           NUMERIC(5,4) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    source_page_id       UUID REFERENCES document_page(id),
    bbox_x1              INTEGER,
    bbox_y1              INTEGER,
    bbox_x2              INTEGER,
    bbox_y2              INTEGER,
    extraction_method_id UUID NOT NULL REFERENCES platform.extraction_method(id),
    model_version        VARCHAR(32),
    raw_ocr_token        VARCHAR(512),
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_medical_prov UNIQUE (version_id, field_name),
    CONSTRAINT chk_bbox_complete CHECK (
        (bbox_x1 IS NULL AND bbox_y1 IS NULL AND bbox_x2 IS NULL AND bbox_y2 IS NULL)
        OR (bbox_x1 IS NOT NULL AND bbox_y1 IS NOT NULL AND bbox_x2 IS NOT NULL AND bbox_y2 IS NOT NULL)
    ),
    CONSTRAINT chk_bbox_valid CHECK (
        bbox_x1 IS NULL OR (bbox_x2 > bbox_x1 AND bbox_y2 > bbox_y1)
    )
);

CREATE INDEX idx_medical_prov_conf ON medical_field_provenance(confidence) WHERE confidence < 0.85;

CREATE TABLE medical_finding (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    certificate_id  UUID NOT NULL REFERENCES medical_certificate(id) ON DELETE CASCADE,
    icd10_code      VARCHAR(8),
    body_region_id  UUID REFERENCES platform.body_region(id),
    injury_type_id  UUID REFERENCES platform.injury_type(id),
    prognosis_id    UUID REFERENCES platform.prognosis(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =========================================================================
-- POLICE REPORT (with Temporal Versioning)
-- =========================================================================

CREATE TABLE police_report (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id    UUID NOT NULL REFERENCES claim_file(id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES claim_document(id),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE police_report_version (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id             UUID NOT NULL REFERENCES police_report(id) ON DELETE CASCADE,
    version               INTEGER NOT NULL CHECK (version >= 1),
    is_current            BOOLEAN NOT NULL DEFAULT TRUE,
    origin                VARCHAR(16) NOT NULL
                          CHECK (origin IN ('AI_EXTRACTION','HUMAN_CORRECTION','DB_ENRICHMENT')),
    operator_id           UUID REFERENCES operator(id),
    report_number         VARCHAR(64),
    report_date           DATE,
    station_name          VARCHAR(256),
    accident_location     VARCHAR(512),
    accident_datetime     TIMESTAMPTZ,
    weather_condition_id  UUID REFERENCES platform.weather_condition(id),
    road_condition_id     UUID REFERENCES platform.road_condition(id),
    liability_split_json  JSONB,
    alcohol_test_result   VARCHAR(16)
                          CHECK (alcohol_test_result IN ('POSITIVE','NEGATIVE','NOT_TESTED')),
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_pr_version UNIQUE (report_id, version)
);

CREATE UNIQUE INDEX idx_pr_current
    ON police_report_version(report_id) WHERE is_current = TRUE;

CREATE TABLE police_field_provenance (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_id           UUID NOT NULL REFERENCES police_report_version(id) ON DELETE CASCADE,
    field_name           VARCHAR(64) NOT NULL,
    confidence           NUMERIC(5,4) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    source_page_id       UUID REFERENCES document_page(id),
    bbox_x1              INTEGER,
    bbox_y1              INTEGER,
    bbox_x2              INTEGER,
    bbox_y2              INTEGER,
    extraction_method_id UUID NOT NULL REFERENCES platform.extraction_method(id),
    model_version        VARCHAR(32),
    raw_ocr_token        VARCHAR(512),
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_police_prov UNIQUE (version_id, field_name),
    CONSTRAINT chk_bbox_complete CHECK (
        (bbox_x1 IS NULL AND bbox_y1 IS NULL AND bbox_x2 IS NULL AND bbox_y2 IS NULL)
        OR (bbox_x1 IS NOT NULL AND bbox_y1 IS NOT NULL AND bbox_x2 IS NOT NULL AND bbox_y2 IS NOT NULL)
    ),
    CONSTRAINT chk_bbox_valid CHECK (
        bbox_x1 IS NULL OR (bbox_x2 > bbox_x1 AND bbox_y2 > bbox_y1)
    )
);

CREATE INDEX idx_police_prov_conf ON police_field_provenance(confidence) WHERE confidence < 0.85;

CREATE TABLE police_party_statement (
    id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id                UUID NOT NULL REFERENCES police_report(id) ON DELETE CASCADE,
    party_id                 UUID NOT NULL REFERENCES claim_party(id),
    statement_summary        TEXT,
    is_consistent_with_facts BOOLEAN,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =========================================================================
-- VALIDATION & DECISION
-- =========================================================================

CREATE TABLE validation_decision (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id             UUID NOT NULL REFERENCES claim_file(id) ON DELETE CASCADE,
    decision             VARCHAR(16) NOT NULL
                         CHECK (decision IN ('STP_APPROVED','HITL_REVIEW','REJECTED','PENDING_DOCUMENTS')),
    composite_confidence NUMERIC(5,4) NOT NULL CHECK (composite_confidence BETWEEN 0 AND 1),
    model_version        VARCHAR(32),
    decided_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    decided_by           VARCHAR(16) NOT NULL
                         CHECK (decided_by IN ('AI_ENGINE','HUMAN_OPERATOR')),
    operator_id          UUID REFERENCES operator(id)
);

CREATE INDEX idx_vd_claim    ON validation_decision(claim_id);
CREATE INDEX idx_vd_decision ON validation_decision(decision);

CREATE TABLE validation_field_flag (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    decision_id    UUID NOT NULL REFERENCES validation_decision(id) ON DELETE CASCADE,
    entity_table   VARCHAR(64) NOT NULL,
    entity_id      UUID NOT NULL,
    field_name     VARCHAR(64) NOT NULL,
    flag_reason_id UUID NOT NULL REFERENCES platform.flag_reason(id),
    resolved       BOOLEAN NOT NULL DEFAULT FALSE,
    resolved_by    UUID REFERENCES operator(id),
    resolved_at    TIMESTAMPTZ,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_vff_unresolved ON validation_field_flag(flag_reason_id) WHERE resolved = FALSE;

-- =========================================================================
-- DISCREPANCIES
-- =========================================================================

CREATE TABLE claim_discrepancy (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id            UUID NOT NULL REFERENCES claim_file(id) ON DELETE CASCADE,
    discrepancy_type_id UUID NOT NULL REFERENCES platform.discrepancy_type(id),
    entity_a_table      VARCHAR(64) NOT NULL,
    entity_a_id         UUID NOT NULL,
    entity_a_field      VARCHAR(64) NOT NULL,
    entity_b_table      VARCHAR(64) NOT NULL,
    entity_b_id         UUID NOT NULL,
    entity_b_field      VARCHAR(64) NOT NULL,
    severity            VARCHAR(16) NOT NULL
                        CHECK (severity IN ('INFO','WARNING','CRITICAL')),
    description         TEXT,
    resolved            BOOLEAN NOT NULL DEFAULT FALSE,
    resolved_by         UUID REFERENCES operator(id),
    resolved_at         TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_disc_unresolved ON claim_discrepancy(severity) WHERE resolved = FALSE;

-- =========================================================================
-- IMMUTABLE AUDIT LOG (Partitioned by Month)
-- =========================================================================

CREATE TABLE claim_event (
    id            UUID NOT NULL DEFAULT gen_random_uuid(),
    claim_id      UUID NOT NULL,  -- No FK: partitioned tables cannot have standard FKs in PG
    event_type_id UUID NOT NULL REFERENCES platform.event_type(id),
    actor_type    VARCHAR(16) NOT NULL
                  CHECK (actor_type IN ('SYSTEM','AI_AGENT','HUMAN_OPERATOR')),
    actor_id      VARCHAR(64) NOT NULL,
    entity_table  VARCHAR(64),
    entity_id     UUID,
    old_version   INTEGER,
    new_version   INTEGER,
    metadata      JSONB,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- Create partitions for the next 12 months
-- In production, pg_partman automates this.
CREATE TABLE claim_event_2026_07 PARTITION OF claim_event
    FOR VALUES FROM ('2026-07-01') TO ('2026-08-01');
CREATE TABLE claim_event_2026_08 PARTITION OF claim_event
    FOR VALUES FROM ('2026-08-01') TO ('2026-09-01');
CREATE TABLE claim_event_2026_09 PARTITION OF claim_event
    FOR VALUES FROM ('2026-09-01') TO ('2026-10-01');
CREATE TABLE claim_event_2026_10 PARTITION OF claim_event
    FOR VALUES FROM ('2026-10-01') TO ('2026-11-01');
CREATE TABLE claim_event_2026_11 PARTITION OF claim_event
    FOR VALUES FROM ('2026-11-01') TO ('2026-12-01');
CREATE TABLE claim_event_2026_12 PARTITION OF claim_event
    FOR VALUES FROM ('2026-12-01') TO ('2027-01-01');

-- Immutability enforcement
CREATE OR REPLACE FUNCTION prevent_audit_mutation()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'claim_event is an immutable audit log. UPDATE and DELETE are prohibited.';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_audit_immutable
    BEFORE UPDATE OR DELETE ON claim_event
    FOR EACH ROW
    EXECUTE FUNCTION prevent_audit_mutation();

CREATE INDEX idx_event_claim  ON claim_event(claim_id, created_at DESC);
CREATE INDEX idx_event_type   ON claim_event(event_type_id);
CREATE INDEX idx_event_actor  ON claim_event(actor_type, actor_id);

COMMIT;
