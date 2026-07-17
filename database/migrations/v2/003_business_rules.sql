-- =============================================================================
-- Migration 003v2: Business Rules Tables
-- Enterprise AI Claims Processing Platform v2
-- =============================================================================
-- Derived from the Claim Lifecycle & Rules Engine design document.
-- These tables encode the deterministic business logic that must NEVER
-- be delegated to an LLM:
--   - Barème de Responsabilité (liability grid)
--   - Document completeness requirements per claim type
--   - Payment authorization thresholds
--   - Regulatory deadlines
--   - Indemnity reference tables
--
-- All rules are versioned. When FMSAR revises the Barème or the insurer
-- changes thresholds, a new version is created. Old claims reference
-- the rule version that was active at their processing time.
-- =============================================================================

BEGIN;

SET search_path TO platform;

-- =========================================================================
-- EXTENDED CLAIM STATUS (26 states from the lifecycle state machine)
-- =========================================================================
-- The original claim_status table only had 11 states. The domain discovery
-- revealed 26 distinct states. We add the missing ones.

INSERT INTO claim_status (code, is_terminal) VALUES
    ('DECLARED',               FALSE),
    ('POLICY_VERIFICATION',    FALSE),
    ('AWAITING_DOCUMENTS',     FALSE),
    ('REMINDER_SENT',          FALSE),
    ('DOCUMENT_REVIEW',        FALSE),
    ('AI_PROCESSING',          FALSE),
    ('EXTRACTION_COMPLETE',    FALSE),
    ('HUMAN_REVIEW',           FALSE),
    ('FRAUD_INVESTIGATION',    FALSE),
    ('LIABILITY_DETERMINATION', FALSE),
    ('EXPERT_ASSESSMENT',      FALSE),
    ('RESERVE_ESTIMATION',     FALSE),
    ('OFFER_GENERATION',       FALSE),
    ('AWAITING_ACCEPTANCE',    FALSE),
    ('NEGOTIATION',            FALSE),
    ('PAYMENT',                FALSE),
    ('SUBROGATION_CHECK',      FALSE),
    ('RECOVERY',               FALSE),
    ('LITIGATION',             FALSE),
    ('REOPENED',               FALSE),
    ('ABANDONED',              TRUE),
    ('REJECTED_POLICY',        TRUE),
    ('REJECTED_FRAUD',         TRUE)
ON CONFLICT (code) DO NOTHING;

-- Remove the simplified statuses that don't match the real lifecycle
DELETE FROM claim_status WHERE code IN (
    'PREPROCESSING', 'OCR_IN_PROGRESS', 'CLASSIFYING',
    'EXTRACTING', 'VALIDATING', 'AWAITING_REVIEW'
)
AND NOT EXISTS (
    -- Safety: only delete if no claim references them
    SELECT 1 FROM information_schema.tables
    WHERE table_schema LIKE 'tenant_%'
);

-- =========================================================================
-- STATE TRANSITION RULES
-- =========================================================================
-- Defines the legal state transitions. The application and Temporal workflow
-- must enforce these. Any transition not in this table is ILLEGAL.

CREATE TABLE state_transition (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_status_id  UUID NOT NULL REFERENCES claim_status(id),
    to_status_id    UUID NOT NULL REFERENCES claim_status(id),
    guard_condition TEXT,           -- Human-readable condition description
    trigger_type    VARCHAR(16) NOT NULL
                    CHECK (trigger_type IN ('AUTOMATIC','HUMAN','TIMER','SIGNAL')),
    timeout_hours   INTEGER,       -- For TIMER triggers: hours before auto-transition
    timeout_action  VARCHAR(32),   -- What happens on timeout: 'ESCALATE', 'TRANSITION', 'ALERT'
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT uq_transition UNIQUE (from_status_id, to_status_id),
    CONSTRAINT chk_no_self_loop CHECK (from_status_id != to_status_id)
);

CREATE INDEX idx_transition_from ON state_transition(from_status_id);

-- =========================================================================
-- BARÈME DE RESPONSABILITÉ (Liability Decision Table)
-- =========================================================================
-- The Barème maps combinations of Constat Amiable circumstances (checkboxes
-- 1-17) to liability percentages. This is the core of liability determination
-- and MUST be deterministic.
--
-- Each rule has a version so that when FMSAR revises the Barème, we can
-- deploy new rules without affecting claims already processed under the
-- old version.

CREATE TABLE bareme_version (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_code    VARCHAR(16) UNIQUE NOT NULL,   -- e.g., 'BAREME_2025'
    effective_date  DATE NOT NULL,
    end_date        DATE,                           -- NULL = currently active
    source          VARCHAR(256),                   -- 'FMSAR Circular 2025-03'
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_bareme_dates CHECK (end_date IS NULL OR end_date > effective_date)
);

CREATE TABLE bareme_rule (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bareme_version_id     UUID NOT NULL REFERENCES bareme_version(id),
    rule_code             VARCHAR(64) NOT NULL,     -- e.g., 'REAR_END_A1_B8'
    description_fr        TEXT NOT NULL,
    description_ar        TEXT,

    -- Conditions: which circumstances must be checked by Driver A and Driver B
    -- Stored as sorted integer arrays for deterministic matching
    driver_a_circumstances INTEGER[] NOT NULL,      -- e.g., {1} (parked)
    driver_b_circumstances INTEGER[] NOT NULL,      -- e.g., {8} (rear-ended)

    -- Result
    driver_a_liability_pct INTEGER NOT NULL CHECK (driver_a_liability_pct BETWEEN 0 AND 100),
    driver_b_liability_pct INTEGER NOT NULL CHECK (driver_b_liability_pct BETWEEN 0 AND 100),

    -- Confidence
    is_certain             BOOLEAN NOT NULL DEFAULT TRUE,  -- FALSE = requires human review
    priority               INTEGER NOT NULL DEFAULT 0,      -- Higher = evaluated first (for overlapping rules)

    created_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_bareme_rule UNIQUE (bareme_version_id, rule_code),
    CONSTRAINT chk_liability_sum CHECK (driver_a_liability_pct + driver_b_liability_pct = 100
                                        OR (driver_a_liability_pct = 0 AND driver_b_liability_pct = 0))
    -- 0/0 means UNDETERMINED → route to human
);

CREATE INDEX idx_bareme_version ON bareme_rule(bareme_version_id);

-- Seed: illustrative Barème rules (the complete set must come from FMSAR)
INSERT INTO bareme_version (version_code, effective_date, source)
VALUES ('BAREME_2025', '2025-01-01', 'FMSAR – Barème Indicatif – Placeholder pending official source');

INSERT INTO bareme_rule (bareme_version_id, rule_code, description_fr, driver_a_circumstances, driver_b_circumstances, driver_a_liability_pct, driver_b_liability_pct, is_certain, priority)
SELECT bv.id, vals.rule_code, vals.description_fr, vals.a_circ, vals.b_circ, vals.a_pct, vals.b_pct, vals.certain, vals.priority
FROM bareme_version bv
CROSS JOIN (VALUES
    ('REAR_END_BASIC',       'Véhicule A à l''arrêt, heurté à l''arrière par B',      '{1}',    '{8}',    0,   100, TRUE,  10),
    ('LANE_CHANGE',          'Véhicule B changeait de file, collision avec A',          '{9}',    '{10}',   0,   100, TRUE,  10),
    ('OVERTAKE_COLLISION',   'Véhicule B doublait, collision avec A',                   '{9}',    '{11}',   0,   100, TRUE,  10),
    ('REVERSING',            'Véhicule B reculait',                                     '{1}',    '{14}',   0,   100, TRUE,  10),
    ('RIGHT_OF_WAY',         'Véhicule B n''a pas observé le signal de priorité',       '{16}',   '{17}',   0,   100, TRUE,  10),
    ('ROUNDABOUT_ENTRY',     'Véhicule B s''engageait sur rond-point, A y circulait',   '{7}',    '{6}',    0,   100, TRUE,  10),
    ('PARKING_EXIT',         'Véhicule B sortait d''un parking',                        '{1}',    '{4}',    0,   100, TRUE,  10),
    ('MUTUAL_LANE_CHANGE',   'Les deux véhicules changeaient de file',                  '{10}',   '{10}',   50,  50,  TRUE,  5),
    ('MUTUAL_OVERTAKE',      'Les deux véhicules doublaient',                           '{11}',   '{11}',   50,  50,  TRUE,  5),
    ('LEFT_TURN_VS_ONCOMING','A virait à gauche, B en sens inverse',                    '{13}',   '{15}',   50,  50,  FALSE, 3),
    ('HEAD_ON_BOTH_FAULT',   'Les deux véhicules empiétaient',                          '{15}',   '{15}',   50,  50,  TRUE,  5)
) AS vals(rule_code, description_fr, a_circ, b_circ, a_pct, b_pct, certain, priority)
WHERE bv.version_code = 'BAREME_2025';

-- =========================================================================
-- DOCUMENT COMPLETENESS REQUIREMENTS
-- =========================================================================
-- Configurable matrix: which documents are required/optional per claim type.
-- This drives the AWAITING_DOCUMENTS → DOCUMENT_REVIEW transition.

CREATE TABLE document_requirement (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id         UUID REFERENCES tenant(id),   -- NULL = platform default
    claim_type_id     UUID NOT NULL REFERENCES claim_type(id),
    document_type_id  UUID NOT NULL REFERENCES document_type(id),
    is_required       BOOLEAN NOT NULL DEFAULT TRUE,
    requirement_note  TEXT,          -- e.g., 'Required only if bodily injury is claimed'
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_doc_req UNIQUE (tenant_id, claim_type_id, document_type_id)
);

-- Seed: default document requirements for AUTO_LIABILITY
INSERT INTO document_requirement (claim_type_id, document_type_id, is_required, requirement_note)
SELECT ct.id, dt.id, vals.required, vals.note
FROM claim_type ct
CROSS JOIN (VALUES
    ('CONSTAT_AMIABLE',        TRUE,  'Required unless police report is provided'),
    ('IDENTITY_CARD',          TRUE,  NULL),
    ('DRIVING_LICENSE',        TRUE,  NULL),
    ('VEHICLE_REGISTRATION',   TRUE,  NULL),
    ('INSURANCE_ATTESTATION',  TRUE,  NULL),
    ('REPAIR_ESTIMATE',        TRUE,  'Required for property damage'),
    ('POLICE_REPORT',          FALSE, 'Required if no Constat Amiable'),
    ('PHOTO_EVIDENCE',         FALSE, NULL),
    ('EXPERT_REPORT',          FALSE, NULL)
) AS vals(doc_code, required, note)
JOIN document_type dt ON dt.code = vals.doc_code
WHERE ct.code = 'AUTO_LIABILITY';

-- Seed: BODILY_INJURY requires everything AUTO_LIABILITY does + medical docs
INSERT INTO document_requirement (claim_type_id, document_type_id, is_required, requirement_note)
SELECT ct.id, dt.id, vals.required, vals.note
FROM claim_type ct
CROSS JOIN (VALUES
    ('CONSTAT_AMIABLE',        TRUE,  NULL),
    ('IDENTITY_CARD',          TRUE,  NULL),
    ('DRIVING_LICENSE',        TRUE,  NULL),
    ('VEHICLE_REGISTRATION',   TRUE,  NULL),
    ('INSURANCE_ATTESTATION',  TRUE,  NULL),
    ('REPAIR_ESTIMATE',        TRUE,  NULL),
    ('MEDICAL_CERTIFICATE',    TRUE,  'Initial medical certificate mandatory'),
    ('MEDICAL_BILL',           TRUE,  'At least one medical bill required'),
    ('POLICE_REPORT',          FALSE, NULL),
    ('PHOTO_EVIDENCE',         FALSE, NULL),
    ('EXPERT_REPORT',          FALSE, NULL)
) AS vals(doc_code, required, note)
JOIN document_type dt ON dt.code = vals.doc_code
WHERE ct.code = 'BODILY_INJURY';

-- =========================================================================
-- PAYMENT AUTHORIZATION THRESHOLDS
-- =========================================================================
-- Hierarchical approval levels based on payment amount.
-- Configurable per tenant.

CREATE TABLE payment_authority (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id         UUID REFERENCES tenant(id),   -- NULL = platform default
    role_id           UUID NOT NULL REFERENCES operator_role(id),
    max_amount        NUMERIC(14,2) NOT NULL,        -- Maximum amount this role can approve
    currency          CHAR(3) NOT NULL DEFAULT 'MAD',
    requires_cosign   BOOLEAN NOT NULL DEFAULT FALSE, -- Requires a second signature
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_payment_auth UNIQUE (tenant_id, role_id, currency)
);

-- Seed: default Moroccan thresholds
INSERT INTO payment_authority (role_id, max_amount, currency, requires_cosign)
SELECT r.id, vals.max_amt, 'MAD', vals.cosign
FROM operator_role r
JOIN (VALUES
    ('REVIEWER',        10000.00,   FALSE),
    ('SENIOR_REVIEWER', 50000.00,   FALSE),
    ('SUPERVISOR',      500000.00,  TRUE),
    ('ADMIN',           999999999.99, TRUE)
) AS vals(role_code, max_amt, cosign)
ON r.code = vals.role_code;

-- =========================================================================
-- REGULATORY DEADLINES
-- =========================================================================
-- Configurable per country (and overridable per tenant).

CREATE TABLE regulatory_deadline (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id        UUID REFERENCES tenant(id),   -- NULL = platform default
    country_iso      CHAR(2) NOT NULL DEFAULT 'MA',
    claim_type_id    UUID REFERENCES claim_type(id), -- NULL = all claim types
    milestone_code   VARCHAR(48) NOT NULL,
    description_fr   TEXT NOT NULL,
    deadline_days    INTEGER NOT NULL,              -- Calendar days from trigger event
    trigger_event    VARCHAR(48) NOT NULL,          -- What starts the clock
    penalty_desc     TEXT,
    legal_reference  VARCHAR(128),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_deadline UNIQUE (tenant_id, country_iso, claim_type_id, milestone_code)
);

INSERT INTO regulatory_deadline (country_iso, milestone_code, description_fr, deadline_days, trigger_event, legal_reference)
VALUES
    ('MA', 'ACK_RECEIPT',     'Accusé de réception de la déclaration',                10,  'CLAIM_DECLARED',       'Code des Assurances, Art. 18'),
    ('MA', 'DOC_REQUEST',     'Demande de pièces complémentaires',                    15,  'CLAIM_DECLARED',       'Best practice'),
    ('MA', 'OFFER_PROP_DMG',  'Proposition d''indemnisation (dommages matériels)',     60,  'FILE_COMPLETE',        'Code des Assurances, Art. 18'),
    ('MA', 'OFFER_BODILY',    'Proposition d''indemnisation (dommages corporels)',     90,  'FILE_COMPLETE',        'Code des Assurances, Art. 18'),
    ('MA', 'PAYMENT',         'Règlement après acceptation',                           30,  'OFFER_ACCEPTED',       'Code des Assurances, Art. 18'),
    ('MA', 'DECLARATION',     'Délai de déclaration par l''assuré',                    5,   'INCIDENT_DATE',        'Code des Assurances, Art. 20');

-- =========================================================================
-- INDEMNITY REFERENCE TABLES
-- =========================================================================
-- These tables store the actuarial reference data used in bodily injury
-- indemnity calculations. They are versioned for auditability.

CREATE TABLE indemnity_table_version (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_name      VARCHAR(64) NOT NULL,          -- e.g., 'ITT_DAILY_RATE', 'IPP_COEFFICIENT'
    version_code    VARCHAR(16) NOT NULL,
    effective_date  DATE NOT NULL,
    end_date        DATE,
    source          VARCHAR(256),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_indem_version UNIQUE (table_name, version_code)
);

CREATE TABLE indemnity_table_entry (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_version_id  UUID NOT NULL REFERENCES indemnity_table_version(id),
    age_min           INTEGER,       -- Age range (inclusive)
    age_max           INTEGER,
    severity_key      VARCHAR(32),   -- e.g., IPP percentage range: '1-5', '6-10'
    amount            NUMERIC(12,2) NOT NULL,
    currency          CHAR(3) NOT NULL DEFAULT 'MAD',
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_indem_entry_version ON indemnity_table_entry(table_version_id);

COMMIT;
