-- =============================================================================
-- Migration 003: Parties & Vehicles (with Temporal Versioning)
-- Enterprise AI Claims Processing Platform
-- =============================================================================
-- Every mutable entity uses a _version pattern:
--   - The "header" table (claim_party, claim_vehicle) is the stable identity.
--   - The "_version" table stores every state change as a new immutable row.
--   - Only one row per entity has is_current = TRUE, enforced by a partial index.
-- =============================================================================

BEGIN;

-- =========================================================================
-- PARTIES
-- =========================================================================

-- -------------------------------------------------------------------------
-- Claim Party (stable identity)
-- -------------------------------------------------------------------------
CREATE TABLE claim_party (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id   UUID NOT NULL REFERENCES claim_file(id) ON DELETE CASCADE,
    role_id    UUID NOT NULL REFERENCES party_role(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_party_claim ON claim_party(claim_id);
CREATE INDEX idx_party_role  ON claim_party(role_id);

-- Now add the deferred FK from insurance_policy
ALTER TABLE insurance_policy
    ADD CONSTRAINT fk_policy_holder
    FOREIGN KEY (policyholder_party_id) REFERENCES claim_party(id);

-- -------------------------------------------------------------------------
-- Party Version (temporal versioning)
-- -------------------------------------------------------------------------
CREATE TABLE party_version (
    id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    party_id               UUID NOT NULL REFERENCES claim_party(id) ON DELETE CASCADE,
    version                INTEGER NOT NULL CHECK (version >= 1),
    is_current             BOOLEAN NOT NULL DEFAULT TRUE,
    origin                 VARCHAR(16) NOT NULL
                           CHECK (origin IN ('AI_EXTRACTION','HUMAN_CORRECTION','DB_ENRICHMENT')),
    operator_id            UUID REFERENCES operator(id),

    -- Typed, normalized fields — never raw text blobs
    last_name              VARCHAR(128),
    first_name             VARCHAR(128),
    date_of_birth          DATE,
    national_id            VARCHAR(32),
    phone                  VARCHAR(24),
    address_line_1         VARCHAR(256),
    address_city           VARCHAR(128),
    address_postal_code    VARCHAR(16),
    address_country_iso    CHAR(2),
    driving_license_number VARCHAR(32),
    driving_license_category VARCHAR(8),

    created_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_party_version UNIQUE (party_id, version)
);

-- Enforce exactly one current version per party
CREATE UNIQUE INDEX idx_party_current
    ON party_version(party_id)
    WHERE is_current = TRUE;

CREATE INDEX idx_party_ver_origin ON party_version(origin);

-- =========================================================================
-- VEHICLES
-- =========================================================================

-- -------------------------------------------------------------------------
-- Claim Vehicle (stable identity)
-- -------------------------------------------------------------------------
CREATE TABLE claim_vehicle (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id           UUID NOT NULL REFERENCES claim_file(id) ON DELETE CASCADE,
    party_id           UUID REFERENCES claim_party(id),
    is_insured_vehicle BOOLEAN NOT NULL DEFAULT FALSE,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_vehicle_claim ON claim_vehicle(claim_id);
CREATE INDEX idx_vehicle_party ON claim_vehicle(party_id);

-- -------------------------------------------------------------------------
-- Vehicle Version (temporal versioning)
-- -------------------------------------------------------------------------
CREATE TABLE vehicle_version (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vehicle_id         UUID NOT NULL REFERENCES claim_vehicle(id) ON DELETE CASCADE,
    version            INTEGER NOT NULL CHECK (version >= 1),
    is_current         BOOLEAN NOT NULL DEFAULT TRUE,
    origin             VARCHAR(16) NOT NULL
                       CHECK (origin IN ('AI_EXTRACTION','HUMAN_CORRECTION','DB_ENRICHMENT')),
    operator_id        UUID REFERENCES operator(id),

    -- Typed, normalized fields
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

-- Enforce exactly one current version per vehicle
CREATE UNIQUE INDEX idx_vehicle_current
    ON vehicle_version(vehicle_id)
    WHERE is_current = TRUE;

-- -------------------------------------------------------------------------
-- Vehicle Damage
-- -------------------------------------------------------------------------
CREATE TABLE vehicle_damage (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vehicle_id       UUID NOT NULL REFERENCES claim_vehicle(id) ON DELETE CASCADE,
    damage_zone_id   UUID NOT NULL REFERENCES damage_zone(id),
    severity_id      UUID NOT NULL REFERENCES damage_severity(id),
    description      TEXT,
    estimated_cost   NUMERIC(12,2),
    currency         CHAR(3) NOT NULL DEFAULT 'MAD',
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_damage_vehicle ON vehicle_damage(vehicle_id);

COMMIT;
