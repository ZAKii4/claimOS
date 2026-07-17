# claimOS — Cours complet du projet

Ce document explique claimOS de A à Z : ce que fait le produit, comment le code est organisé,
comment une pièce jointe devient des données structurées, et où se trouvent les zones fragiles.
Il est écrit pour quelqu'un qui n'a jamais ouvert le repo — chaque section peut se lire seule,
mais l'ordre suit le trajet réel d'un document dans le système.

**État au 2026-07-17** : la cause racine documentée au §4.6 (aucune information "sinistre"
extraite) a été corrigée, et le second parcours de saisie (manuelle) ainsi que le pipeline complet
à 6 agents ont été construits. Le détail de ce travail, avec le raisonnement complet derrière
chaque décision, est dans une série de cours dédiée :

- [`COURS_01_DECISIONS_ARCHITECTURE.md`](COURS_01_DECISIONS_ARCHITECTURE.md) — pourquoi ces choix
- [`COURS_02_ROLE_AUTOMATIQUE.md`](COURS_02_ROLE_AUTOMATIQUE.md) — le fix de la cause racine
- [`COURS_03_SAISIE_MANUELLE.md`](COURS_03_SAISIE_MANUELLE.md) — le second parcours d'ouverture
- [`COURS_04_AGENTS.md`](COURS_04_AGENTS.md) — les 6 agents et leur graphe de dépendances
- [`COURS_05_ORCHESTRATION.md`](COURS_05_ORCHESTRATION.md) — le branchement sur un vrai claim
- [`COURS_06_TESTS.md`](COURS_06_TESTS.md) — ce qui est testé, et ce qui ne l'est pas encore
- [`COURS_07_FRONTEND.md`](COURS_07_FRONTEND.md) — l'UI des deux parcours et de l'analyse à 6 agents
- [`COURS_08_LANGGRAPH_ET_MODELES.md`](COURS_08_LANGGRAPH_ET_MODELES.md) — migration vers LangGraph
  et choix des modèles par agent (recherche, puis une vraie contrainte disque qui a tranché)

Ce document-ci reste la référence pour l'architecture générale ; les sections §4.6, §6 et §9
ci-dessous ont été mises à jour en conséquence plutôt que dupliquées.

---

## 1. Le produit, en une phrase

claimOS est une plateforme de traitement de sinistres automobile pour assureurs : un opérateur
(ou un futur flux automatisé) dépose les pièces d'un dossier — constat amiable, carte grise,
attestation d'assurance, certificat médical — et le système essaie d'en extraire automatiquement
les informations utiles (qui, quoi, où, quand, responsabilité, victimes...) pour préremplir un
formulaire d'ouverture de sinistre, plutôt que de faire ressaisir ces champs à la main.

Deux couches composent le dépôt :

- **`backend/`** : API FastAPI (Python 3.13) qui fait tout le travail réel — ingestion,
  OCR, classification, extraction, décision.
- **`frontend/`** : dashboard Next.js qui consomme cette API.

**Un avertissement structurel important**, à garder en tête pour tout le reste du cours : le repo
provient d'un unique commit "v1.0.0 Enterprise Release" qui prétend livrer ~45 phases de
plateforme (command center, fédération, gouvernance IA, DevOps autonome...). Une bonne partie de
ces modules `backend/app/{acos,agentic_ai,autonomous,command_center,federation,investigation,
devops,collaboration,governance,optimization,simulation,workflows,platform}/` sont des coquilles
de 100-350 lignes qui renvoient des données statiques/mockées — par exemple
`command_center/kpi.py` renvoie un dictionnaire de KPIs en dur. **Le code qui compte vraiment** est
le pipeline documentaire (`app/pipeline/`), ses moteurs (`app/engines/`), la persistance
(`app/persistence/`, `app/models/`), et le système multi-agents (`app/agents/`). Ne jamais
présumer qu'un module sous `app/` fait quelque chose de réel sans l'avoir lu.

---

## 2. Vue d'ensemble de l'infrastructure

```
                 ┌──────────────┐        ┌───────────────────┐
   Navigateur →  │  Next.js     │  REST  │   FastAPI backend │
                 │  (frontend)  │ ─────→ │   (backend/app)   │
                 └──────────────┘        └─────────┬─────────┘
                                                     │
                     ┌────────────┬──────────────────┼──────────────┬─────────────┐
                     ▼            ▼                  ▼              ▼             ▼
                Postgres      Redis              Neo4j          Ollama       nginx (proxy)
             (pgvector,        (cache)        (graphe de       (LLM local,   devant front+back
              claims, KB)                      connaissance)    embeddings)
```

Tout est orchestré par `docker-compose.yml` (`make up` / `make down` / `make logs`). Les secrets
viennent d'un `.env` racine (modèle : `.env.example`). Côté backend, les settings runtime sont
centralisés dans `app/config/settings.py` (`get_settings()`, pydantic-settings) — `app/core/settings.py`
est un stub vide qui pointe explicitement vers ce fichier, ne jamais y ajouter de config.

**Commandes utiles** (depuis `backend/`) :

```bash
poetry install
PYTHONPATH=. poetry run pytest tests/ -v
poetry run ruff check .
poetry run uvicorn app.main:app --reload
poetry run alembic upgrade head
```

`app/main.py` construit l'app FastAPI et monte deux arbres de routes : `app/api/router.py`
(qui inclut `app/api/v1/router.py`, ~30 modules d'endpoints sous `app/api/v1/endpoints/`, un par
sous-système) et `review_router` séparé (`app/review/`). Les exceptions métier
(`EntityNotFoundError`, `DuplicateEntityError`, `BusinessValidationError`, `EngineProcessingError`)
sont mappées vers des codes HTTP (404/409/422/502/500) dans `app/main.py` — c'est pour ça que le
code métier lève ces exceptions plutôt que des `HTTPException` brutes.

---

## 3. Le pipeline documentaire — le cœur du système

### 3.1 Vue d'ensemble

Un document suit une chaîne linéaire de 17 étapes, définie dans `app/pipeline/__init__.py`
(`get_document_pipeline()`) et exécutée par `PipelineOrchestrator`
(`app/pipeline/orchestrator.py`) sur un état partagé `DocumentContext` (`app/pipeline/core.py`) :

```
Upload → Fingerprint → MetadataExtraction → VirusScan → Storage →
PageExtraction → IQAAssessment → Preprocessing → OCR → LayoutAnalysis →
Classification → BusinessExtraction → EvidenceGraph → CrossValidation →
DecisionEngine → HumanReview → Archiving
```

Chaque étape (`app/pipeline/steps/xxx.py`) est un adaptateur fin qui délègue le vrai travail à un
moteur dans `app/engines/` (ex : `ocr.py` → `app/engines/ocr/manager.py`). **La logique vit dans le
moteur, pas dans l'étape** — c'est là qu'il faut chercher/modifier le comportement.

Un **point structurel critique** traverse toute la seconde moitié du pipeline : chaque étape ne
s'exécute que si l'étape précédente a produit un résultat `status == SUCCESS` pour la page
concernée. Concrètement :

- Pas d'OCR réussi → Layout est sauté pour cette page (`DEGRADED`, pas fatal, mais rien n'est
  produit).
- Pas de Layout → Classification sautée.
- Pas de Classification → `BusinessExtractionStep` saute la page entièrement
  (`app/pipeline/steps/extraction.py:42-51`, condition qui exige les 3 résultats en `SUCCESS`).

Autrement dit : **une seule étape qui échoue silencieusement en amont suffit à faire disparaître
toute extraction en aval, sans erreur bloquante visible** — c'est le premier endroit où regarder
quand "rien n'est extrait".

Un point d'entrée alternatif existe en parallèle : `AgentManager.process_claim()`
(`app/agents/manager.py`), qui remplace le pipeline séquentiel par un graphe planner/scheduler
(voir §6). **Il n'est pas branché sur l'ingestion de documents aujourd'hui** — seul le pipeline
linéaire est réellement utilisé par l'API `POST /claims/{claim_id}/documents`.

### 3.2 Le point d'entrée réel

```
POST /claims/{claim_id}/documents            (app/api/v1/endpoints/documents.py)
        │
        ▼
DocumentService.ingest_document()             (app/services/document_service.py)
        │  construit un DocumentContext, appelle get_document_pipeline().execute(context)
        │  segmente les pages en documents logiques (app/pipeline/segmentation.py)
        │  fusionne l'extraction par page → une ExtractionResult par document
        │  persiste un ClaimDocument par segment, avec document_role et extracted_data
        ▼
GET /claims/{claim_id}/documents/opening-form (app/api/v1/endpoints/documents.py)
        │  fusionne tous les documents rôlés+extraits d'un claim en un ClaimOpeningForm
        ▼
PATCH /claims/{claim_id}/documents/opening-form
        │  correction manuelle d'un champ (prime toujours sur l'extraction auto)
```

Un même upload peut contenir plusieurs documents logiques (ex : un scan qui enchaîne un PV puis
une attestation) — `segment_pages()` les sépare en segments, chacun devenant un `ClaimDocument`
distinct en base.

### 3.3 OCR (étape 9)

`app/pipeline/steps/ocr.py` → `HybridOCREngine` (`app/engines/ocr/engine.py`) → `OCRManager`
(`app/engines/ocr/manager.py`), qui essaie une liste d'adaptateurs dans l'ordre
`["doctr", "paddleocr", "tesseract"]` et s'arrête au premier qui réussit. Si **aucun** des trois
n'est disponible (dépendances lourdes : `torch`+`doctr`, `paddlepaddle`+`paddleocr`, binaire
système `tesseract`), `OCRManager.execute()` lève `RuntimeError`, l'étape OCR marque une erreur
`FATAL`, et — voir §3.1 — tout le reste de la chaîne est sauté pour cette page. Il n'existe plus
d'adaptateur mock depuis le retrait de `mock_adapter.py` (voir §8, "politique anti-mock").

Vérification rapide de la disponibilité des moteurs :
```python
from app.engines.ocr.manager import OCRManager
OCRManager().get_available_adapters()
```

### 3.4 Layout Analysis (étape 10) et Classification (étape 11)

`LayoutEngine` (`app/engines/layout/manager.py`) détecte les régions structurelles (champs de
formulaire, tableaux...) à partir de l'image et de l'OCR. `ClassificationEngine`
(`app/engines/classification/manager.py`) combine trois classifieurs (`RulesClassifier`,
`OCRClassifier`, `VisualClassifier`) via un `EnsembleClassifier`, avec un seuil `unknown_threshold
= 0.4` en dessous duquel le document est classé "inconnu". Ces deux moteurs traitent
**une seule page à la fois** (`layout_result.document.pages[0]` — hypothèse d'architecture
actuelle, pas de regroupement multi-page natif à ce niveau).

### 3.5 Business Extraction (étape 12) — voir §4, section dédiée.

### 3.6 Decision Engine, Human Review, Archiving

Étapes 15-17, moins critiques pour "pourquoi rien n'est extrait" — elles consomment le résultat de
l'extraction plutôt que d'en produire.

---

## 4. Extraction métier — comment le texte devient des champs structurés

C'est le module `app/engines/extraction/` et l'étape `BusinessExtractionStep`
(`app/pipeline/steps/extraction.py`).

### 4.1 L'orchestration

`ExtractionEngine` (`app/engines/extraction/manager.py`) :
1. Récupère les extracteurs applicables via `ExtractorRegistry`.
2. Exécute **chaque extracteur isolément** — une exception dans un extracteur ne casse pas les
   autres (`try/except` par extracteur, erreur loggée dans `extractor_errors`).
3. `EntityResolver` (`resolver.py`) règle les conflits : si deux extracteurs produisent le même
   `field_name`, celui avec la plus haute confiance gagne.
4. Calcule une confiance globale = moyenne des confiances des entités retenues.

### 4.2 Les 6 extracteurs enregistrés

Déclarés dans `BusinessExtractionStep.__init__` :

| Extracteur | Fichier | Méthode | Champs couverts |
|---|---|---|---|
| `vehicle.license_plate_extractor` | `extractors/vehicle/license_plate.py` | regex | plaque |
| `insurance.policy_number_extractor` | `extractors/insurance/policy_number.py` | regex/layout | n° police |
| `insurance.national_id_extractor` | `extractors/insurance/national_id.py` | regex | CIN |
| `insurance.owner_name_extractor` | `extractors/insurance/owner_identity.py` | layout | nom propriétaire |
| `vehicle.brand_extractor` | `extractors/vehicle/vehicle_brand.py` | regex/dictionnaire | marque véhicule |
| **`llm.field_extractor`** | `extractors/llm/llm_field_extractor.py` | **appel LLM** | **~35 champs restants** |

Les 5 extracteurs regex/layout ne couvrent que 5 champs sur les ~40 que déclare
`ClaimOpeningForm`. **Tout le reste — circonstances de l'accident, victimes, dates, responsabilité,
autorité, informations du conducteur — passe exclusivement par `LLMFieldExtractor`.** C'est
l'extracteur le plus important pour "l'information du sinistre" au sens large, et le plus fragile
(dépend d'un service externe).

`LLMFieldExtractor.priority = 40` (le plus bas) : sur un champ où deux extracteurs se
chevauchent (ex. plaque d'immatriculation, que le LLM essaie aussi en cross-check), le LLM ne
l'emporte jamais sur l'extracteur dédié à confiance égale.

### 4.3 Le LLM utilisé et le prompt

`LLMFieldExtractor._call_llm()` appelle `LLMManager.generate()` (`app/llm/manager.py`) avec :
- `model = get_settings().OLLAMA_DEFAULT_MODEL` (défaut `"qwen2.5"`, env `OLLAMA_DEFAULT_MODEL`)
- `temperature = 0.0`
- `response_format = {"type": "json_object"}`

`LLMManager` route le nom de modèle vers un provider par sous-chaîne
(`gpt`→OpenAI, `claude`→Anthropic, `gemini`→Gemini, sinon→**Ollama**), donc cet appel tombe
toujours sur Ollama local sauf changement du nom de modèle par défaut.
`OllamaProvider` (`app/llm/providers/ollama_provider.py:31-32`) remappe en interne
`"qwen2.5"` → `"qwen2.5-coder:14b"` (le nom réel du modèle pullé côté Ollama).

Le prompt (`_build_prompt()`, `llm_field_extractor.py:119-149`) est en français :
- instruction explicite de ne jamais inventer une valeur (`value: null, confidence: 0.0` si absent) ;
- liste des ~40 champs scalaires (`SCALAR_FIELD_SPECS`) avec description + type attendu
  (`text`/`date`/`boolean`/`number`) ;
- schéma imbriqué pour une liste `victimes` (`VICTIM_FIELD_SPECS`) ;
- le texte OCR complet de la page (`_full_text()`, concaténation mot par mot de
  `OCRResult.page.blocks`), injecté en fin de prompt.

Sortie attendue :
```json
{
  "fields": {"<nom_champ>": {"value": ..., "confidence": 0.0-1.0}, ...},
  "victimes": [{"nom": ..., "prenom": ..., ...}]
}
```

### 4.4 Parsing et validation de la sortie

1. `GuardrailsEngine.validate_json_output()` (`app/llm/guardrails.py`) : retire les fences
   ` ```json ` éventuelles, puis `json.loads`. Lève `ValueError` si invalide.
2. `_coerce_value(raw_value, value_type)` : cast selon le type déclaré — booléen, `float()` pour
   les nombres, regex `AAAA-MM-JJ` pour les dates (échec = signal doux, pas un rejet dur, car l'OCR
   produit des formats de date très variés).
3. `ConfidenceAdjuster.adjust()` (`confidence.py`) : pénalise ×0.5 si format invalide, bonus +0.1
   si l'entité est liée à une région de formulaire structurée, pénalité ×0.9 si pas de bounding
   box. **Toute entité dont la confiance finale est ≤ 0.3 est purement écartée.**
4. Chaque entité retenue devient une `ExtractedEntity` (`app/engines/extraction/models.py`) avec
   une `Provenance` complète (page, méthode `"llm"`, nom de l'extracteur) pour la traçabilité.

**Aucun fallback silencieux vers une fausse valeur** : si l'appel LLM échoue (Ollama injoignable,
timeout, JSON invalide), `LLMFieldExtractor._call_llm()` catch l'exception, logge un `warning`, et
retourne `None` → l'extracteur produit `[]` pour cette page. C'est une dégradation *silencieuse*
du point de vue de l'utilisateur final (pas d'erreur bloquante remontée), donc un point de
défaillance difficile à repérer sans regarder les logs.

### 4.5 Fusion multi-pages puis multi-documents

- `merge_document_extraction()` (`app/engines/extraction/merge.py`) : concatène les
  `ExtractionResult` de toutes les pages d'un même document logique en un seul résultat. Retourne
  `None` si rien à fusionner (traité comme "pas de données", pas fabriqué).
- `FormMappingEngine.map()` (`app/engines/form_mapping/manager.py`) : fusionne les extractions de
  **plusieurs documents d'un même claim** (carte grise + attestation + constat + certificat
  médical...) en un seul `ClaimOpeningForm`.

**Le point le plus important de toute cette section** : `FormMappingEngine` ne sait pas, à partir
d'un `field_name` générique comme `"vehicle_plate"`, s'il appartient au véhicule assuré ou au
véhicule adverse. Il a donc besoin d'un `DocumentRole` explicite par document
(`OWN_VEHICLE`, `ADVERSE_VEHICLE`, `POLICY_HOLDER`, `VICTIM`, `ACCIDENT_REPORT`), fourni au moment
de l'upload (`document_role` dans `POST /claims/{claim_id}/documents`, paramètre **optionnel**,
défaut `None`). `FIELD_MAPPING` (table `(rôle, field_name) → chemin dans ClaimOpeningForm`,
`form_mapping/manager.py`) montre que **la quasi-totalité des champs "niveau sinistre"** —
`numero_pv`, `lieu_survenance`, `date_survenance`, `circonstances_accident`, `responsabilite_pct`,
`victimes_blessees`, la liste `victimes`, etc. — **n'est mappée que sous le rôle
`ACCIDENT_REPORT`**. Un document jamais tagué avec ce rôle précis ne remplira donc **jamais** ces
champs, quelle que soit la qualité de l'extraction en amont.

Et `DocumentService.get_opening_form()` (`document_service.py:254`) est encore plus strict :
```python
if not document.document_role or not document.extracted_data:
    continue
```
Tout document sans `document_role` est **silencieusement ignoré** du formulaire final — pas
d'erreur, pas d'avertissement, juste absent.

### 4.6 Ce que la vérification empirique a montré (2026-07-17)

Sur la base de données de développement actuelle (58 `claim_document`, 43 claims) :

- OCR : les 3 adaptateurs (`doctr`, `tesseract`, `paddleocr`) sont disponibles dans cet
  environnement. Ollama est joignable et le modèle `qwen2.5-coder:14b` est bien pullé. Ces deux
  causes environnementales sont **écartées** ici.
- 48/58 documents ont au moins une entité extraite ; l'extraction fonctionne globalement.
- Mais répartition des entités par rôle : `OWN_VEHICLE` = 96 entités (39 docs), `ADVERSE_VEHICLE` =
  30 entités (13 docs), **`ACCIDENT_REPORT` = 9 entités sur seulement 2 documents au total**.
- **Sur les 43 claims de la base, aucun ne combine un document `ACCIDENT_REPORT` avec des
  documents `OWN_VEHICLE`/`ADVERSE_VEHICLE`** — deux claims isolés ont *uniquement* un
  `ACCIDENT_REPORT`, les 41 autres n'en ont jamais tagué un seul.
- Conséquence directe via §4.5 : pour ces 41 claims, `ClaimOpeningForm` peut légitimement afficher
  plaque/marque/propriétaire (bien extraits), mais **tous les champs "sinistre"
  (circonstances, lieu, date, victimes, responsabilité...) restent NOT_FOUND** — pas parce que
  l'extraction a échoué, mais parce qu'aucun document n'a jamais été tagué `ACCIDENT_REPORT` pour
  ces claims.
- Signal à part : 4 documents (2 claims) ont `document_role = NULL` — probablement le constat lui
  -même, jamais tagué, donc totalement invisible dans `get_opening_form()` (§4.5).
- Un document isolé (`f8c3605a-...`, 11 pages, qualité OCR correcte 0.73-0.99) a produit
  `global_confidence = 0.0` et **zéro entité malgré les 6 extracteurs exécutés sans erreur** —
  anomalie ponctuelle qui mérite un second regard (contenu réellement vide, ou bug de fond dans un
  cas limite), mais qui ne représente qu'1 document sur 58 et n'explique pas le pattern global.

**Conclusion de la vérification** : la cause dominante et vérifiée du "aucune information du
sinistre extraite" est un **écart de workflow, pas un bug d'extraction** — le document
constat/PV n'est presque jamais uploadé avec `document_role=ACCIDENT_REPORT`, alors que c'est le
seul rôle qui déverrouille les champs de niveau sinistre dans `FIELD_MAPPING`.

**Corrigé le 2026-07-17** (voir [`COURS_02_ROLE_AUTOMATIQUE.md`](COURS_02_ROLE_AUTOMATIQUE.md)) :
`infer_document_role()` (`app/engines/form_mapping/manager.py`) déduit désormais automatiquement
`ACCIDENT_REPORT` quand la classification renvoie la famille `"Police Report"` (le constat/PV) —
la seule famille non ambiguë. `DocumentService.ingest_document()` applique cette déduction quand
l'appelant ne fournit pas de `document_role` explicite, sans jamais l'emporter sur un choix
manuel. Les familles ambiguës (`Identity Card`, `Insurance Attestation`...) restent volontairement
non déduites — deviner faux serait pire que de laisser `NOT_FOUND`.

---

## 5. Persistance

- Les modèles SQLAlchemy vivent dans `app/models/` et sont ré-exportés via
  `app/models/__init__.py` — toujours importer depuis ce point d'entrée (pas les fichiers
  individuels), pour que la `Base` déclarative voie tous les modèles avant de résoudre les
  relations.
- Forme du domaine : tables de référence (`ClaimStatus`, `ClaimType`, `DamageSeverity`,
  `DocumentType`...) → entités centrales (`Operator`, `InsurancePolicy`, `ClaimFile`,
  `ClaimDocument`/`DocumentPage`) → parties/véhicules et au-delà.
- `app/persistence/` = plomberie bas niveau (session, unit-of-work, repository de base).
  `app/repositories/` = implémentations de repository de plus haut niveau. Deux couches
  distinctes, pas de recouvrement à supposer.
- Migrations Alembic sous `backend/migrations/versions/` — seulement deux existent à ce jour
  (schéma initial, tables vectorielles de connaissance) : le schéma est jeune par rapport à
  l'étendue de `app/models/`.

---

## 6. Le système multi-agents (`app/agents/`) — la couche de collaboration post-extraction

- `AgentRegistry` découvre les agents sous `app/agents/modules/`.
- `Planner` (`app/agents/planner.py` — à ne pas confondre avec `PlanningEngine` dans
  `app/agents/core/planning.py`, un planificateur LLM séparé utilisé par
  `POST /agents/plans/generate`) construit un `ExecutionGraph` statique à partir des agents
  disponibles.
- `Scheduler` (`app/agents/scheduler.py`) exécute ce graphe de façon asynchrone en respectant les
  dépendances.
- `SharedMemory`/`AgentHistory` (`app/agents/shared_memory.py`, `app/agents/memory/`) gardent
  l'état inter-agents et un journal d'audit par claim.
- `AgentMonitor` enregistre succès/échec/durée par agent.
- `EventBus` (`app/agents/communication.py`) = pub/sub entre agents.

**Mis à jour le 2026-07-17** (détail complet :
[`COURS_04_AGENTS.md`](COURS_04_AGENTS.md) et [`COURS_05_ORCHESTRATION.md`](COURS_05_ORCHESTRATION.md)) —
ce système est maintenant un pipeline complet de **6 agents** avec un rôle chacun, branché sur de
vraies données de claim :

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

- `ocr_supervisor` (déjà existant) — adopte le texte déjà connu du claim plutôt que de relancer
  l'OCR.
- `extraction_agent` (nouveau) — aplatit le `ClaimOpeningForm` fusionné en entités plates.
- `fraud_agent` (déjà existant) — score de fraude via LLM.
- `legal_agent` (nouveau) — règles de dates déterministes + analyse LLM des champs juridiques,
  dégrade proprement si le LLM échoue.
- `decision_agent` (nouveau) — recommandation `DecisionType`, ne peut jamais auto-approuver
  silencieusement sur échec technique.
- `supervisor_agent` (nouveau) — arbitrage final, filet de sécurité sur confiance faible.

**Ce système reste distinct du pipeline linéaire, volontairement** — il ne refait pas l'OCR/la
classification/l'extraction (déjà faits, testés, multi-documents dans le pipeline §3), il
raisonne *après*, sur les données déjà persistées d'un claim. Point d'entrée :
`POST /claims/{claim_id}/agents/run` (`app/api/v1/endpoints/agents.py`), à appeler après qu'un
claim a des données (upload ou saisie manuelle, §4.6 et
[`COURS_03_SAISIE_MANUELLE.md`](COURS_03_SAISIE_MANUELLE.md)). Le endpoint générique
`POST /agents/run` (caller construit `raw_data` à la main) reste disponible séparément.

---

## 7. Knowledge / RAG (`app/knowledge/`)

`KnowledgeManager` compose : `EmbeddingsEngine` (via `LLMManager`), `PgVectorStore` (Postgres +
pgvector) comme store vectoriel principal, `BM25Index` pour la recherche par mots-clés,
`HybridSearchEngine` combinant les deux, et `SummarizerEngine`. Les documents sont suivis à la
fois en mémoire et persistés via SQLAlchemy (`app/models/knowledge.py`). Neo4j (`app/graph/`)
alimente des requêtes de connaissance/relations à part, indépendamment du store vectoriel.

---

## 8. Politique anti-mock et tests

Le projet a délibérément retiré tout fallback mocké pour les providers IA :
`app/llm/providers/mock_provider.py` et `app/engines/ocr/adapters/mock_adapter.py` ont été
supprimés. `backend/tests/conftest.py` fournit un marqueur `requires_ollama` qui **skip** (et ne
fake pas) les tests qui appellent un vrai Ollama local quand il n'est pas joignable — y compris en
CI, qui n'a pas de service Ollama configuré (`.github/workflows/ci.yml`).

Tests liés à l'extraction :
- `tests/engines/extraction/test_extraction.py` : `ExtractionEngine` bout-en-bout, mais uniquement
  avec les extracteurs regex/layout (pas de LLM).
- `tests/engines/extraction/test_llm_field_extractor.py` : unit tests de `LLMFieldExtractor` avec
  un `LLMManager` **mocké** (`AsyncMock`) — champs scalaires, valeurs nulles, victimes, dégradation
  sur échec LLM, court-circuit sur texte OCR vide. **Aucun test n'exerce le vrai prompt contre un
  Ollama réel** (pas de marqueur `requires_ollama` ici) — à ajouter si le prompt ou la liste de
  champs change significativement.
- `tests/engines/form_mapping/test_form_mapping.py` : couvre la fusion multi-documents en aval.

Ne jamais réintroduire un mock provider comme raccourci — si un chemin de code a besoin d'un faux
retour, c'est le signal qu'un test devrait plutôt être marqué `requires_ollama`.

---

## 9. Où regarder selon le symptôme (aide-mémoire)

| Symptôme observé | Premier endroit à vérifier |
|---|---|
| Aucune extraction sur *aucun* document | `OCRManager.get_available_adapters()` — un moteur OCR manquant fait tout échouer en cascade |
| Extraction partielle : seuls plaque/police/CIN/nom/marque sortent, rien d'autre | Ollama joignable ? `OLLAMA_DEFAULT_MODEL` pullé ? → `LLMFieldExtractor._call_llm()` |
| Véhicule/police bien extraits mais **rien sur le sinistre** (circonstances, victimes, date, lieu) | Depuis le 2026-07-17, `ACCIDENT_REPORT` est auto-inféré pour la famille `"Police Report"` (§4.6, [`COURS_02`](COURS_02_ROLE_AUTOMATIQUE.md)) — si ça persiste, vérifier que la classification a bien reconnu le document comme tel (`RulesClassifier`, mots-clés "constat amiable"/PV) |
| Un document précis à zéro alors que les autres marchent | Regarder `extractors_used` et `global_confidence` dans son `extracted_data` ; qualité OCR (`document_page.quality_score`) |
| Formulaire d'ouverture vide malgré des `ClaimDocument.extracted_data` non nuls | `document.document_role IS NULL` et la famille n'était pas `"Police Report"` → toujours exclu par `get_opening_form()` (`document_service.py`) — utiliser la saisie manuelle ([`COURS_03`](COURS_03_SAISIE_MANUELLE.md)) ou taguer le rôle explicitement |
| Recommandation de décision manquante ou pas de score de fraude/légal pour un claim | La collaboration multi-agents n'est pas automatique — appeler `POST /claims/{id}/agents/run` explicitement ([`COURS_05`](COURS_05_ORCHESTRATION.md)) |
| Comportement différent de ce qu'un module `app/{governance,federation,command_center,...}` "devrait" faire | Relire §1 — c'est probablement une coquille qui renvoie des données statiques |

---

## 10. Frontend, en bref

Next.js App Router sous `frontend/src/app/`, groupé en `(auth)` (login, MFA) et `(dashboard)`. Les
groupes de routes du dashboard miroitent de près les sous-systèmes backend (agents, claims,
command-center, federation, governance, investigation, knowledge, local-ai, observability,
platform, security, workflow...) — pour trouver l'UI d'un endpoint backend donné, chercher le
dossier au nom correspondant sous `(dashboard)`. Tous les appels API passent par le client unique
`frontend/src/lib/api-client.ts` (`NEXT_PUBLIC_API_URL`, défaut `http://localhost:8000/api/v1`).

`frontend/src/components/claims/` porte l'essentiel de l'UI documentaire d'un claim :
`NewClaimWizard.tsx` (création + choix upload/saisie manuelle), `ClaimReviewPanel.tsx` (formulaire
fusionné, correction en ligne), `ManualEntryForm.tsx` (saisie manuelle groupée, Cours 3) et
`AgentCollaborationPanel.tsx` (déclenchement des 6 agents, Cours 4-5) — détail complet dans
[`COURS_07_FRONTEND.md`](COURS_07_FRONTEND.md), y compris la vérification effectuée en navigateur
réel contre le vrai backend.
