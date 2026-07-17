-- =============================================================================
-- Migration 000: Platform Schema (Shared Cross-Tenant)
-- Enterprise AI Claims Processing Platform v2
-- =============================================================================
-- This schema is SHARED across all tenants. It contains:
--   - Tenant registry and configuration
--   - All lookup/reference tables (moved from tenant scope)
--   - Workflow definitions
--   - Model registry
--   - Extraction templates
--
-- IMPORTANT: All lookup tables live here because they are identical across
-- tenants. Duplicating them per-tenant wastes space and complicates updates
-- (e.g., adding a new document_type requires N migrations instead of 1).
-- =============================================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS platform;
SET search_path TO platform;

-- =========================================================================
-- TENANT MANAGEMENT
-- =========================================================================

CREATE TABLE tenant (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code            VARCHAR(32) UNIQUE NOT NULL,  -- e.g., 'acme_insurance'
    name            VARCHAR(256) NOT NULL,
    country_iso     CHAR(2) NOT NULL DEFAULT 'MA',
    schema_name     VARCHAR(64) UNIQUE NOT NULL,  -- e.g., 'tenant_acme'
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    config          JSONB NOT NULL DEFAULT '{}',   -- tenant-specific overrides
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Tenant-specific configuration (normalized, not dumped into JSONB)
CREATE TABLE tenant_config (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id               UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    stp_confidence_threshold NUMERIC(5,4) NOT NULL DEFAULT 0.9500,
    max_hitl_queue_depth    INTEGER NOT NULL DEFAULT 500,
    llm_routing_policy      VARCHAR(16) NOT NULL DEFAULT 'HYBRID'
                            CHECK (llm_routing_policy IN ('CLOUD_ONLY','ONPREM_ONLY','HYBRID')),
    requires_pii_tokenization BOOLEAN NOT NULL DEFAULT TRUE,
    data_residency_region   VARCHAR(16) NOT NULL DEFAULT 'MA',
    daily_token_budget      INTEGER NOT NULL DEFAULT 10000000,  -- 10M tokens
    retention_days_hot      INTEGER NOT NULL DEFAULT 90,
    retention_days_cold     INTEGER NOT NULL DEFAULT 2555,      -- 7 years (regulatory)
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_tenant_config UNIQUE (tenant_id)
);

-- =========================================================================
-- WORKFLOW DEFINITIONS (Tenant-Configurable Pipelines)
-- =========================================================================

CREATE TABLE workflow_definition (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID REFERENCES tenant(id),  -- NULL = platform default
    claim_type_code VARCHAR(32) NOT NULL,         -- matches claim_type.code
    name            VARCHAR(128) NOT NULL,
    version         INTEGER NOT NULL DEFAULT 1,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    -- Steps are ordered. Each step maps to a Temporal Activity.
    steps           JSONB NOT NULL,
    -- Example steps JSONB:
    -- [
    --   {"order": 1, "activity": "IngestAndNormalize", "retry_max": 3, "timeout_sec": 60},
    --   {"order": 2, "activity": "RunOCR", "retry_max": 3, "timeout_sec": 120},
    --   {"order": 3, "activity": "ClassifyDocuments", "retry_max": 2, "timeout_sec": 30},
    --   {"order": 4, "activity": "ExtractEntities", "retry_max": 2, "timeout_sec": 300},
    --   {"order": 5, "activity": "ValidateAgainstDB", "retry_max": 3, "timeout_sec": 60},
    --   {"order": 6, "activity": "ComputeConfidence", "retry_max": 1, "timeout_sec": 10},
    --   {"order": 7, "activity": "RouteDecision", "retry_max": 1, "timeout_sec": 10}
    -- ]
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_workflow_version UNIQUE (tenant_id, claim_type_code, version)
);

-- =========================================================================
-- MODEL REGISTRY (Tracking All Deployed AI Models)
-- =========================================================================

CREATE TABLE model_registry (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name      VARCHAR(128) NOT NULL,         -- e.g., 'doctr-arabic-handwritten'
    model_version   VARCHAR(32) NOT NULL,           -- e.g., 'v2.1.3'
    model_type      VARCHAR(32) NOT NULL
                    CHECK (model_type IN (
                        'OCR', 'LAYOUT', 'CLASSIFIER', 'OBJECT_DETECTION',
                        'LLM', 'NER', 'SUPER_RESOLUTION', 'SCORING'
                    )),
    provider        VARCHAR(32) NOT NULL,           -- 'SELF_HOSTED', 'GOOGLE', 'ANTHROPIC', 'META'
    status          VARCHAR(16) NOT NULL DEFAULT 'STAGING'
                    CHECK (status IN ('STAGING','CANARY','PRODUCTION','DEPRECATED','RETIRED')),
    artifact_uri    TEXT,                            -- MLflow / S3 path to model weights
    metrics         JSONB,                          -- {"accuracy": 0.94, "f1": 0.92, "latency_p99_ms": 1200}
    promoted_at     TIMESTAMPTZ,
    promoted_by     VARCHAR(64),                    -- operator or 'AUTO_PROMOTION'
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_model_version UNIQUE (model_name, model_version)
);

-- =========================================================================
-- EXTRACTION TEMPLATES (For Known Document Formats)
-- =========================================================================
-- When the classifier recognizes a known template (e.g., a specific insurer's
-- "Constat Amiable" form), we can skip the expensive LLM and use deterministic
-- field extraction based on known coordinates. This is a massive cost saver.

CREATE TABLE extraction_template (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id         UUID REFERENCES tenant(id),   -- NULL = cross-tenant
    document_type_id  UUID NOT NULL REFERENCES document_type(id),
    template_name     VARCHAR(128) NOT NULL,
    template_version  INTEGER NOT NULL DEFAULT 1,
    is_active         BOOLEAN NOT NULL DEFAULT TRUE,
    -- Field mappings: known field names and their expected BBox regions
    field_mappings    JSONB NOT NULL,
    -- Example:
    -- [
    --   {"field": "policy_number", "bbox": [120, 45, 310, 65], "type": "TEXT"},
    --   {"field": "date_of_loss", "bbox": [400, 45, 550, 65], "type": "DATE"},
    --   {"field": "vehicle_a_plate", "bbox": [80, 200, 250, 225], "type": "TEXT"}
    -- ]
    match_confidence_threshold NUMERIC(5,4) NOT NULL DEFAULT 0.9500,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_template_version UNIQUE (tenant_id, document_type_id, template_name, template_version)
);

-- =========================================================================
-- ALL LOOKUP TABLES (Moved from tenant scope to platform scope)
-- =========================================================================

CREATE TABLE claim_type (
    id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code     VARCHAR(32) UNIQUE NOT NULL,
    label_fr VARCHAR(128) NOT NULL,
    label_ar VARCHAR(128) NOT NULL
);

CREATE TABLE claim_status (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code        VARCHAR(32) UNIQUE NOT NULL,
    is_terminal BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE document_type (
    id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code     VARCHAR(48) UNIQUE NOT NULL,
    label_fr VARCHAR(128) NOT NULL,
    label_ar VARCHAR(128) NOT NULL
);

CREATE TABLE party_role (
    id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(32) UNIQUE NOT NULL
);

CREATE TABLE extraction_method (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code        VARCHAR(48) UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE event_type (
    id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(64) UNIQUE NOT NULL
);

CREATE TABLE flag_reason (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code        VARCHAR(48) UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE discrepancy_type (
    id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(48) UNIQUE NOT NULL
);

CREATE TABLE damage_zone (
    id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(48) UNIQUE NOT NULL
);

CREATE TABLE damage_severity (
    id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(16) UNIQUE NOT NULL
);

CREATE TABLE body_region (
    id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(48) UNIQUE NOT NULL
);

CREATE TABLE injury_type (
    id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(32) UNIQUE NOT NULL
);

CREATE TABLE prognosis (
    id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(32) UNIQUE NOT NULL
);

CREATE TABLE weather_condition (
    id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(16) UNIQUE NOT NULL
);

CREATE TABLE road_condition (
    id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(16) UNIQUE NOT NULL
);

CREATE TABLE operator_role (
    id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(32) UNIQUE NOT NULL
);

CREATE TABLE product_type (
    id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code     VARCHAR(32) UNIQUE NOT NULL,
    label_fr VARCHAR(128) NOT NULL,
    label_ar VARCHAR(128) NOT NULL
);

CREATE TABLE insurer (
    id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code    VARCHAR(16) UNIQUE NOT NULL,
    name    VARCHAR(256) NOT NULL,
    country CHAR(2) NOT NULL DEFAULT 'MA'
);

-- =========================================================================
-- SEED DATA (same as v1, now in platform schema)
-- =========================================================================

INSERT INTO claim_type (code, label_fr, label_ar) VALUES
    ('AUTO_LIABILITY',   'Responsabilité civile automobile', 'المسؤولية المدنية للسيارات'),
    ('BODILY_INJURY',    'Dommages corporels',               'أضرار جسدية'),
    ('PROPERTY_DAMAGE',  'Dommages matériels',               'أضرار مادية'),
    ('MIXED',            'Dommages corporels et matériels',   'أضرار جسدية ومادية'),
    ('THEFT',            'Vol de véhicule',                   'سرقة مركبة'),
    ('NATURAL_DISASTER', 'Catastrophe naturelle',             'كارثة طبيعية'),
    ('FIRE',             'Incendie',                          'حريق'),
    ('GLASS_BREAKAGE',   'Bris de glace',                     'كسر الزجاج');

INSERT INTO claim_status (code, is_terminal) VALUES
    ('INGESTED',          FALSE),
    ('PREPROCESSING',     FALSE),
    ('OCR_IN_PROGRESS',   FALSE),
    ('CLASSIFYING',       FALSE),
    ('EXTRACTING',        FALSE),
    ('VALIDATING',        FALSE),
    ('AWAITING_REVIEW',   FALSE),
    ('PENDING_DOCUMENTS', FALSE),
    ('VALIDATED',         TRUE),
    ('REJECTED',          TRUE),
    ('ARCHIVED',          TRUE);

INSERT INTO document_type (code, label_fr, label_ar) VALUES
    ('POLICE_REPORT',           'Procès-verbal de police',        'محضر الشرطة'),
    ('CONSTAT_AMIABLE',         'Constat amiable',                 'التقرير الودي'),
    ('MEDICAL_CERTIFICATE',     'Certificat médical',              'شهادة طبية'),
    ('MEDICAL_BILL',            'Facture médicale',                'فاتورة طبية'),
    ('REPAIR_ESTIMATE',         'Devis de réparation',             'تقدير الإصلاح'),
    ('REPAIR_INVOICE',          'Facture de réparation',           'فاتورة الإصلاح'),
    ('IDENTITY_CARD',           'Carte d''identité nationale',     'بطاقة التعريف الوطنية'),
    ('DRIVING_LICENSE',         'Permis de conduire',              'رخصة السياقة'),
    ('VEHICLE_REGISTRATION',    'Carte grise',                     'البطاقة الرمادية'),
    ('INSURANCE_ATTESTATION',   'Attestation d''assurance',        'شهادة التأمين'),
    ('EXPERT_REPORT',           'Rapport d''expertise',            'تقرير الخبرة'),
    ('DELEGATION_OF_AUTHORITY', 'Procuration',                     'توكيل'),
    ('PHOTO_EVIDENCE',          'Photo de preuve',                 'صورة إثبات'),
    ('CORRESPONDENCE',          'Correspondance',                  'مراسلة'),
    ('OTHER',                   'Autre document',                  'وثيقة أخرى');

INSERT INTO party_role (code) VALUES
    ('POLICYHOLDER'), ('DRIVER'), ('VICTIM'), ('WITNESS'),
    ('THIRD_PARTY_DRIVER'), ('THIRD_PARTY_PASSENGER'),
    ('PEDESTRIAN'), ('LEGAL_REPRESENTATIVE'), ('BENEFICIARY');

INSERT INTO extraction_method (code, description) VALUES
    ('OCR_DIRECT',              'Value taken directly from OCR token with high confidence.'),
    ('LLM_FUZZY_MATCH',         'LLM output fuzzy-matched back to an OCR token to retrieve BBox.'),
    ('LLM_SEMANTIC_INFERENCE',  'LLM inferred value from surrounding context; no exact OCR token match.'),
    ('VLM_VISUAL_READ',         'Vision-Language Model read directly from the image pixels.'),
    ('HUMAN_MANUAL',            'Value entered or corrected by a human operator.'),
    ('DB_LOOKUP',               'Value enriched from the insurance core database.'),
    ('SUPER_RESOLUTION_OCR',    'OCR applied after Super-Resolution upscaling of a low-res image.'),
    ('DAMAGE_INFERRED',         'Value reconstructed from damaged/torn document by VLM contextual reasoning.'),
    ('TEMPLATE_EXTRACTION',     'Value extracted via known template field coordinates (no LLM needed).');

INSERT INTO event_type (code) VALUES
    ('CLAIM_INGESTED'), ('DOCUMENT_NORMALIZED'), ('DOCUMENT_CLASSIFIED'),
    ('ENTITY_EXTRACTED'), ('FIELD_CORRECTED'), ('DECISION_RENDERED'),
    ('DECISION_OVERRIDDEN'), ('DISCREPANCY_DETECTED'), ('DISCREPANCY_RESOLVED'),
    ('CLAIM_VALIDATED'), ('CLAIM_REJECTED'), ('DOCUMENT_REQUESTED'),
    ('CLAIM_REOPENED'), ('OPERATOR_ASSIGNED'), ('POLICY_VERIFIED'),
    ('PII_ACCESS_LOGGED'), ('MODEL_PROMOTED'), ('WORKFLOW_STEP_COMPLETED'),
    ('WORKFLOW_STEP_FAILED'), ('WORKFLOW_STEP_RETRIED');

INSERT INTO flag_reason (code, description) VALUES
    ('LOW_CONFIDENCE',   'Extraction confidence below the acceptable threshold.'),
    ('DAMAGE_INFERRED',  'Value was inferred from a damaged region of the document.'),
    ('DB_MISMATCH',      'Extracted value does not match the insurance core database.'),
    ('MISSING_BBOX',     'No bounding box could be assigned; value may be hallucinated.'),
    ('ILLEGIBLE_SOURCE', 'Source region is too degraded for reliable extraction.'),
    ('MULTI_VALUE',      'Multiple conflicting values found for the same field.');

INSERT INTO discrepancy_type (code) VALUES
    ('DATE_CONFLICT'), ('LIABILITY_MISMATCH'), ('VEHICLE_POLICY_MISMATCH'),
    ('MEDICAL_INCONSISTENCY'), ('IDENTITY_MISMATCH'), ('AMOUNT_DISCREPANCY'),
    ('DUPLICATE_CLAIM'), ('POLICY_EXPIRED_AT_LOSS_DATE');

INSERT INTO damage_zone (code) VALUES
    ('FRONT_BUMPER'), ('REAR_BUMPER'),
    ('FRONT_LEFT_FENDER'), ('FRONT_RIGHT_FENDER'),
    ('REAR_LEFT_FENDER'), ('REAR_RIGHT_FENDER'),
    ('FRONT_LEFT_DOOR'), ('FRONT_RIGHT_DOOR'),
    ('REAR_LEFT_DOOR'), ('REAR_RIGHT_DOOR'),
    ('HOOD'), ('TRUNK'), ('ROOF'),
    ('WINDSHIELD'), ('REAR_WINDOW'),
    ('LEFT_MIRROR'), ('RIGHT_MIRROR'),
    ('LEFT_HEADLIGHT'), ('RIGHT_HEADLIGHT'),
    ('LEFT_TAILLIGHT'), ('RIGHT_TAILLIGHT'),
    ('CHASSIS'), ('ENGINE'), ('TOTAL_LOSS');

INSERT INTO damage_severity (code) VALUES
    ('MINOR'), ('MODERATE'), ('SEVERE'), ('TOTAL_LOSS');

INSERT INTO body_region (code) VALUES
    ('HEAD'), ('FACE'), ('CERVICAL_SPINE'), ('THORACIC_SPINE'),
    ('LUMBAR_SPINE'), ('CHEST'), ('ABDOMEN'), ('PELVIS'),
    ('LEFT_SHOULDER'), ('RIGHT_SHOULDER'),
    ('LEFT_ARM'), ('RIGHT_ARM'),
    ('LEFT_FOREARM'), ('RIGHT_FOREARM'),
    ('LEFT_HAND'), ('RIGHT_HAND'),
    ('LEFT_HIP'), ('RIGHT_HIP'),
    ('LEFT_THIGH'), ('RIGHT_THIGH'),
    ('LEFT_KNEE'), ('RIGHT_KNEE'),
    ('LEFT_LEG'), ('RIGHT_LEG'),
    ('LEFT_ANKLE'), ('RIGHT_ANKLE'),
    ('LEFT_FOOT'), ('RIGHT_FOOT'),
    ('MULTIPLE_REGIONS');

INSERT INTO injury_type (code) VALUES
    ('FRACTURE'), ('CONTUSION'), ('LACERATION'), ('ABRASION'),
    ('WHIPLASH'), ('DISLOCATION'), ('SPRAIN'), ('CONCUSSION'),
    ('INTERNAL_BLEEDING'), ('BURN'), ('AMPUTATION'), ('PARALYSIS'),
    ('SOFT_TISSUE_INJURY'), ('DENTAL_INJURY'), ('DEATH');

INSERT INTO prognosis (code) VALUES
    ('FULL_RECOVERY'), ('PARTIAL_DISABILITY'), ('PERMANENT_DISABILITY'),
    ('UNDER_TREATMENT'), ('CONSOLIDATION_PENDING');

INSERT INTO weather_condition (code) VALUES
    ('CLEAR'), ('RAIN'), ('FOG'), ('SNOW'), ('ICE'), ('WIND'), ('NIGHT'), ('UNKNOWN');

INSERT INTO road_condition (code) VALUES
    ('DRY'), ('WET'), ('ICY'), ('MUDDY'), ('UNDER_CONSTRUCTION'), ('UNKNOWN');

INSERT INTO operator_role (code) VALUES
    ('REVIEWER'), ('SENIOR_REVIEWER'), ('SUPERVISOR'), ('ADMIN'), ('SYSTEM');

INSERT INTO product_type (code, label_fr, label_ar) VALUES
    ('AUTO_TPL',           'Responsabilité civile auto',       'المسؤولية المدنية للسيارات'),
    ('AUTO_COMPREHENSIVE', 'Tous risques auto',                'جميع المخاطر للسيارات'),
    ('AUTO_FIRE_THEFT',    'Incendie et vol auto',             'حريق وسرقة السيارات'),
    ('FLEET',              'Flotte automobile',                'أسطول السيارات');

COMMIT;
