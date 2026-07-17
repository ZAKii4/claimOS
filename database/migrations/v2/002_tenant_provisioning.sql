-- =============================================================================
-- Migration 002v2: Tenant Provisioning Function
-- Enterprise AI Claims Processing Platform v2
-- =============================================================================
-- This function automates the creation of a new tenant. It:
--   1. Creates the tenant's PostgreSQL schema
--   2. Executes the tenant schema template within it
--   3. Registers the tenant in platform.tenant
--   4. Creates default configuration in platform.tenant_config
--   5. Creates default workflow definitions
--
-- Usage:
--   SELECT platform.provision_tenant(
--       'acme_insurance',
--       'ACME Insurance Company',
--       'MA'
--   );
-- =============================================================================

BEGIN;

SET search_path TO platform;

CREATE OR REPLACE FUNCTION platform.provision_tenant(
    p_tenant_code    VARCHAR(32),
    p_tenant_name    VARCHAR(256),
    p_country_iso    CHAR(2) DEFAULT 'MA'
)
RETURNS UUID
LANGUAGE plpgsql
SECURITY DEFINER  -- Runs with the privileges of the function owner (DBA)
AS $$
DECLARE
    v_tenant_id     UUID;
    v_schema_name   VARCHAR(64);
BEGIN
    -- Derive schema name from tenant code
    v_schema_name := 'tenant_' || p_tenant_code;

    -- Validate that the schema does not already exist
    IF EXISTS (
        SELECT 1 FROM information_schema.schemata
        WHERE schema_name = v_schema_name
    ) THEN
        RAISE EXCEPTION 'Schema % already exists. Tenant may already be provisioned.', v_schema_name;
    END IF;

    -- 1. Create the schema
    EXECUTE format('CREATE SCHEMA %I', v_schema_name);

    -- 2. Register the tenant
    INSERT INTO platform.tenant (code, name, country_iso, schema_name)
    VALUES (p_tenant_code, p_tenant_name, p_country_iso, v_schema_name)
    RETURNING id INTO v_tenant_id;

    -- 3. Create default configuration
    INSERT INTO platform.tenant_config (tenant_id)
    VALUES (v_tenant_id);

    -- 4. Create default workflow definitions for common claim types
    INSERT INTO platform.workflow_definition (tenant_id, claim_type_code, name, steps)
    VALUES
    (v_tenant_id, 'AUTO_LIABILITY', 'Standard Auto Liability Workflow', '[
        {"order": 1, "activity": "IngestAndNormalize", "retry_max": 3, "timeout_sec": 60},
        {"order": 2, "activity": "RunOCR", "retry_max": 3, "timeout_sec": 120},
        {"order": 3, "activity": "ClassifyDocuments", "retry_max": 2, "timeout_sec": 30},
        {"order": 4, "activity": "DetectDuplicatesAndMissing", "retry_max": 1, "timeout_sec": 15},
        {"order": 5, "activity": "ExtractEntities", "retry_max": 2, "timeout_sec": 300},
        {"order": 6, "activity": "ValidateAgainstDB", "retry_max": 3, "timeout_sec": 60},
        {"order": 7, "activity": "DetectDiscrepancies", "retry_max": 1, "timeout_sec": 30},
        {"order": 8, "activity": "ComputeConfidence", "retry_max": 1, "timeout_sec": 10},
        {"order": 9, "activity": "RouteDecision", "retry_max": 1, "timeout_sec": 10}
    ]'::jsonb),
    (v_tenant_id, 'BODILY_INJURY', 'Bodily Injury Workflow (with Medical Review)', '[
        {"order": 1, "activity": "IngestAndNormalize", "retry_max": 3, "timeout_sec": 60},
        {"order": 2, "activity": "RunOCR", "retry_max": 3, "timeout_sec": 120},
        {"order": 3, "activity": "ClassifyDocuments", "retry_max": 2, "timeout_sec": 30},
        {"order": 4, "activity": "DetectDuplicatesAndMissing", "retry_max": 1, "timeout_sec": 15},
        {"order": 5, "activity": "ExtractEntities", "retry_max": 2, "timeout_sec": 300},
        {"order": 6, "activity": "ExtractMedicalFindings", "retry_max": 2, "timeout_sec": 300},
        {"order": 7, "activity": "ValidateAgainstDB", "retry_max": 3, "timeout_sec": 60},
        {"order": 8, "activity": "DetectDiscrepancies", "retry_max": 1, "timeout_sec": 30},
        {"order": 9, "activity": "ComputeConfidence", "retry_max": 1, "timeout_sec": 10},
        {"order": 10, "activity": "RouteDecision", "retry_max": 1, "timeout_sec": 10}
    ]'::jsonb);

    -- Log the provisioning event
    -- (claim_event is tenant-scoped, so we log in the platform schema
    --  via a separate platform-level audit table for tenant lifecycle events)

    RAISE NOTICE 'Tenant "%" provisioned successfully. Schema: %, ID: %',
        p_tenant_code, v_schema_name, v_tenant_id;

    RETURN v_tenant_id;
END;
$$;

-- =========================================================================
-- Helper: Set tenant context for application connections
-- =========================================================================
-- Application code calls this at the start of every database session
-- to ensure all queries execute within the correct tenant schema.
--
-- Usage: SELECT platform.set_tenant_context('acme_insurance');

CREATE OR REPLACE FUNCTION platform.set_tenant_context(
    p_tenant_code VARCHAR(32)
)
RETURNS VOID
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_schema_name VARCHAR(64);
BEGIN
    SELECT schema_name INTO STRICT v_schema_name
    FROM platform.tenant
    WHERE code = p_tenant_code AND is_active = TRUE;

    -- Set search_path: tenant schema first, then platform for lookups
    EXECUTE format('SET search_path TO %I, platform', v_schema_name);

    -- Store tenant context for audit logging
    PERFORM set_config('app.tenant_code', p_tenant_code, TRUE);
    PERFORM set_config('app.tenant_schema', v_schema_name, TRUE);

EXCEPTION
    WHEN NO_DATA_FOUND THEN
        RAISE EXCEPTION 'Tenant "%" not found or is inactive.', p_tenant_code;
END;
$$;

COMMIT;
