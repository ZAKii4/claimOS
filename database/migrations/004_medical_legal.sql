-- =============================================================================
-- Migration 004: Medical & Legal Domain Tables
-- Enterprise AI Claims Processing Platform
-- =============================================================================
-- Medical certificates, findings, police reports, and party statements.
-- All with temporal versioning following the same pattern as parties/vehicles.
-- =============================================================================

BEGIN;

-- =========================================================================
-- MEDICAL
-- =========================================================================

-- -------------------------------------------------------------------------
-- Medical Certificate (stable identity)
-- -------------------------------------------------------------------------
CREATE TABLE medical_certificate (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id    UUID NOT NULL REFERENCES claim_file(id) ON DELETE CASCADE,
    party_id    UUID NOT NULL REFERENCES claim_party(id),
    document_id UUID NOT NULL REFERENCES claim_document(id),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_medcert_claim ON medical_certificate(claim_id);
CREATE INDEX idx_medcert_party ON medical_certificate(party_id);

-- -------------------------------------------------------------------------
-- Medical Certificate Version (temporal versioning)
-- -------------------------------------------------------------------------
CREATE TABLE medical_cert_version (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    certificate_id          UUID NOT NULL REFERENCES medical_certificate(id) ON DELETE CASCADE,
    version                 INTEGER NOT NULL CHECK (version >= 1),
    is_current              BOOLEAN NOT NULL DEFAULT TRUE,
    origin                  VARCHAR(16) NOT NULL
                            CHECK (origin IN ('AI_EXTRACTION','HUMAN_CORRECTION','DB_ENRICHMENT')),
    operator_id             UUID REFERENCES operator(id),

    -- Typed, normalized fields
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
    ON medical_cert_version(certificate_id)
    WHERE is_current = TRUE;

-- -------------------------------------------------------------------------
-- Medical Finding (normalized diagnoses and injuries)
-- -------------------------------------------------------------------------
CREATE TABLE medical_finding (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    certificate_id  UUID NOT NULL REFERENCES medical_certificate(id) ON DELETE CASCADE,
    icd10_code      VARCHAR(8),
    body_region_id  UUID REFERENCES body_region(id),
    injury_type_id  UUID REFERENCES injury_type(id),
    prognosis_id    UUID REFERENCES prognosis(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_finding_cert    ON medical_finding(certificate_id);
CREATE INDEX idx_finding_icd10   ON medical_finding(icd10_code) WHERE icd10_code IS NOT NULL;
CREATE INDEX idx_finding_injury  ON medical_finding(injury_type_id);

-- =========================================================================
-- POLICE REPORT
-- =========================================================================

-- -------------------------------------------------------------------------
-- Police Report (stable identity)
-- -------------------------------------------------------------------------
CREATE TABLE police_report (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id    UUID NOT NULL REFERENCES claim_file(id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES claim_document(id),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_pr_claim ON police_report(claim_id);

-- -------------------------------------------------------------------------
-- Police Report Version (temporal versioning)
-- -------------------------------------------------------------------------
CREATE TABLE police_report_version (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id             UUID NOT NULL REFERENCES police_report(id) ON DELETE CASCADE,
    version               INTEGER NOT NULL CHECK (version >= 1),
    is_current            BOOLEAN NOT NULL DEFAULT TRUE,
    origin                VARCHAR(16) NOT NULL
                          CHECK (origin IN ('AI_EXTRACTION','HUMAN_CORRECTION','DB_ENRICHMENT')),
    operator_id           UUID REFERENCES operator(id),

    -- Typed, normalized fields
    report_number         VARCHAR(64),
    report_date           DATE,
    station_name          VARCHAR(256),
    accident_location     VARCHAR(512),
    accident_datetime     TIMESTAMPTZ,
    weather_condition_id  UUID REFERENCES weather_condition(id),
    road_condition_id     UUID REFERENCES road_condition(id),
    liability_split_json  JSONB,
    alcohol_test_result   VARCHAR(16)
                          CHECK (alcohol_test_result IN ('POSITIVE','NEGATIVE','NOT_TESTED')),

    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_pr_version UNIQUE (report_id, version)
);

CREATE UNIQUE INDEX idx_pr_current
    ON police_report_version(report_id)
    WHERE is_current = TRUE;

-- -------------------------------------------------------------------------
-- Police Party Statement
-- -------------------------------------------------------------------------
CREATE TABLE police_party_statement (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id               UUID NOT NULL REFERENCES police_report(id) ON DELETE CASCADE,
    party_id                UUID NOT NULL REFERENCES claim_party(id),
    statement_summary       TEXT,
    is_consistent_with_facts BOOLEAN,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_pps_report ON police_party_statement(report_id);
CREATE INDEX idx_pps_party  ON police_party_statement(party_id);

COMMIT;
