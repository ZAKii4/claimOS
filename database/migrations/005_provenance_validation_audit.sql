-- =============================================================================
-- Migration 005: Provenance, Validation, Audit & Decision Tables
-- Enterprise AI Claims Processing Platform
-- =============================================================================
-- This is the anti-hallucination and governance layer.
-- field_provenance: links every extracted value to its source BBox.
-- validation_decision: STP vs HITL routing.
-- validation_field_flag: specific fields needing human attention.
-- claim_discrepancy: cross-document contradictions.
-- claim_event: immutable audit log of every action.
-- =============================================================================

BEGIN;

-- =========================================================================
-- PROVENANCE (Anti-Hallucination Layer)
-- =========================================================================

CREATE TABLE field_provenance (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_table          VARCHAR(64) NOT NULL,
    entity_id             UUID NOT NULL,
    field_name            VARCHAR(64) NOT NULL,
    confidence            NUMERIC(5,4) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    source_page_id        UUID REFERENCES document_page(id),
    bbox_x1               INTEGER,
    bbox_y1               INTEGER,
    bbox_x2               INTEGER,
    bbox_y2               INTEGER,
    extraction_method_id  UUID NOT NULL REFERENCES extraction_method(id),
    model_version         VARCHAR(32),
    raw_ocr_token         VARCHAR(512),
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- One provenance record per field per entity version
    CONSTRAINT uq_provenance UNIQUE (entity_table, entity_id, field_name),

    -- If bbox is provided, all four coordinates must be present
    CONSTRAINT chk_bbox_complete CHECK (
        (bbox_x1 IS NULL AND bbox_y1 IS NULL AND bbox_x2 IS NULL AND bbox_y2 IS NULL)
        OR
        (bbox_x1 IS NOT NULL AND bbox_y1 IS NOT NULL AND bbox_x2 IS NOT NULL AND bbox_y2 IS NOT NULL)
    ),

    -- BBox coordinates must be valid (x2 > x1, y2 > y1)
    CONSTRAINT chk_bbox_valid CHECK (
        bbox_x1 IS NULL OR (bbox_x2 > bbox_x1 AND bbox_y2 > bbox_y1)
    )
);

CREATE INDEX idx_prov_entity     ON field_provenance(entity_table, entity_id);
CREATE INDEX idx_prov_confidence ON field_provenance(confidence);
CREATE INDEX idx_prov_low_conf   ON field_provenance(confidence) WHERE confidence < 0.85;
CREATE INDEX idx_prov_method     ON field_provenance(extraction_method_id);
CREATE INDEX idx_prov_page       ON field_provenance(source_page_id);

-- =========================================================================
-- VALIDATION & DECISION ENGINE
-- =========================================================================

-- -------------------------------------------------------------------------
-- Validation Decision (STP vs HITL routing)
-- -------------------------------------------------------------------------
CREATE TABLE validation_decision (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id              UUID NOT NULL REFERENCES claim_file(id) ON DELETE CASCADE,
    decision              VARCHAR(16) NOT NULL
                          CHECK (decision IN ('STP_APPROVED','HITL_REVIEW','REJECTED','PENDING_DOCUMENTS')),
    composite_confidence  NUMERIC(5,4) NOT NULL CHECK (composite_confidence BETWEEN 0 AND 1),
    model_version         VARCHAR(32),
    decided_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    decided_by            VARCHAR(16) NOT NULL
                          CHECK (decided_by IN ('AI_ENGINE','HUMAN_OPERATOR')),
    operator_id           UUID REFERENCES operator(id)
);

CREATE INDEX idx_vd_claim    ON validation_decision(claim_id);
CREATE INDEX idx_vd_decision ON validation_decision(decision);
CREATE INDEX idx_vd_date     ON validation_decision(decided_at DESC);

-- -------------------------------------------------------------------------
-- Validation Field Flag (fields requiring human attention)
-- -------------------------------------------------------------------------
CREATE TABLE validation_field_flag (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    decision_id    UUID NOT NULL REFERENCES validation_decision(id) ON DELETE CASCADE,
    entity_table   VARCHAR(64) NOT NULL,
    entity_id      UUID NOT NULL,
    field_name     VARCHAR(64) NOT NULL,
    flag_reason_id UUID NOT NULL REFERENCES flag_reason(id),
    resolved       BOOLEAN NOT NULL DEFAULT FALSE,
    resolved_by    UUID REFERENCES operator(id),
    resolved_at    TIMESTAMPTZ,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_vff_decision   ON validation_field_flag(decision_id);
CREATE INDEX idx_vff_unresolved ON validation_field_flag(flag_reason_id) WHERE resolved = FALSE;
CREATE INDEX idx_vff_entity     ON validation_field_flag(entity_table, entity_id);

-- =========================================================================
-- DISCREPANCIES (Cross-Document Contradictions)
-- =========================================================================

CREATE TABLE claim_discrepancy (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id            UUID NOT NULL REFERENCES claim_file(id) ON DELETE CASCADE,
    discrepancy_type_id UUID NOT NULL REFERENCES discrepancy_type(id),
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

CREATE INDEX idx_disc_claim      ON claim_discrepancy(claim_id);
CREATE INDEX idx_disc_unresolved ON claim_discrepancy(severity) WHERE resolved = FALSE;
CREATE INDEX idx_disc_type       ON claim_discrepancy(discrepancy_type_id);

-- =========================================================================
-- IMMUTABLE AUDIT LOG
-- =========================================================================

CREATE TABLE claim_event (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id      UUID NOT NULL REFERENCES claim_file(id) ON DELETE CASCADE,
    event_type_id UUID NOT NULL REFERENCES event_type(id),
    actor_type    VARCHAR(16) NOT NULL
                  CHECK (actor_type IN ('SYSTEM','AI_AGENT','HUMAN_OPERATOR')),
    actor_id      VARCHAR(64) NOT NULL,
    entity_table  VARCHAR(64),
    entity_id     UUID,
    old_version   INTEGER,
    new_version   INTEGER,
    metadata      JSONB,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- This table is append-only. Prevent updates and deletes at the DB level.
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

CREATE INDEX idx_event_claim     ON claim_event(claim_id, created_at DESC);
CREATE INDEX idx_event_type      ON claim_event(event_type_id);
CREATE INDEX idx_event_actor     ON claim_event(actor_type, actor_id);
CREATE INDEX idx_event_entity    ON claim_event(entity_table, entity_id);

COMMIT;
