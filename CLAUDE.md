# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

claimOS is an AI-powered Intelligent Claims Processing Platform for insurance companies: a FastAPI
backend (`backend/`) implementing a document-processing pipeline plus a large surface of "enterprise
platform" subsystems, and a Next.js frontend (`frontend/`) dashboard consuming its REST API.

**Read this before assuming a module is production-grade:** the repo's history is a single "v1.0.0
Enterprise Release" commit (see `CHANGELOG.md`) that claims ~45 phases of platform build-out
(command center, federation, autonomous organization, AI governance, cognitive layer, DevOps, etc).
Many top-level `backend/app/` packages (`acos/`, `agentic_ai/`, `autonomous/`, `command_center/`,
`federation/`, `investigation/`, `devops/`, `collaboration/`, `governance/`, `optimization/`,
`simulation/`, `workflows/`, `platform/`) are thin (100-350 lines) and return hardcoded/mocked data
rather than real implementations — e.g. `command_center/kpi.py` returns a static dict of fake KPIs.
The genuinely load-bearing code is the document pipeline (`app/pipeline/`), its engines
(`app/engines/`), persistence (`app/persistence/`, `app/models/`), and the multi-agent system
(`app/agents/`). Verify behavior by reading the actual module before describing it as functional to
the user.

**No-mock policy:** the codebase deliberately has no mock/fake fallback for AI providers —
`app/llm/providers/mock_provider.py` and `app/engines/ocr/adapters/mock_adapter.py` were removed.
Tests that exercise real LLM/OCR code paths against a live local Ollama server are *skipped* (not
faked) when Ollama isn't reachable — see `backend/tests/conftest.py` and the
`requires_ollama` pytest marker. Don't reintroduce mock providers as a shortcut; if a code path
needs a fake, that's a signal to check whether the test should be marked `requires_ollama` instead.

## Commands

### Backend (from `backend/`)

```bash
poetry install                                    # install deps (Python >=3.13, Poetry-managed)
PYTHONPATH=. poetry run pytest tests/ -v          # run full test suite (this is what CI runs)
PYTHONPATH=. poetry run pytest tests/engines/test_ocr.py -v      # single file
PYTHONPATH=. poetry run pytest tests/engines/test_ocr.py::test_x -v  # single test
poetry run ruff check .                           # lint (line-length 100, rules: E,F,I,W,UP)
poetry run uvicorn app.main:app --reload          # run API locally (needs Postgres/Redis/Neo4j/Ollama reachable)
poetry run alembic upgrade head                   # apply DB migrations (script_location: backend/migrations)
poetry run alembic revision --autogenerate -m "x" # new migration
```

`backend/tests/conftest.py` is a shared root fixture file, but it's minimal — it only provides
Ollama-reachability skipping (`requires_ollama` marker), not DB fixtures. Individual test modules
under `backend/tests/<subsystem>/` manage their own DB/service fixtures — check the target test
file before assuming shared setup applies. Tests that hit a live Ollama server will be skipped
(not failed) in environments without Ollama, including CI, which has no Ollama service configured.

### Frontend (from `frontend/`)

```bash
npm run dev      # Next.js dev server
npm run build
npm run lint      # eslint
```

Frontend talks to the backend via `NEXT_PUBLIC_API_URL` (default `http://localhost:8000/api/v1`,
see `frontend/src/lib/api-client.ts`).

### Whole stack

```bash
make up        # docker compose up -d  (frontend, backend, nginx, postgres, redis, neo4j, ollama)
make logs / make backend / make frontend
make shell     # bash inside the backend container
make down / make clean  # clean removes volumes — data loss
```

`docker-compose.yml` wires: Postgres (pgvector image, claims/knowledge storage), Redis, Neo4j
(knowledge graph, `NEO4J_PLUGINS=["apoc"]`), Ollama (local LLM runtime), and an nginx reverse proxy
in front of frontend+backend. Required secrets come from a root `.env` (see `.env.example`).

CI (`.github/workflows/ci.yml`) runs the backend pytest suite (Python 3.12 in the CI image, though
`pyproject.toml` requires `>=3.13` — be aware of this mismatch if a change relies on 3.13-only
syntax) on push/PR to `main`; the `build-push` job is a placeholder (no actual docker build/push
configured) and has no Ollama service, so `requires_ollama`-marked tests are skipped there.

## Architecture

### Document processing pipeline

The core domain flow is a linear, step-based pipeline defined in `app/pipeline/__init__.py`
(`get_document_pipeline()`), executed by `PipelineOrchestrator` (`app/pipeline/orchestrator.py`)
over a shared `DocumentContext` (`app/pipeline/core.py`). Steps run in this fixed order:

```
Upload → Fingerprint → MetadataExtraction → VirusScan → Storage →
PageExtraction → IQAAssessment → Preprocessing → OCR → LayoutAnalysis →
Classification → BusinessExtraction → EvidenceGraph → CrossValidation →
DecisionEngine → HumanReview → Archiving
```

Each step in `app/pipeline/steps/` is a thin adapter that delegates to the corresponding engine in
`app/engines/` (e.g. `ocr.py` → `app/engines/ocr/manager.py`, `classification.py` →
`app/engines/classification/`, `decision_engine.py` → `app/engines/decision/`). When changing
pipeline behavior, the actual logic usually lives in the engine, not the step wrapper. This step
list has changed before (a standalone `ValidationStep` and separate entity-extraction/decision/
learning steps were removed) — check `app/pipeline/__init__.py` directly rather than trusting a
remembered order.

An alternate, agent-based entry point exists in parallel: `AgentManager.process_claim()`
(`app/agents/manager.py`) — see "Multi-agent system" below. It does not replace the linear
pipeline for document ingestion; it runs *after*, as a post-extraction reasoning layer over a
claim's already-persisted, fused data. Check which one a given endpoint actually calls before
assuming the linear pipeline is in use.

### Multi-agent system (`app/agents/`)

A complete 6-agent collaboration pipeline, one node per agent role, wired into a static DAG:

```
ocr_supervisor        extraction_agent
      |                       |
      v                       v
 fraud_agent            legal_agent
      \                     /
       v                   v
        decision_agent
              |
              v
       supervisor_agent
```

- `AgentRegistry` discovers agent implementations under `app/agents/modules/` (`ocr_supervisor.py`,
  `extraction_agent.py`, `fraud_agent.py`, `legal_agent.py`, `decision_agent.py`,
  `supervisor_agent.py`).
- `app/agents/graph.py` (`build_graph()`) compiles the DAG above as a **LangGraph** `StateGraph` —
  the earlier hand-rolled `Planner`/`Scheduler` pair was replaced outright (deleted, not kept
  alongside) once the platform's own spec called for LangGraph explicitly. Each `BaseAgent` is
  wrapped as a LangGraph node closed over the same shared, mutable `AgentContext`/`SharedMemory`
  every agent already mutated in place — only the per-agent `AgentResult` flows through
  LangGraph-managed state (needs a merge reducer since `ocr_supervisor`/`extraction_agent` write
  it in the same superstep). Not `app/agents/core/planning.py`, which is a separate LLM-based
  `PlanningEngine` used by `POST /agents/plans/generate`.
- `SharedMemory`/`AgentHistory` (`app/agents/shared_memory.py`, `app/agents/memory/`) track
  cross-agent state and an audit trail per claim.
- `AgentMonitor` records per-agent success/failure and duration for observability.
- `EventBus` (`app/agents/communication.py`) is the pub/sub mechanism between agents.
- `app/agents/claim_bridge.py` bridges a claim's fused `ClaimOpeningForm` into the `raw_data` shape
  agents expect (no raw OCR text is persisted anywhere — see `docs/COURS_05_ORCHESTRATION.md` for
  why a text summary of FOUND fields is used instead).

Entry point for a real claim: `POST /claims/{claim_id}/agents/run`
(`app/api/v1/endpoints/agents.py`, `claim_agents_router`) — fetches the claim's opening form, runs
all 6 agents, returns their combined result. The older generic `POST /agents/run` (caller builds
`raw_data` by hand) still exists separately. `FraudAgent`/`LegalAgent`/`DecisionAgent` each call a
*separately configurable* Ollama model (`OLLAMA_FRAUD_MODEL`/`OLLAMA_LEGAL_MODEL`/
`OLLAMA_DECISION_MODEL` in `app/config/settings.py`, not the shared `OLLAMA_DEFAULT_MODEL`) — all
three currently default to `qwen3:4b` (~2.5GB, chosen over larger models after a real disk-space
failure while pulling bigger candidates — see `docs/COURS_08_LANGGRAPH_ET_MODELES.md`). Full
rationale for every design choice (the deterministic-rules-before-LLM safety layer in
`decision_agent`, why `supervisor_agent` can override a confident decision, the LangGraph
migration, model selection) is in `docs/COURS_01_DECISIONS_ARCHITECTURE.md` through
`docs/COURS_08_LANGGRAPH_ET_MODELES.md`.

### Business extraction pipeline (`app/engines/extraction/`)

This is the step-12 `BusinessExtractionStep` (`app/pipeline/steps/extraction.py`) in the linear
pipeline above — the only wired entry point is document ingestion
(`POST /claims/{claim_id}/documents`, `app/api/v1/endpoints/documents.py` →
`DocumentService.ingest_document()` in `app/services/document_service.py` →
`get_document_pipeline().execute()`). There is no CLI or scheduled job that triggers extraction, and
the parallel `AgentManager` path does not call it.

- **Engine**: `ExtractionEngine` (`app/engines/extraction/manager.py`) runs every extractor in
  `ExtractorRegistry` per page, isolates failures per-extractor (one broken extractor degrades, not
  the whole document), then `EntityResolver` (`resolver.py`) picks the highest-confidence candidate
  per `field_name` when multiple extractors produce the same field.
- **Extractors registered** (`app/pipeline/steps/extraction.py`): 5 deterministic regex/layout
  extractors under `extractors/insurance/` and `extractors/vehicle/` (license plate, policy number,
  national ID, owner name, vehicle brand — only ~5 of ~40 possible fields), plus
  **`LLMFieldExtractor`** (`extractors/llm/llm_field_extractor.py`, priority 40 — lowest, so
  deterministic extractors win ties on overlapping fields like vehicle plate).
- **LLM used**: `LLMFieldExtractor` calls `LLMManager.generate()` (`app/llm/manager.py`) with
  `model=get_settings().OLLAMA_DEFAULT_MODEL` (default `"qwen2.5"`, env `OLLAMA_DEFAULT_MODEL`),
  `temperature=0.0`, `response_format={"type": "json_object"}`. `LLMManager` routes by substring in
  the model name (`gpt`→OpenAI, `claude`→Anthropic, `gemini`→Gemini, else→Ollama), so this call
  always resolves to the local Ollama provider unless the default model name changes. No mock
  fallback — an unreachable Ollama makes the extractor log a warning and return `[]` (see
  no-mock policy above).
- **Prompt**: built by `_build_prompt()` in `llm_field_extractor.py`. It's a French-language prompt
  instructing the model to extract only information actually present (never invent — absent fields
  get `value: null, confidence: 0.0`), listing every field from `SCALAR_FIELD_SPECS` (~40 fields:
  accident facts, policy holder, driver, adverse party) with its description and expected JSON type
  (`text`/`date`/`boolean`/`number`), plus a nested `victimes` list schema from `VICTIM_FIELD_SPECS`
  (per-victim sub-fields). The full page's OCR text (`_full_text()`, concatenated word-by-word from
  `OCRResult.page.blocks`) is appended at the end. Expected output shape:
  `{"fields": {"<name>": {"value": ..., "confidence": 0.0-1.0}}, "victimes": [...]}`.
- **Parsing/validation**: `GuardrailsEngine.validate_json_output()` (`app/llm/guardrails.py`) strips
  ```` ```json ```` fences and `json.loads`s the raw response (raises `ValueError` on invalid JSON,
  which the extractor catches and degrades from). Per-field, `_coerce_value()` casts the raw value to
  its declared type (bool coercion, `float()` for numbers, `YYYY-MM-DD` regex check for dates — a
  failed date check is a soft signal, not a hard rejection) and returns `(value, is_valid)`.
  `ConfidenceAdjuster.adjust()` (`confidence.py`) then penalizes invalid-format values (×0.5), boosts
  entities tied to a layout form region, and penalizes entities with no bounding box; entities with
  final `confidence <= 0.3` are dropped. Every entity carries a `Provenance`
  (`app/engines/extraction/models.py`) with `extraction_method="llm"` for traceability.
- **Downstream**: per-page `ExtractionResult`s are merged into one document-level result by
  `merge_document_extraction()` (`app/engines/extraction/merge.py`, plain concatenation — entities
  already carry page-level provenance). `FormMappingEngine` (`app/engines/form_mapping/manager.py`)
  then fuses extractions from multiple role-tagged documents (`DocumentRole`: OWN_VEHICLE,
  ADVERSE_VEHICLE, POLICY_HOLDER, VICTIM, ACCIDENT_REPORT) into one `ClaimOpeningForm`, exposed via
  `GET .../opening-form` with per-field `FieldStatus` (FOUND/NOT_FOUND/CONFLICT) and manual override
  via `PATCH .../opening-form` (`correct_opening_form_field`, wins over auto-extraction).
  `document_role` is optional at upload time; `infer_document_role()` auto-tags the one
  unambiguous case (`"Police Report"` family → `ACCIDENT_REPORT`) when the caller doesn't specify
  one — see `docs/COURS_02_ROLE_AUTOMATIQUE.md` for why only that one family is auto-inferred.
- **Manual entry**: a claim's opening form can also be filled entirely by hand, without any
  document, via `POST .../opening-form/manual` (`DocumentService.submit_manual_fields()`) — bulk
  version of the same `field_overrides` mechanism `correct_field()` uses for single-field
  corrections. See `docs/COURS_03_SAISIE_MANUELLE.md`.
- **Tests**: `tests/engines/extraction/test_extraction.py` covers `ExtractionEngine` end-to-end but
  only with the regex/layout extractors (no LLM). `tests/engines/extraction/test_llm_field_extractor.py`
  unit-tests `LLMFieldExtractor` against a **mocked** `LLMManager` (`AsyncMock`) — scalar fields,
  null values, victim list parsing, LLM-failure degradation, and the empty-OCR-text short-circuit.
  None of these are `requires_ollama`-marked, so there's currently no test that exercises the real
  prompt against a live Ollama model — worth adding if the prompt/field list changes materially.

### Knowledge / RAG platform (`app/knowledge/`)

`KnowledgeManager` composes: `EmbeddingsEngine` (via `LLMManager`), `PgVectorStore` (Postgres +
pgvector) as the primary vector store, `BM25Index` for keyword search, `HybridSearchEngine`
combining both, and `SummarizerEngine`. Documents are tracked both in an in-memory list and
persisted via SQLAlchemy (`app/models/knowledge.py`). Neo4j (`app/graph/`) backs graph-based
knowledge/relationship queries separately from the vector store.

### Persistence

- SQLAlchemy models live in `app/models/` and are re-exported through `app/models/__init__.py` —
  import from there (not individual model files) so the declarative `Base` sees every model
  registered before relationships resolve.
- Domain shape: lookup tables (`ClaimStatus`, `ClaimType`, `DamageSeverity`, `DocumentType`, etc.)
  → core entities (`Operator`, `InsurancePolicy`, `ClaimFile`, `ClaimDocument`/`DocumentPage`) →
  parties/vehicles and beyond.
- `app/persistence/` holds the lower-level base/session/unit-of-work/repository plumbing; `app/repositories/`
  holds higher-level repository implementations — these are separate layers, don't assume overlap.
- Alembic migrations are in `backend/migrations/versions/`; only two exist so far (initial schema,
  knowledge vector tables) — the schema is still young relative to how much of `app/models/` exists.

### Config

Runtime settings are `app/config/settings.py` (`get_settings()`, pydantic-settings, reads
`backend/.env`). `app/core/settings.py` is an intentional empty stub with a comment pointing back
to `app/config/settings.py` — do not add settings there.

### API layout

`app/main.py` builds the FastAPI app and mounts two router trees: `app/api/router.py` (top-level,
includes `app/api/v1/router.py`) and a separate `review_router` (`app/review/review_router.py`).
`app/api/v1/router.py` aggregates the endpoint modules under `app/api/v1/endpoints/` — one per
subsystem (claims, auth, ollama, knowledge, agents, governance, federation, command_center, ...).
When adding an endpoint, register it there and follow the existing subsystem grouping rather than
adding to an unrelated module.

Domain-specific `ClaimOSException` subclasses (`EntityNotFoundError`, `DuplicateEntityError`,
`BusinessValidationError`, `EngineProcessingError`) are mapped to HTTP status codes via exception
handlers in `app/main.py` (404/409/422/502/500) — raise these instead of raw `HTTPException` inside
engines/services so the status code mapping stays centralized.

### Frontend

Next.js App Router under `frontend/src/app/`, split into `(auth)` (login, MFA) and `(dashboard)`
route groups. Dashboard route groups mirror the backend subsystems closely (agents, claims,
command-center, federation, governance, investigation, knowledge, local-ai, observability,
platform, security, workflow, ...) — when a backend endpoint module has a UI, look for the
matching folder name under `(dashboard)`. All API calls go through the single client in
`frontend/src/lib/api-client.ts`.
