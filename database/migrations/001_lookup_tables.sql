-- =============================================================================
-- Migration 001: Lookup Tables
-- Enterprise AI Claims Processing Platform
-- =============================================================================
-- These are the foundational reference tables. They must be created first
-- because all domain tables reference them via foreign keys.
-- Lookup tables use UUIDs as PKs and support multilingual labels (fr/ar).
-- =============================================================================

BEGIN;

-- -------------------------------------------------------------------------
-- Claim Type (AUTO_LIABILITY, BODILY_INJURY, PROPERTY_DAMAGE, etc.)
-- -------------------------------------------------------------------------
CREATE TABLE claim_type (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code            VARCHAR(32) UNIQUE NOT NULL,
    label_fr        VARCHAR(128) NOT NULL,
    label_ar        VARCHAR(128) NOT NULL
);

INSERT INTO claim_type (code, label_fr, label_ar) VALUES
    ('AUTO_LIABILITY',   'Responsabilité civile automobile', 'المسؤولية المدنية للسيارات'),
    ('BODILY_INJURY',    'Dommages corporels',               'أضرار جسدية'),
    ('PROPERTY_DAMAGE',  'Dommages matériels',               'أضرار مادية'),
    ('MIXED',            'Dommages corporels et matériels',   'أضرار جسدية ومادية'),
    ('THEFT',            'Vol de véhicule',                   'سرقة مركبة'),
    ('NATURAL_DISASTER', 'Catastrophe naturelle',             'كارثة طبيعية'),
    ('FIRE',             'Incendie',                          'حريق'),
    ('GLASS_BREAKAGE',   'Bris de glace',                     'كسر الزجاج');

-- -------------------------------------------------------------------------
-- Claim Status
-- -------------------------------------------------------------------------
CREATE TABLE claim_status (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code        VARCHAR(32) UNIQUE NOT NULL,
    is_terminal BOOLEAN NOT NULL DEFAULT FALSE
);

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

-- -------------------------------------------------------------------------
-- Document Type
-- -------------------------------------------------------------------------
CREATE TABLE document_type (
    id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code     VARCHAR(48) UNIQUE NOT NULL,
    label_fr VARCHAR(128) NOT NULL,
    label_ar VARCHAR(128) NOT NULL
);

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

-- -------------------------------------------------------------------------
-- Party Role
-- -------------------------------------------------------------------------
CREATE TABLE party_role (
    id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(32) UNIQUE NOT NULL
);

INSERT INTO party_role (code) VALUES
    ('POLICYHOLDER'),
    ('DRIVER'),
    ('VICTIM'),
    ('WITNESS'),
    ('THIRD_PARTY_DRIVER'),
    ('THIRD_PARTY_PASSENGER'),
    ('PEDESTRIAN'),
    ('LEGAL_REPRESENTATIVE'),
    ('BENEFICIARY');

-- -------------------------------------------------------------------------
-- Extraction Method
-- -------------------------------------------------------------------------
CREATE TABLE extraction_method (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code        VARCHAR(48) UNIQUE NOT NULL,
    description TEXT
);

INSERT INTO extraction_method (code, description) VALUES
    ('OCR_DIRECT',              'Value taken directly from OCR token with high confidence.'),
    ('LLM_FUZZY_MATCH',         'LLM output fuzzy-matched back to an OCR token to retrieve BBox.'),
    ('LLM_SEMANTIC_INFERENCE',  'LLM inferred value from surrounding context; no exact OCR token match.'),
    ('VLM_VISUAL_READ',         'Vision-Language Model read directly from the image pixels.'),
    ('HUMAN_MANUAL',            'Value entered or corrected by a human operator.'),
    ('DB_LOOKUP',               'Value enriched from the insurance core database.'),
    ('SUPER_RESOLUTION_OCR',    'OCR applied after Super-Resolution upscaling of a low-res image.'),
    ('DAMAGE_INFERRED',         'Value reconstructed from damaged/torn document by VLM contextual reasoning.');

-- -------------------------------------------------------------------------
-- Event Type (for the immutable audit log)
-- -------------------------------------------------------------------------
CREATE TABLE event_type (
    id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(64) UNIQUE NOT NULL
);

INSERT INTO event_type (code) VALUES
    ('CLAIM_INGESTED'),
    ('DOCUMENT_NORMALIZED'),
    ('DOCUMENT_CLASSIFIED'),
    ('ENTITY_EXTRACTED'),
    ('FIELD_CORRECTED'),
    ('DECISION_RENDERED'),
    ('DECISION_OVERRIDDEN'),
    ('DISCREPANCY_DETECTED'),
    ('DISCREPANCY_RESOLVED'),
    ('CLAIM_VALIDATED'),
    ('CLAIM_REJECTED'),
    ('DOCUMENT_REQUESTED'),
    ('CLAIM_REOPENED'),
    ('OPERATOR_ASSIGNED'),
    ('POLICY_VERIFIED');

-- -------------------------------------------------------------------------
-- Flag Reason (why a field requires human attention)
-- -------------------------------------------------------------------------
CREATE TABLE flag_reason (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code        VARCHAR(48) UNIQUE NOT NULL,
    description TEXT
);

INSERT INTO flag_reason (code, description) VALUES
    ('LOW_CONFIDENCE',   'Extraction confidence below the acceptable threshold.'),
    ('DAMAGE_INFERRED',  'Value was inferred from a damaged region of the document.'),
    ('DB_MISMATCH',      'Extracted value does not match the insurance core database.'),
    ('MISSING_BBOX',     'No bounding box could be assigned; value may be hallucinated.'),
    ('ILLEGIBLE_SOURCE', 'Source region is too degraded for reliable extraction.'),
    ('MULTI_VALUE',      'Multiple conflicting values found for the same field.');

-- -------------------------------------------------------------------------
-- Discrepancy Type
-- -------------------------------------------------------------------------
CREATE TABLE discrepancy_type (
    id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(48) UNIQUE NOT NULL
);

INSERT INTO discrepancy_type (code) VALUES
    ('DATE_CONFLICT'),
    ('LIABILITY_MISMATCH'),
    ('VEHICLE_POLICY_MISMATCH'),
    ('MEDICAL_INCONSISTENCY'),
    ('IDENTITY_MISMATCH'),
    ('AMOUNT_DISCREPANCY'),
    ('DUPLICATE_CLAIM'),
    ('POLICY_EXPIRED_AT_LOSS_DATE');

-- -------------------------------------------------------------------------
-- Damage Zone (normalized vehicle damage locations)
-- -------------------------------------------------------------------------
CREATE TABLE damage_zone (
    id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(48) UNIQUE NOT NULL
);

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

-- -------------------------------------------------------------------------
-- Damage Severity
-- -------------------------------------------------------------------------
CREATE TABLE damage_severity (
    id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(16) UNIQUE NOT NULL
);

INSERT INTO damage_severity (code) VALUES
    ('MINOR'), ('MODERATE'), ('SEVERE'), ('TOTAL_LOSS');

-- -------------------------------------------------------------------------
-- Body Region (for medical findings)
-- -------------------------------------------------------------------------
CREATE TABLE body_region (
    id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(48) UNIQUE NOT NULL
);

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

-- -------------------------------------------------------------------------
-- Injury Type
-- -------------------------------------------------------------------------
CREATE TABLE injury_type (
    id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(32) UNIQUE NOT NULL
);

INSERT INTO injury_type (code) VALUES
    ('FRACTURE'), ('CONTUSION'), ('LACERATION'), ('ABRASION'),
    ('WHIPLASH'), ('DISLOCATION'), ('SPRAIN'), ('CONCUSSION'),
    ('INTERNAL_BLEEDING'), ('BURN'), ('AMPUTATION'), ('PARALYSIS'),
    ('SOFT_TISSUE_INJURY'), ('DENTAL_INJURY'), ('DEATH');

-- -------------------------------------------------------------------------
-- Prognosis
-- -------------------------------------------------------------------------
CREATE TABLE prognosis (
    id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(32) UNIQUE NOT NULL
);

INSERT INTO prognosis (code) VALUES
    ('FULL_RECOVERY'), ('PARTIAL_DISABILITY'), ('PERMANENT_DISABILITY'),
    ('UNDER_TREATMENT'), ('CONSOLIDATION_PENDING');

-- -------------------------------------------------------------------------
-- Weather Condition
-- -------------------------------------------------------------------------
CREATE TABLE weather_condition (
    id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(16) UNIQUE NOT NULL
);

INSERT INTO weather_condition (code) VALUES
    ('CLEAR'), ('RAIN'), ('FOG'), ('SNOW'), ('ICE'), ('WIND'), ('NIGHT'), ('UNKNOWN');

-- -------------------------------------------------------------------------
-- Road Condition
-- -------------------------------------------------------------------------
CREATE TABLE road_condition (
    id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(16) UNIQUE NOT NULL
);

INSERT INTO road_condition (code) VALUES
    ('DRY'), ('WET'), ('ICY'), ('MUDDY'), ('UNDER_CONSTRUCTION'), ('UNKNOWN');

-- -------------------------------------------------------------------------
-- Operator Role
-- -------------------------------------------------------------------------
CREATE TABLE operator_role (
    id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(32) UNIQUE NOT NULL
);

INSERT INTO operator_role (code) VALUES
    ('REVIEWER'), ('SENIOR_REVIEWER'), ('SUPERVISOR'), ('ADMIN'), ('SYSTEM');

-- -------------------------------------------------------------------------
-- Product Type (insurance product)
-- -------------------------------------------------------------------------
CREATE TABLE product_type (
    id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code     VARCHAR(32) UNIQUE NOT NULL,
    label_fr VARCHAR(128) NOT NULL,
    label_ar VARCHAR(128) NOT NULL
);

INSERT INTO product_type (code, label_fr, label_ar) VALUES
    ('AUTO_TPL',           'Responsabilité civile auto',       'المسؤولية المدنية للسيارات'),
    ('AUTO_COMPREHENSIVE', 'Tous risques auto',                'جميع المخاطر للسيارات'),
    ('AUTO_FIRE_THEFT',    'Incendie et vol auto',             'حريق وسرقة السيارات'),
    ('FLEET',              'Flotte automobile',                'أسطول السيارات');

-- -------------------------------------------------------------------------
-- Insurer
-- -------------------------------------------------------------------------
CREATE TABLE insurer (
    id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code     VARCHAR(16) UNIQUE NOT NULL,
    name     VARCHAR(256) NOT NULL,
    country  CHAR(2) NOT NULL DEFAULT 'MA'
);

COMMIT;
