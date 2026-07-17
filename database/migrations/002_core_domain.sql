-- =============================================================================
-- Migration 002: Core Domain Tables
-- Enterprise AI Claims Processing Platform
-- =============================================================================
-- Operators, Policies, Claims, Documents, Pages.
-- These form the structural backbone of the platform.
-- =============================================================================

BEGIN;

-- -------------------------------------------------------------------------
-- Operators (human reviewers)
-- -------------------------------------------------------------------------
CREATE TABLE operator (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id    VARCHAR(32) UNIQUE NOT NULL,
    full_name      VARCHAR(256) NOT NULL,
    email          VARCHAR(256) UNIQUE NOT NULL,
    role_id        UUID NOT NULL REFERENCES operator_role(id),
    is_active      BOOLEAN NOT NULL DEFAULT TRUE,
    accuracy_score NUMERIC(5,4),
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_operator_role ON operator(role_id);
CREATE INDEX idx_operator_active ON operator(is_active) WHERE is_active = TRUE;

-- -------------------------------------------------------------------------
-- Insurance Policy
-- -------------------------------------------------------------------------
CREATE TABLE insurance_policy (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_number         VARCHAR(64) UNIQUE NOT NULL,
    insurer_id            UUID NOT NULL REFERENCES insurer(id),
    product_type_id       UUID NOT NULL REFERENCES product_type(id),
    effective_date        DATE NOT NULL,
    expiry_date           DATE NOT NULL,
    status                VARCHAR(16) NOT NULL DEFAULT 'ACTIVE'
                          CHECK (status IN ('ACTIVE','EXPIRED','CANCELLED','SUSPENDED')),
    policyholder_party_id UUID,  -- FK added after claim_party is created
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_policy_dates CHECK (expiry_date > effective_date)
);

CREATE INDEX idx_policy_insurer    ON insurance_policy(insurer_id);
CREATE INDEX idx_policy_number     ON insurance_policy(policy_number);
CREATE INDEX idx_policy_status     ON insurance_policy(status);
CREATE INDEX idx_policy_dates      ON insurance_policy(effective_date, expiry_date);

-- -------------------------------------------------------------------------
-- Claim File (Root Aggregate)
-- -------------------------------------------------------------------------
CREATE TABLE claim_file (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_ref          VARCHAR(64) UNIQUE NOT NULL,
    policy_id             UUID REFERENCES insurance_policy(id),
    claim_type_id         UUID NOT NULL REFERENCES claim_type(id),
    date_of_loss          DATE NOT NULL,
    date_received         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    composite_confidence  NUMERIC(5,4) CHECK (composite_confidence BETWEEN 0 AND 1),
    status_id             UUID NOT NULL REFERENCES claim_status(id),
    stp_eligible          BOOLEAN NOT NULL DEFAULT FALSE,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_claim_status_date ON claim_file(status_id, date_received DESC);
CREATE INDEX idx_claim_policy      ON claim_file(policy_id);
CREATE INDEX idx_claim_loss_date   ON claim_file(date_of_loss);
CREATE INDEX idx_claim_stp         ON claim_file(stp_eligible) WHERE stp_eligible = TRUE;

-- -------------------------------------------------------------------------
-- Claim Document (logical document within a claim file)
-- -------------------------------------------------------------------------
CREATE TABLE claim_document (
    id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id                  UUID NOT NULL REFERENCES claim_file(id) ON DELETE CASCADE,
    document_type_id          UUID NOT NULL REFERENCES document_type(id),
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

CREATE INDEX idx_doc_claim    ON claim_document(claim_id);
CREATE INDEX idx_doc_type     ON claim_document(document_type_id);
CREATE INDEX idx_doc_dup      ON claim_document(is_duplicate) WHERE is_duplicate = TRUE;

-- -------------------------------------------------------------------------
-- Document Page (physical page)
-- -------------------------------------------------------------------------
CREATE TABLE document_page (
    id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id              UUID NOT NULL REFERENCES claim_document(id) ON DELETE CASCADE,
    page_number              INTEGER NOT NULL CHECK (page_number >= 1),
    original_page_number     INTEGER NOT NULL CHECK (original_page_number >= 1),
    image_uri                TEXT NOT NULL,
    ocr_hocr_uri             TEXT NOT NULL,
    orientation_corrected_deg INTEGER DEFAULT 0,
    resolution_dpi           INTEGER NOT NULL,
    quality_score            NUMERIC(5,4) CHECK (quality_score BETWEEN 0 AND 1),
    is_missing_detected      BOOLEAN NOT NULL DEFAULT FALSE,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_doc_page UNIQUE (document_id, page_number)
);

CREATE INDEX idx_page_doc     ON document_page(document_id);
CREATE INDEX idx_page_quality ON document_page(quality_score) WHERE quality_score < 0.5;

COMMIT;
