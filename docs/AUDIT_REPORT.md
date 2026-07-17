# claimOS — Rapport d'audit honnête (Sprint #1)

Date : 2026-07-13
Méthode : audit statique en lecture seule (6 balayages parallèles couvrant pipeline/engines,
IA/Ollama/RAG, modules "enterprise", câblage API, frontend, infrastructure), avec exécution
réelle du pipeline pour confirmer certains constats. Aucune correction n'a encore été appliquée —
ce document précède toute intervention.

**Verdict global : l'affirmation "v1.0.0, plateforme en production" est fausse.** Le pipeline de
traitement de documents censé être le cœur du produit **plante à la 2ᵉ étape sur 18** quand on
l'exécute réellement. Sur ~34 modules d'API et ~22 modules "enterprise", une poignée seulement
fait du vrai travail (DB réelle, calculs réels) ; le reste est soit des littéraux codés en dur,
soit une logique Python réelle qui tourne en mémoire (perdue au redémarrage) sur des données
jamais alimentées. Un bug de sécurité réel (pas seulement une simulation) a été trouvé dans
l'authentification.

Légende : ✅ Fonctionnel réel · ⚠️ Partiel (logique réelle mais donnée/branchement fake, ou état
non persistant) · ❌ Simulé / codé en dur / non implémenté.

---

## 1. Backend — cœur métier (pipeline, engines, persistence)

| Composant | Statut | Constat |
|---|---|---|
| `PipelineOrchestrator` / `DocumentContext` (`app/pipeline/core.py`, `orchestrator.py`) | ✅ | Vraie machine à états (sagas, compensation en ordre inverse). Jamais testée avec la vraie factory : `tests/test_pipeline.py` n'utilise que des mocks maison. |
| Pipeline câblé (`get_document_pipeline()`) | ❌ | **Plante à l'exécution réelle** (`AttributeError: 'ValidationStep' object has no attribute 'name'`) : 4 steps (validation, layout_analysis, classification, evidence_graph) suivent une convention d'interface incompatible avec l'orchestrateur (dict-context sans hériter de `PipelineStep`). Le pipeline "18 étapes enterprise" n'a jamais tourné de bout en bout. |
| Upload, Fingerprint, Storage | ✅ | Logique réelle (hash, écriture disque, rollback). |
| Metadata extraction, Virus scan, Page extraction, Business extraction, Cross-validation, Decision engine (step), Human review, Archiving | ❌ | 7 étapes sont des no-ops ou constantes : scan antivirus toujours `True`, extraction de pages toujours "2 pages", extraction métier = `{"stub_field": "stub_value"}`, décision toujours `HITL_REVIEW`, etc. |
| OCR (`app/engines/ocr/`) | ✅ | Adaptateurs réels (pytesseract, doctr, paddleocr). `mock_adapter.py` a bien été supprimé, mais `steps/ocr.py:49` référence encore la clé `"mock"` (code mort/cassé). |
| IQA, Preprocessing (`app/engines/iqa`, `preprocessing`) | ✅ | Vrais calculs OpenCV/scikit-image (flou, exposition, bruit, binarisation Sauvola). Un score "quality_gain" est une heuristique fake (`len(ops)*0.1`). |
| Classification (`app/engines/classification/`) | ❌ | Classifieurs auto-documentés comme mocks (`classifier.py:9,20,34`) : matching de mots-clés ("facture"/"tva"), aucun modèle ML chargé. |
| Extraction (`app/engines/extraction/`) | ⚠️ | Seulement 2 extracteurs réels (plaque, n° police) sur toute la richesse du schéma de données. |
| Decision / Evidence Graph / Validation (engines) | ⚠️ | Architecture réelle et la plus aboutie du repo, mais **jamais atteinte** car le pipeline plante avant, et le `DecisionEngineStep` réellement câblé les ignore. |
| Ingestion, resolution, rules (`app/engines/ingestion|resolution|rules`) | ❌ | Packages vides, aucune implémentation. |
| Persistence réelle (`app/core`, `app/models`, `app/repositories`) | ✅ | SQLAlchemy réel, schéma cohérent avec les migrations Alembic (2 revisions, correspondance vérifiée table par table). |
| Persistence fantôme (`app/persistence/*`) | ❌ | **Deuxième stack complète et orpheline** : Base déclarative distincte, modèles distincts (`Tenant`, `User`, `Role`, `Claim`, `Document`), DB par défaut = **SQLite en mémoire** (perdue à chaque arrêt), aucune migration, `seeder.py` contient un appel SQLAlchemy invalide (plante à l'exécution) et un mot de passe "hashé" qui ne l'est pas. |

## 2. Backend — API (câblage des ~34 modules d'endpoints)

Seuls **5 modules sur 34 sont réellement adossés à la base de données** : `claims`, `validation`,
`lookups`, `health`, `app/review/review_router.py`. Tous les autres délèguent à des classes
Python réelles mais **purement en mémoire** (singletons process-local, état perdu au redémarrage) :

- ✅ Réels et persistants : `claims.py`, `validation.py`, `lookups.py`, `health.py`, `review_router.py`.
- ⚠️ Logique réelle, état non persistant ou branché sur des données fake : `decision.py` (1 route réelle, 4 statiques), `agents.py`, `llm.py`, `monitoring.py`, `workflows.py`, `simulation.py`, `governance.py`, `local_ai.py`, `agentic_ai.py`, `collaboration.py`, `investigation.py`, `ai_governance.py`, `platform_sdk.py`, `ollama.py`.
- ❌ Codé en dur / simulé de bout en bout : `learning.py` (4/6 routes), `knowledge.py` (réponse "LLM" = template f-string), `platform.py` (backup toujours "14GB / COMPLETED"), `devops.py`, `federation.py`, `command_center.py` (KPI littéraux, `/operations` toujours "ALL_SYSTEMS_NOMINAL"), `live_logs.py` (logs `random.choice()` sur 5 lignes canned, auto-documenté comme simulation), `mcp.py` (marketplace = 1 entrée en dur), `observability.py` (`get_anomalies` rejoue toujours le même état fake), `optimization.py`, `integrations.py` (webhook = stub qui renvoie l'entrée), `analytics.py` (fallback caché avec des chiffres fabriqués si la vraie requête DB échoue — masque silencieusement les pannes).

**Bug de sécurité critique** : `auth.py` — le login ne vérifie **jamais le mot de passe** (le champ
est récupéré puis ignoré) ; n'importe quel mot de passe passe si l'email correspond à un compte
actif. Le `/mfa/verify` compare à la constante `"123456"` au lieu du moteur TOTP réel. Ce n'est pas
une simulation, c'est une vulnérabilité d'authentification exploitable dès aujourd'hui.

## 3. Backend — modules "enterprise / vision" (22 modules, ~45 phases annoncées)

| Statut | Modules |
|---|---|
| ✅ Réel et de bonne qualité | `app/review/` (~95% réel, seul module vraiment production-ready), `app/collaboration/` (verrouillage optimiste réel, WebSocket réel), `app/governance/` (chiffrement Fernet réel, détection PII réelle, audit log réel — mais rien ne persiste en DB) |
| ⚠️ Logique réelle sur données jamais peuplées / non persistante | `app/devops/`, `app/analytics/` (agrégations réelles mais data lake jamais alimenté en prod), `app/simulation/` (Monte Carlo réel mais moteur de décision = table à 4 branches), `app/workflows/` (DAG async réel mais `ServiceTask.execute` est un no-op — chaque tâche "réussit" instantanément sans rien faire), `app/integration/` (circuit breaker réel, mais les connecteurs Salesforce/SAP renvoient l'input en écho, aucun appel HTTP réel), `app/learning/` (~85% d'algorithmes réels, contournés par l'endpoint), `app/optimization/` (le plus abouti des modules vision), `app/platform/`, `app/security/` (crypto réelle mais intégration cassée, cf. bug auth ci-dessus), `app/mcp/` (partagé entre réel et "Simulates"/"Mock" explicites), `app/acos/`, `app/agentic_ai/`, `app/autonomous/` (contrôle de flux réel enrobant des résultats truqués, ex. un benchmark de labo dont le gagnant est biaisé par un bonus fixe) |
| ❌ Quasi entièrement fake | `app/investigation/` (9/9 fichiers ignorent leurs paramètres d'entrée), `app/federation/` (8/9 fichiers statiques), `app/model_registry/` (8/12 fichiers renvoient la même sortie canned pour n'importe quel modèle), `app/sdk/` (tests toujours "PASS/45 tests"), `app/command_center/` (KPI littéraux confirmés), `app/observability/` (nouveaux fichiers `aiops.py`/`slo.py`/`health.py`/`costs.py` hardcodés — à distinguer de `metrics.py`/`tracing.py` qui sont, eux, réellement branchés à Prometheus/OpenTelemetry) |

**Sur les tests** : de nombreux modules ont des tests qui vérifient les mêmes littéraux codés en
dur que le code produit — tautologiques. Plusieurs fichiers de test contiennent des commentaires
explicites visant un quota externe de nombre de tests (ex. `tests/federation/test_federation.py`
mentionne littéralement *"pour répondre à l'exigence stricte de '82 tests validés'"*), ce qui
confirme que les tests ont été écrits pour satisfaire un chiffre, pas pour valider un comportement.

## 4. IA (agents, LLM, Ollama, RAG, Neo4j)

| Composant | Statut | Constat |
|---|---|---|
| Agents existants | ❌ | Seuls 2 agents existent (`fraud_agent.py`, `ocr_supervisor.py`) sur toute la promesse multi-agents. Aucun des deux n'appelle un LLM. `OCRSupervisorAgent` renvoie un texte de facture codé en dur. `FraudAgent` fait un simple test de sous-chaîne (`"fake" in texte`). |
| Orchestration (registry/planner/scheduler/eventbus) | ⚠️ | Vraie exécution asynchrone en DAG avec dépendances — mais le planner est un DAG figé en dur, et référence des agents (`classification_supervisor`, `validation_supervisor`) qui n'existent pas. |
| PlanningEngine / ReasoningEngine ("Cognitive AI") | ❌ | Auto-documentés `"(mocked)"` / `"Simulates autonomous reasoning"` — if/else sur mots-clés, conclusions/justifications en dur (ex : une "détection de cycle de fraude" est une phrase littérale, pas un vrai calcul de graphe). |
| `OllamaProvider` | ✅ | Vrai client httpx (chat, streaming, embeddings, health check) sur `/api/chat`, `/api/embeddings`, `/api/tags`. |
| Routage LLM (`LLMManager._select_provider`) | ❌ | Routage par sous-chaîne sur le nom du modèle (`"llama"→Ollama`, sinon → **Mock**). **Aucun appel réel dans le code ne demande un modèle contenant "llama"** — tout finit sur `MockProvider`, qui renvoie littéralement `"This is a mocked response."`, silencieusement, sans erreur visible. |
| OpenAI / Anthropic / Gemini providers | ❌ | 100% `NotImplementedError` sur `generate`/`stream`/`embed`. |
| Embeddings (RAG) | ❌ | `EmbeddingsEngine` route vers Mock → vecteurs `random.random()` 384 dims. **La recherche vectorielle "sémantique" tourne du cosinus réel sur du bruit.** |
| PgVectorStore, BM25Index, RRF (`app/knowledge/`) | ✅ (logique) / ❌ (données) | Vraie requête pgvector, vrai BM25 (Okapi), vraie fusion Reciprocal-Rank — tout ceci opère sur des embeddings fake, donc inutile en pratique. |
| `app/vector/*` (2ᵉ pipeline RAG, exposé par `/knowledge/hybrid-search`) | ❌ | Store en mémoire (liste Python) malgré un commentaire promettant une DB ; embeddings = hash déterministe du texte, pas une vraie sémantique ; la "réponse LLM" est un template f-string, aucun LLM appelé. |
| Neo4j (`app/graph/`) | ⚠️ | Vrai driver/Cypher quand Neo4j est joignable, mais bascule **silencieusement et définitivement** vers un graphe en mémoire (`networkx`) au moindre échec, sans retry ni alerte. Port bolt par défaut non standard (7688) et jamais configuré dans `.env.example`. Le pipeline de sinistres n'écrit jamais dans ce graphe — les "anneaux de fraude" détectés tournent sur un graphe systématiquement vide en usage réel. |

## 5. Base de données

- ✅ **Stack réelle** : Postgres + pgvector, modèles SQLAlchemy dans `app/models/`, migrations
  Alembic à jour et cohérentes avec le schéma déclaré (vérifié table par table).
- ❌ **Stack fantôme** : `app/persistence/*` déclare un second schéma (tenants/users/roles/claims/
  documents) jamais migré, avec un fallback silencieux vers SQLite en mémoire — inutilisable en
  production tel quel, et contenant un bug d'exécution (`seeder.py`).
- ⚠️ Neo4j configuré mais jamais réellement peuplé par le flux métier ; port par défaut incohérent
  avec la config docker-compose (7687 vs 7688).
- ⚠️ La quasi-totalité des "moteurs enterprise" (fédération, command center, devops, observability,
  gouvernance, plateforme...) gardent leur état dans des dictionnaires Python de classe — rien de
  tout cela ne survit à un redémarrage, malgré l'apparence d'un système d'état persistant.

## 6. Sécurité

- ❌ **Auth bypass critique** : `auth.py` ne vérifie jamais le mot de passe soumis au login.
- ❌ MFA : vérification contre une constante `"123456"` au lieu du moteur TOTP réel existant.
- ⚠️ JWT réel (jose/HS256) mais secret signé en dur dans le code source.
- ⚠️ Chiffrement (`governance/encryption`) réellement implémenté (Fernet + fallback XOR) mais clés
  gardées en mémoire seulement (perdues au redémarrage, pas de KMS).
- ⚠️ RBAC/ABAC, détection PII, audit log à chaînage de hash : logique réelle mais aucune
  persistance en base.
- ❌ Scan de sécurité (`devops/security.py`) : synthétique, ne scanne rien de réel.

## 7. Frontend

Sur 19 routes du dashboard, **seules 3 appellent une API**, et **1 seule** (`/claims`) est
réellement adossée de bout en bout à la base de données.

| Route | Statut |
|---|---|
| `/claims` | ✅ Réel, erreur affichée honnêtement en cas d'échec |
| `/` (dashboard exécutif), `/agents` | ⚠️ Appelle une vraie API mais **masque silencieusement toute erreur réseau** en substituant des chiffres codés en dur (aucun indicateur visible pour l'utilisateur) |
| `/collaboration` | ⚠️ Vrais endpoints mais état backend en mémoire (non persistant), room ID codé en dur côté client |
| `/command-center`, `/federation`, `/governance`, `/investigation`, `/developer`, `/platform`, `/security`, `/ai-runtime`, `/observability` | ❌ Aucun appel API — JSX 100% statique, y compris quand un backend "réel" existe (mais lui-même fake) |
| `/knowledge`, `/lab`, `/local-ai`, `/monitoring`, `/workflow`, `/analytics` | ❌ Pages "Under Construction", aucune logique |
| `(auth)/login`, `(auth)/mfa` | ❌ Formulaires sans `onSubmit`, purement décoratifs — **on ne peut littéralement pas se connecter via l'UI aujourd'hui** |

Aucun hook TanStack Query n'est utilisé nulle part dans `(dashboard)` malgré sa présence dans les
dépendances — tout passe par `useEffect` + `fetch` manuel + `useState`.

**Anomalie à vérifier séparément** : `frontend/AGENTS.md` contient une instruction demandant de
lire `node_modules/next/dist/docs/` avant d'écrire du code — sans rapport avec ce dépôt, à
inspecter (provenance du fichier).

## 8. Infrastructure

- ❌ **Le build Docker du backend est cassé** : `docker/backend/Dockerfile` copie un
  `requirements.txt` qui n'existe pas (le projet utilise Poetry) — `docker compose build` échoue
  immédiatement sur le backend.
- ✅ Dockerfile frontend, nginx.conf, docker-compose.yml (racine) : cohérents et fonctionnels
  (une fois le Dockerfile backend corrigé).
- ❌ **Helm** : dossier `templates/` totalement vide — `helm install` ne déploierait rien.
- ❌ **GitOps** : dossier vide, aucune config ArgoCD/Flux.
- ⚠️ **Kubernetes** : seulement 5 manifestes (namespace, configmap, backend, ollama, hpa) —
  ni Postgres/Redis/Neo4j, ni Service, ni Ingress, ni Secret (référencé mais jamais défini),
  ni déploiement frontend. Image `claimos/backend:v1.0.0` jamais construite ni poussée nulle part.
- ❌ **CI/CD** : le job `build-push` n'exécute que des `echo` — les commandes `docker build`/`push`
  sont commentées. Aucune image n'atteint jamais un registre. **Zéro CI pour le frontend**
  (ni lint, ni build, ni test).
- ⚠️ `infrastructure/docker-compose.yml` décrit une architecture parallèle (Kafka, Temporal,
  Qdrant, ELK) totalement déconnectée du code réel — non invoquée par le Makefile ni la CI.
- ✅ Alembic / migrations : réelles et cohérentes avec le schéma applicatif.

---

## Ce qui est réellement terminé

- Persistance principale (Postgres + SQLAlchemy + Alembic) pour les claims, documents,
  validations — schéma et migrations cohérents.
- OCR, IQA, Preprocessing : vrais traitements d'image (pytesseract/doctr/paddleocr, OpenCV,
  scikit-image).
- `OllamaProvider` : vrai client HTTP (chat, streaming, embeddings, health check).
- `PgVectorStore` / `BM25Index` / fusion RRF : vraie logique de recherche hybride (mais nourrie de
  données fake, cf. plus bas).
- `app/review/` : module de revue humaine, seul module "enterprise" quasiment production-ready.
- `/claims` (API + frontend) : le seul flux complet, bout en bout, réel.
- `app/collaboration/` : verrouillage optimiste et WebSocket réels.
- `app/governance/` : chiffrement, détection PII, audit log à chaînage de hash — réels en logique.
- CI backend (job `test`) : exécute réellement `pytest`.

## Ce qui ne l'est pas

- Le pipeline de traitement de documents "18 étapes" — **plante à l'exécution**, jamais testé
  intégralement.
- Le déploiement production (Docker backend cassé, Helm vide, GitOps vide, k8s incomplet,
  CI qui ne publie jamais d'image).
- L'authentification (mot de passe jamais vérifié, MFA hardcodée).
- Le frontend au-delà de `/claims` (16 des 19 routes sont statiques ou des stubs "Under
  Construction").
- La quasi-totalité des modules "vision" (federation, command_center, investigation,
  model_registry, sdk, mcp marketplace, observability aiops/slo) : purement décoratifs.

## Ce qui était simulé

- Tous les agents IA (fraud/OCR) — aucun appel LLM.
- Le "raisonnement cognitif" (PlanningEngine/ReasoningEngine) — auto-documenté "(mocked)"/"Simulates".
- Le fallback LLM par défaut — toute requête ne contenant pas "llama" dans le nom du modèle
  reçoit `"This is a mocked response."`, silencieusement.
- Les embeddings par défaut — vecteurs aléatoires, pas de sémantique réelle.
- `/knowledge/hybrid-search` — réponse "IA" = template de chaîne de caractères.
- Les KPI de command_center, federation, model_registry, sdk — littéraux codés en dur.
- Les logs "live" (`live_logs.py`) — `random.choice()` sur 5 lignes fixes, auto-documenté comme
  faute d'event bus réel.
- Les tests de plusieurs modules — écrits pour satisfaire un quota de nombre de tests ("82 tests
  validés"), pas pour valider un comportement.

## Ce qui a été corrigé

- **Le pipeline câblé ne plante plus.** Le bug d'interface (4 étapes écrites contre une
  convention `dict` incompatible avec l'ABC `PipelineStep`/`DocumentContext` attendue par
  l'orchestrateur) est corrigé : `LayoutAnalysisStep`, `ClassificationStep`, `EvidenceGraphStep`
  et l'étape de validation croisée sont réécrites sur la bonne interface, en réutilisant les
  vrais moteurs déjà existants (`LayoutEngine`, `ClassificationEngine`, `EvidenceGraphEngine`,
  `ValidationEngine`).
- **`ValidationStep` mal positionné (position 2, avant même l'evidence graph) supprimé** —
  sa vraie logique (génération du `ValidationReport` à partir de l'evidence graph) est
  maintenant exécutée à la bonne étape, `CrossValidationStep` (position 14), qui était
  auparavant un simple `return context` sans logique.
- **`BusinessExtractionStep`** ne renvoie plus `{"stub_field": "stub_value"}` — il appelle
  réellement `ExtractionEngine` (extracteurs plaque d'immatriculation + n° de police).
- **`DecisionEngineStep`** ne renvoie plus systématiquement `"HITL_REVIEW"` codé en dur — il
  appelle réellement `DecisionEngine` (risque, stratégies, routage, SLA, audit) sur le
  `ValidationReport` et l'`EvidenceGraphResult` produits en amont ; le repli vers
  `HITL_REVIEW` ne survient plus que si une étape amont a effectivement échoué (dégradation
  honnête, plus un mensonge silencieux).
- **Référence morte à un adaptateur OCR `"mock"` supprimée** de `steps/ocr.py` (l'adaptateur
  avait été supprimé du code mais la clé restait référencée).
- **Suppression des 3 fichiers dupliqués/orphelins** (`steps/validation.py`,
  `steps/entity_extraction.py`, `steps/decision.py`) dont la logique réelle a été fusionnée
  dans les étapes correctement câblées ci-dessus — ils n'étaient importés nulle part ailleurs
  (vérifié) et duplicaient, sur une interface incompatible, exactement ce que les étapes
  câblées étaient censées faire.
- **Test de non-régression ajouté** (`tests/test_pipeline.py::test_real_document_pipeline_runs_end_to_end_without_crashing`)
  qui exécute la vraie factory `get_document_pipeline()` — jusqu'ici, seuls des mocks
  maison étaient testés, ce qui explique comment ce plantage est passé inaperçu.
- **Vérifié par exécution réelle** (pas seulement par les tests) : avec une image contenant du
  texte réel, la chaîne OCR → Layout → Classification → Extraction → Evidence Graph →
  Validation → Decision produit désormais une vraie décision (`AUTO_APPROVED` avec un score de
  confiance réel, un raisonnement explicite), sans aucune donnée fabriquée.
- 961/961 tests passent après ces changements (960 précédemment + le nouveau test), aucune
  régression.

**`PageExtractionStep` est maintenant un vrai rendu de pages (plus un stub à "2 pages" fixes)** :

- PDF → rendu page par page en JPEG réel via PyMuPDF (nouvelle dépendance `pymupdf`, ajoutée à
  `pyproject.toml`/`poetry.lock`) à 300 DPI, un fichier image réel par page sur disque.
- Image (JPEG/PNG) uploadée directement → utilisée telle quelle comme unique page, sans copie
  inutile.
- PDF invalide/corrompu → `PipelineError` FATAL explicite (plus de silence : avant, un payload
  invalide produisait quand même "2 pages" fantômes qui n'existaient pas sur disque, ce qui
  faisait ensuite planter IQA/OCR plus loin dans la chaîne).
- `compensate()` supprime réellement les images de pages rendues en cas d'échec ultérieur
  (rollback saga), sans jamais supprimer le fichier original uploadé.
- **Vérifié par exécution réelle** avec un vrai PDF à 2 pages contenant du texte : rendu réel des
  2 pages, OCR réel, et extraction réelle d'une plaque d'immatriculation (`AB-123-CD`, confiance
  0.8) directement depuis le texte OCR — chaîne complète sans une seule erreur. Idem avec un
  upload JPEG direct.
- Test de régression mis à jour pour construire un vrai PDF minimal (via PyMuPDF) plutôt qu'un
  payload factice — l'ancien payload bidon `b"%PDF-1.4 fake"` était accepté par l'ancien stub
  mais est maintenant, à raison, rejeté comme PDF invalide.
- `backend/uploads/` (stockage local des fichiers uploadés et pages rendues) ajouté au
  `.gitignore` — ce n'était pas le cas avant.

**Ce qui N'A PAS été corrigé dans ce sprint (hors périmètre)** :
`MetadataExtractionStep`, `VirusScanStep`, `HumanReviewStep`, `ArchivingStep` restent des
no-ops ; le bug d'authentification, le frontend statique, et l'infra de déploiement cassée
ne sont pas traités ici.

## Sprint #3 — IA / ML (tout le pipeline LLM, agents, RAG)

Chantier complet sur tout ce qui touche à l'IA/ML, en 8 étapes, chacune vérifiée par exécution
réelle (pas seulement des tests) contre une vraie instance Ollama locale (qwen2.5-coder:14b,
llama3, mxbai-embed-large) et un vrai Postgres/pgvector :

1. **Gateway LLM honnête** (`app/llm/manager.py`) : le routage ne retombe plus jamais
   silencieusement sur un `MockProvider` — supprimé de la codebase de production (il vivait dans
   `app/llm/providers/`, auto-découvert comme un vrai fournisseur). Toute requête vers un provider
   non configuré/joignable lève maintenant une exception explicite (`LLMProviderUnavailableError`).
2. **OpenAI / Anthropic / Gemini réellement implémentés** (appels HTTP réels, plus de
   `NotImplementedError`) — fonctionnels si une clé API est configurée, sinon échec explicite et
   documenté (`ProviderNotConfiguredError`) plutôt qu'un stub silencieux.
3. **Embeddings** : le modèle par défaut pointait vers un nom OpenAI mort qui retombait sur des
   vecteurs aléatoires. Il pointe maintenant vers le vrai modèle Ollama (`mxbai-embed-large`,
   1024 dimensions) — ce qui a révélé et corrigé un **vrai bug caché** : la colonne pgvector
   (`knowledge_chunk.vector_embedding`) était dimensionnée à 384 (calibrée sur le mock), donc
   l'insertion de vrais embeddings aurait toujours échoué. Migration Alembic appliquée.
4. **Agents réellement fonctionnels** : `OCRSupervisorAgent` appelle maintenant le vrai moteur OCR
   (au lieu de renvoyer un texte de facture codé en dur) ; `FraudAgent` appelle un vrai LLM avec un
   raisonnement réel (au lieu d'un test de sous-chaîne "fake"/"photoshop"). Vérifié avec une vraie
   image générée à la volée : OCR réel → raisonnement LLM réel → score de fraude réel.
5. **Planning/Reasoning "Cognitive AI"** (`PlanningEngine`, `ReasoningEngine`) : auto-documentés
   `"(mocked)"`/`"Simulates"` dans le code d'origine, remplacés par de vrais appels LLM avec
   parsing JSON structuré (schéma imposé, plus de if/else figé).
6. **Stack RAG dupliquée et fake consolidée** : `app/vector/similarity_engine.py` (embeddings
   pseudo-aléatoires par hash de texte) et `app/vector/repository.py` (liste Python en mémoire
   malgré un commentaire promettant une DB) sont maintenant réels — nouvelle table Postgres
   `tenant_embedding` (migration Alembic) avec vraie recherche pgvector. `hybrid_rag.py` ne dump
   plus tout le graphe Neo4j sans condition (`MATCH (n) RETURN n`) — filtre maintenant par entités
   détectées dans la requête, avec LIMIT ; sa "réponse LLM" (un f-string qui comptait juste les
   sources) est remplacée par un vrai appel LLM grounded sur le contexte récupéré.
7. **Tests qui validaient la fakerie comme "correcte" corrigés** : plusieurs tests asserraient
   littéralement `provider_name == "Mock"` ou `"mocked" in summary` comme comportement attendu.
   Réécrits pour valider un comportement réel, avec un marqueur `skipif` explicite (visible, pas
   silencieux) quand Ollama n'est pas joignable localement — pertinent car la CI actuelle n'a pas
   de service Ollama.
8. **Suite complète exécutée deux fois contre Ollama réel** : 3 échecs transitoires (timeouts
   httpx à 60s sous contention, en enchaînant des dizaines d'appels réels à un modèle 14B) —
   chacun repasse individuellement. Corrigé à la racine (timeout Ollama porté à 120s, aligné sur
   la réalité de l'inférence locale) plutôt que masqué. **964/964 tests passent** après ce correctif,
   deux exécutions complètes consécutives.

**Ce qui reste explicitement hors périmètre de ce sprint** : le pipeline de traitement de
documents utilise toujours `PageExtractionStep` (déjà corrigé au sprint précédent) mais
`MetadataExtractionStep`/`VirusScanStep`/`HumanReviewStep`/`ArchivingStep` restent des no-ops ;
Neo4j n'est jamais peuplé par le flux métier réel des sinistres (seulement testé isolément) ; les
~22 modules "vision" (federation, command_center, investigation...) ne sont pas concernés par ce
sprint IA/ML ; le bug d'authentification (mot de passe jamais vérifié) reste ouvert.

## Ce qui reste à développer

Compte tenu de l'ampleur (~34 modules API, ~22 modules "enterprise", pipeline à réparer,
authentification à sécuriser, déploiement à reconstruire), une remise à plat complète en un seul
passage n'est pas réaliste. Priorisation proposée, à valider :

1. **Sécurité immédiate** : corriger la vérification de mot de passe et la MFA dans `auth.py` —
   c'est une vulnérabilité active, pas un chantier de "réalisme".
2. **Réparer le pipeline câblé** (interface `PipelineStep` incohérente) pour qu'il tourne au moins
   sans planter, avant de décider quelles étapes remplacer par du vrai traitement.
3. **Décider du sort de la stack de persistance fantôme** (`app/persistence/*`) : la supprimer ou
   la fusionner avec la vraie stack — elle ne doit pas rester comme piège en SQLite mémoire.
4. **LLM réel** : soit configurer et router réellement vers Ollama (le seul provider implémenté),
   soit implémenter un des providers cloud stubés — mais ne pas laisser le fallback silencieux vers
   `MockProvider` en routage par défaut.
5. **Frontend** : décider quelles routes "vision" (federation, command-center, investigation...)
   sont un vrai besoin produit à construire, versus à retirer — les garder comme démo statique
   sans le dire à l'utilisateur est le problème central de ce rapport.
6. **Infrastructure de déploiement** : corriger le Dockerfile backend, compléter ou supprimer
   Helm/k8s/GitOps selon la cible réelle de déploiement, et faire produire une vraie image par la CI.
7. **Modules "vision"** (acos, agentic_ai, autonomous, command_center, federation, investigation,
   model_registry, sdk, mcp, devops, observability aiops/slo) : chacun nécessite une décision
   produit — vrai chantier futur, vitrine à assumer explicitement, ou suppression. Ce n'est pas
   un simple "bug à corriger", c'est un choix de périmètre.

Cette priorisation reste à valider avec vous avant toute implémentation, comme convenu.

## Sprint #4 — Passe de préparation à la livraison (évaluateur technique)

Objectif : que tout ce qui est présenté comme fonctionnel le soit vraiment, et que ce qui ne l'est
pas soit clairement retiré ou étiqueté plutôt que simulé. Vérifié par exécution réelle à chaque
étape (build Docker exécuté et testé, pas juste inspecté ; requêtes HTTP réelles, pas des appels
Python internes).

1. **Sécurité auth** (déjà détaillé plus haut, sprint courant) : mot de passe vérifié pour de
   vrai, MFA TOTP réel avec enrollment fonctionnel, clé JWT non codée en dur, verrouillage après
   échecs répétés.
2. **Frontend login/MFA** : formulaires réels branchés sur l'API, store d'auth (zustand) qui
   attache le token à tous les appels suivants.
3. **Build Docker backend réparé** : référençait un `requirements.txt` inexistant (le projet
   utilise Poetry) et une image Python 3.11 alors que le code exige 3.13+. Corrigé, **testé par un
   vrai build + démarrage de conteneur** : le healthcheck répond 200, tesseract et pymupdf
   fonctionnent dans l'image.
4. **Audit honnêteté frontend** : découverte en cours de route que plusieurs pages considérées
   "statiques" par l'audit initial avaient déjà été réellement branchées entre-temps (probablement
   par un processus IDE en arrière-plan) — l'état a été revérifié page par page avant toute
   correction plutôt que de se fier à l'audit précédent. Un composant `RoadmapBanner` réutilisable
   a été ajouté à chaque page qui mélange encore des sections réelles et des sections illustratives
   (command-center, federation, governance, investigation, developer, platform, security,
   ai-runtime, observability, settings, collaboration), avec une phrase précise sur ce qui est réel
   vs illustratif dans **cette page spécifique** plutôt qu'un simple label générique. Les deux
   masquages silencieux d'erreur identifiés dans l'audit initial (dashboard et console agents qui
   substituaient des chiffres fabriqués sur échec réseau) ont été supprimés au profit d'un vrai
   message d'erreur visible.
5. **Page Knowledge Base reconnectée pour de vrai** : appelait un endpoint (`/investigation/search`)
   confirmé entièrement fake (résultats fixes ignorant la requête). Plutôt que d'étiqueter, elle a
   été rebranchée sur le vrai moteur hybride construit lors du sprint IA/ML précédent
   (`/knowledge/hybrid-search` — vrais embeddings, vraie recherche pgvector, vrai LLM). Au passage,
   un **vrai bug de routage** a été découvert et corrigé : ce router n'avait aucun préfixe, donc
   l'endpoint vivait en réalité à `/api/v1/hybrid-search` et non `/api/v1/knowledge/hybrid-search`
   comme son nom le laissait supposer.
6. **Audit honnêteté API** : ajout d'un marqueur `_data_source` explicite dans les réponses JSON
   des endpoints qui fabriquent des données en dict (command-center overview/kpis/recommendations/
   situation/operations, federation replication/mesh/disaster-recovery/governance, investigation
   graph) — détectable par n'importe quel client, pas seulement ce frontend. Les endpoints qui
   renvoient des listes n'ont pas été ré-enveloppés (risque de casser le contrat frontend existant
   `Array.isArray`) ; leur nature illustrative reste documentée ici et dans la bannière frontend
   correspondante.
7. **Masquage silencieux corrigé côté serveur** : `/analytics/dashboards` retombait sur des
   métriques fabriquées en dur (`claims_processed: 1247`, etc.) à la moindre exception, y compris
   une vraie panne DB — masquant silencieusement les pannes réelles derrière des chiffres crédibles.
   Remplacé par une erreur HTTP 502 explicite et loggée.
8. **Vérification finale** : suite de tests complète exécutée deux fois après l'ensemble de ces
   changements — **970/970 tests passent**, aucune régression. Build frontend propre. Flux complet
   testé en conditions réelles via HTTP : login → token réel → liste de claims authentifiée →
   recherche hybride avec vraie réponse LLM → pipeline documentaire complet → décision réelle.

### Ce qui reste explicitement hors périmètre après ce sprint

- Helm (templates vides), GitOps (dossier vide), k8s (manifestes incomplets : pas de Secret, pas
  de Service/Ingress, pas de Postgres/Redis/Neo4j) — non traités, décision de périmètre de
  déploiement à prendre séparément.
- CI ne publie toujours aucune image (job `build-push` en no-op) et n'exécute aucun lint/build
  frontend.
- Les ~22 modules "vision" restants (federation au-delà de ce qui a été corrigé, model_registry,
  sdk, mcp, devops, observability aiops/slo...) gardent leur état en mémoire (perdu au redémarrage)
  et fabriquent en partie leurs données — chacun nécessite une décision produit propre, pas un
  correctif mécanique.
- `MetricsService` (dashboard) contient encore une approximation documentée mais non corrigée :
  `active_agents` et `fraud_prevented` sont partiellement dérivés de vraies données (ex. un vrai
  compte de fraudes) multipliées par une constante non calibrée — moins grave que le masquage
  silencieux corrigé au point 7, mais pas une vraie mesure.
- Le pipeline documentaire garde des étapes no-op (`MetadataExtractionStep`, `VirusScanStep`,
  `HumanReviewStep`, `ArchivingStep`) — signalées, non corrigées, hors périmètre de ce sprint.

**En résumé pour un évaluateur technique** : le cœur du produit (auth, pipeline documentaire, IA/
LLM/RAG, page claims, login/MFA, build Docker backend) est maintenant réel et vérifié par
exécution, pas seulement par inspection de code. Le reste du frontend "vision" est honnêtement
étiqueté plutôt que simulé. L'infrastructure de déploiement (Helm/k8s/GitOps/CI) et une partie des
modules "enterprise" secondaires restent un chantier ouvert et documenté, pas caché.

## Sprint #5 — Le JWT était émis mais jamais vérifié

Découvert en observant l'app tourner : le header affichait "Jane Doe / Executive AI Director"
codé en dur (`Topbar.tsx`), sans rapport avec le vrai utilisateur connecté. En creusant, un
constat plus sérieux : **aucun endpoint de l'API ne vérifiait le token JWT émis au login** —
`/auth/login` délivrait un vrai token, mais rien ne l'exigeait ni ne le validait ensuite. N'importe
quel endpoint restait appelable sans authentification.

Corrigé :
- Nouvelle dépendance FastAPI `get_current_operator` (`app/api/v1/dependencies.py`) qui valide
  réellement le Bearer token, résout l'opérateur réel en base, et rejette (401) token manquant,
  invalide, expiré, ou opérateur inactif/inexistant.
- Nouvel endpoint `GET /auth/me` retournant le vrai opérateur authentifié.
- Dépendance appliquée aux endpoints métier réels : `claims` (create/list/get), `validation`
  (report/issues/statistics/run), `decision` (get/history/explanations/audit/run), et tout le
  router `review` (inbox/session/lock/unlock/correct/approve).
- Frontend : `Topbar` affiche maintenant le vrai nom/rôle via `/auth/me`, avec un vrai bouton
  déconnexion. `AuthGuard` ajouté sur le layout dashboard — redirige vers `/login` si aucun token.
  Le faux indicateur de notification (point rouge sans donnée réelle derrière) a été retiré au
  passage.
- 6 nouveaux tests (401 sans token, 401 avec token invalide, 200 avec vrai token, `/auth/me`
  retourne le bon opérateur). **975/975 tests passent.** Vérifié en conditions réelles via HTTP :
  requête sans token → 401 ; login réel → token → `/claims` et `/auth/me` répondent 200 avec les
  vraies données.

**Périmètre non couvert** : seuls les endpoints métier "réels" (claims, validation, decision,
review) sont protégés — les ~30 autres modules d'endpoints ("vision"/enterprise, déjà étiquetés
comme illustratifs côté frontend) restent librement accessibles sans token. Étendre la protection
à l'ensemble de l'API est un choix de périmètre distinct, pas traité ici.

## Sprint #6 — Le pipeline documentaire et le Form Mapping Engine tournaient dans le vide

Point de départ : deux nouveaux engines avaient été construits (extracteurs `national_id`,
`owner_name`, `vehicle_brand` ; `FormMappingEngine` qui fusionne les extractions de plusieurs
documents d'un dossier en un `ClaimOpeningForm` provenancé champ par champ) — tous les deux
unitairement testés et réels dans leur logique, mais **jamais appelés avec de vraies données de
sinistre**. En creusant pourquoi : `get_document_pipeline()` (18 étapes, OCR réel, extraction
réelle) n'était invoqué nulle part dans l'API — seulement depuis un script manuel
(`scripts/test_pipeline_e2e.py`) et les tests. Aucun code, nulle part, ne construisait jamais une
ligne `ClaimDocument` en base : le dépôt-repository existait, mais rien ne l'appelait. Les deux
moteurs étaient donc orphelins, chacun correct isolément, mais sans aucun chemin réel les reliant à
un sinistre.

Corrigé :
- **Persistance des documents connectée pour de vrai** : migration Alembic ajoutant
  `document_role` et `extracted_data` (JSONB) à `claim_document`. Nouveau
  `DocumentService.ingest_document()` exécute la vraie pipeline sur un fichier uploadé, fusionne
  les résultats d'extraction par page en un seul `ExtractionResult` par document
  (`app/engines/extraction/merge.py`), résout/crée le `DocumentType` correspondant à la famille
  prédite par la classification (table `document_type` non pré-alimentée — get-or-create plutôt
  que d'échouer sur toute famille encore jamais vue), et persiste la ligne `ClaimDocument` réelle.
- **Nouveaux endpoints réels** : `POST /claims/{id}/documents` (upload multipart, exécute la
  pipeline réelle, tag optionnel du rôle du document — OWN_VEHICLE/ADVERSE_VEHICLE/POLICY_HOLDER/
  VICTIM) et `GET /claims/{id}/documents/opening-form` (charge tous les documents persistés du
  sinistre, reconstruit leurs `ExtractionResult`, et appelle `FormMappingEngine` pour produire le
  `ClaimOpeningForm` fusionné). Les deux protégés par `get_current_operator`.
- **Deux bugs réels découverts et corrigés en vérifiant par exécution** (pas seulement en lisant
  le code) :
  1. `ClassificationStep` assignait le dict `DocumentClass` entier (au lieu du seul champ
     `family`) à `context.document_type_code` (typé `str | None`) — jamais remarqué car rien
     n'utilisait ce champ jusqu'à ce sprint.
  2. `PolicyNumberExtractor` accédait à `field.label_text`/`field.value_text`, des noms qui
     n'existent pas sur le vrai modèle `FormFieldRegion` (les vrais champs sont `label`/`value`).
     Comme `FormFieldRegion` autorise les champs additionnels (`extra="allow"`), le test unitaire
     de cet extracteur construisait sa fixture avec ces mêmes mauvais noms et "passait" en
     testant un attribut fantôme — jamais le vrai comportement. En production, **cette exception
     faisait échouer l'extraction de tout le document**, pas seulement le champ policy_number :
     `ExtractionEngine.process()` n'isolait pas les extracteurs entre eux. Corrigé aux deux
     niveaux : noms de champs réparés, et chaque extracteur est maintenant exécuté dans son
     propre `try/except` pour qu'un extracteur cassé dégrade (ce seul champ manque) au lieu de
     faire échouer tout le document.
- **Vérifié en conditions réelles via HTTP** (pas seulement via les tests) : serveur démarré,
  vrai login, création d'un vrai sinistre, upload de deux vrais PDF (généré via PyMuPDF, un par
  partie) avec rôles `OWN_VEHICLE`/`ADVERSE_VEHICLE`, récupération du formulaire fusionné —
  plaques, noms et marques des deux véhicules correctement désambiguïsés par rôle, avec
  bounding box, extracteur et document source réels pour chaque champ.
- 12 nouveaux tests (fusion multi-pages, get-or-create du type de document, ingestion HTTP réelle,
  fusion HTTP réelle sur deux documents, 404 sur sinistre inconnu, 401 sans token). **995/995 tests
  passent.**

**Ce qui reste explicitement hors périmètre** : `document_role` doit toujours être renseigné
manuellement par l'appelant (aucun moteur de liaison document → partie n'existe) ; les lignes
`DocumentPage` ne sont pas persistées (seul le document parent l'est) ; `PolicyNumberExtractor`
reste dépendant de la détection de champs de formulaire par le moteur Layout, dont la fiabilité
sur des documents réels variés n'a pas été évaluée dans ce sprint ; `ArchivingStep` reste un
no-op (signalé au sprint #2, toujours vrai).

## Sprint #7 — Extraction haute précision sur tout type de document, et stockage complet

Objectif explicite de l'utilisateur : que l'extraction couvre vraiment tout type de document avec
une précision élevée, et que tout ce qui touche au stockage soit vérifié, pas seulement câblé.
Point de départ (audit à froid, avant toute correction) : seuls 5 champs sur ~40 du
`ClaimOpeningForm` avaient un extracteur (tous regex/layout) ; l'OCR ne tournait qu'en anglais
alors que les paquets de langue française et arabe sont installés localement mais jamais demandés ;
`FIELDS_WITHOUT_EXTRACTOR` avait un vrai bug (le sous-arbre `conducteur.*` en était absent) ;
`DocumentPage` n'était construit nulle part ; `MetadataExtractionStep` et `VirusScanStep`
restaient des stubs no-op, sans aucune librairie antivirus installée.

Corrigé, vérifié par exécution réelle à chaque étape :

1. **OCR bilingue réel** (`app/engines/ocr/adapters/tesseract_adapter.py`) : `pytesseract` ne
   recevait jamais de paramètre `lang` (défaut Tesseract = anglais seul), alors que
   `tesseract --list-langs` confirme `fra`/`ara`/`eng` déjà installés sur la machine. Nouveau
   réglage `OCR_LANGUAGES` (défaut `"fra+ara+eng"`), câblé pour de vrai dans l'appel
   `image_to_data`. Vérifié sur une image réelle contenant du texte français ("Nom du
   souscripteur: MARTIN") — reconnu correctement, ce qui n'était pas garanti en mode anglais seul.

2. **Extracteur LLM générique pour tous les champs restants**
   (`app/engines/extraction/extractors/llm/llm_field_extractor.py`) : les 5 extracteurs
   regex/layout ne couvraient que `vehicle_plate, policy_number, national_id, owner_name,
   vehicle_brand`. Un nouvel extracteur, branché dans le même `ExtractorRegistry` que les autres
   (donc isolé par le try/except par-extracteur du sprint #6), appelle un vrai LLM local (même
   patron que `ReasoningEngine`/`PlanningEngine` : `LLMManager` + `GuardrailsEngine
   .validate_json_output`) avec un prompt structuré demandant ~35 champs (dates, lieu,
   circonstances, informations du conducteur, victimes...) plus une liste de victimes, chacun avec
   sa propre confiance, `null` explicite si absent du texte plutôt qu'une valeur inventée. Comme
   `BaseExtractor.extract()` est synchrone et `LLMManager.generate()` asynchrone, un petit pont
   (`app/engines/extraction/async_bridge.py`) exécute la coroutine dans un thread dédié si une
   boucle asyncio tourne déjà, sinon directement — robuste peu importe le contexte d'appel.
   **Vérifié contre un vrai Ollama local** (pas seulement mocké) : sur un texte de constat
   synthétique, extraction correcte de lieu, date (normalisée en ISO), heure, circonstances,
   identité du conducteur, et distinction correcte entre le conducteur et une victime blessée
   distincte. **Coût réel mesuré : ~60-70 secondes par appel LLM** (modèle 14B local) — ajouté en
   toute franchise ici plutôt que caché : chaque upload de document en subit désormais le coût.
3. **Couverture de champs corrigée et étendue** (`app/engines/form_mapping/manager.py`) : le bug
   du sous-arbre `conducteur.*` absent de `FIELDS_WITHOUT_EXTRACTOR` est résolu en lui donnant une
   vraie couverture plutôt qu'un meilleur message d'erreur — nouveau rôle `DocumentRole
   .ACCIDENT_REPORT` (le constat lui-même, pour les faits au niveau du sinistre, indépendants de
   toute partie), et `FIELD_MAPPING` étendu pour que chaque champ scalaire du schéma ait
   désormais une correspondance réelle. `FIELDS_WITHOUT_EXTRACTOR` est maintenant un ensemble vide
   (gardé comme filet de sécurité pour un futur champ de schéma sans mapping, pas comme
   documentation d'un manque actuel). Nouvelle logique de collecte des victimes
   (`_collect_victims`) : les entités `victime.<index>.<champ>` produites par l'extracteur LLM
   sont regroupées par document et par index pour peupler `form.victimes` (une liste, donc hors du
   mécanisme `MappedField` existant) — non fusionnées entre documents (pas de liaison automatique
   de personnes). `fraud_indicators` reste volontairement hors périmètre : c'est le domaine de
   `FraudAgent`, pas une préoccupation d'extraction par document.
4. **Persistance des pages** (`app/services/document_service.py`) : aucune ligne `DocumentPage`
   n'était jamais construite nulle part dans le dépôt — le rendu par page ne vivait qu'en mémoire
   sur `PageContext` le temps d'une exécution. Chaque page rendue avec une image réelle est
   désormais persistée (`image_uri`, résolution, angle de rotation corrigé, score de qualité réel
   venant de l'IQAEngine). Migration Alembic additionnelle : `ocr_hocr_uri` était `NOT NULL` alors
   qu'aucune étape ne produit de fichier hOCR nulle part dans le code — rendu nullable plutôt que
   d'y forcer une valeur fictive.
5. **`MetadataExtractionStep` réel** (`app/pipeline/steps/metadata.py`) : remplace le stub qui
   posait juste `extracted_native_metadata=True`. Extraction réelle des métadonnées PDF
   (auteur, titre, dates, nombre de pages via PyMuPDF) et EXIF image (marque/modèle d'appareil,
   date de prise de vue via Pillow) ; dégrade proprement (erreur DEGRADED, pas de plantage) sur un
   fichier corrompu, plutôt que de prétendre avoir réussi.
6. **`VirusScanStep` réel via ClamAV** (`app/pipeline/steps/virus_scan.py`) : remplace le stub qui
   posait `virus_scan_passed=True` sans jamais rien scanner. Nouveau service `clamav` dans
   `docker-compose.yml` (image `clamav/clamav:stable`, `platform: linux/amd64` requis sur Apple
   Silicon — aucune image arm64 native n'est publiée), client réel `clamd` (protocole INSTREAM).
   Une infection détectée est **FATAL** (bloque le pipeline, ne stocke jamais le fichier) ; un
   daemon injoignable **DEGRADE** (`virus_scan_passed=None`, avertissement explicite) plutôt que
   de mentir en repassant silencieusement à `True` — la distinction entre "scanné et propre" et
   "jamais scanné" est maintenant réelle. **Vérifié par détection réelle** de la chaîne de test
   standard EICAR (reconnue par tout moteur antivirus réel, y compris ClamAV) : upload EICAR →
   `PipelineError` FATAL avec la signature réelle renvoyée par le démon ; upload propre → passe.
7. **Vérifié en conditions réelles via HTTP** (pas seulement via les tests) : upload d'un constat
   synthétique riche en un seul document tagué `ACCIDENT_REPORT` → pipeline complet exécuté
   (OCR bilingue, classification, extraction regex, extraction LLM, IQA, scan antivirus réel,
   métadonnées réelles) sans aucun avertissement de pipeline → formulaire fusionné avec date,
   lieu, heure et victime correctement extraits et normalisés. `circonstances_accident` n'a pas
   été rempli sur cette exécution précise (variabilité réelle d'un modèle local 14B, pas un bug de
   câblage) — noté ici en toute honnêteté plutôt que masqué.
8. **1015/1015 tests passent** (995 précédents + 20 nouveaux), suite complète exécutée deux fois,
   aucune régression. Durée de la suite complète passée de ~190s à ~493s : coût direct et mesuré
   de l'extraction LLM synchrone désormais exécutée à chaque test qui fait tourner le pipeline
   réel — signalé ici comme compromis assumé, pas comme régression cachée.

**Ce qui reste explicitement hors périmètre** :
- **Latence** : ~60-70s par document à cause de l'appel LLM synchrone dans le pipeline
  synchrone — aucune file d'attente asynchrone/arrière-plan n'a été mise en place ; chaque upload
  HTTP attend la fin complète du LLM avant de répondre. Un vrai chantier de performance
  (traitement asynchrone, file de tâches) serait nécessaire avant une mise en charge réelle.
- Un document ne peut porter qu'un seul rôle à la fois (`document_role`) : un constat amiable
  réel mélange souvent des faits de sinistre ET des informations sur le conducteur/souscripteur,
  mais le rôle `ACCIDENT_REPORT` ne route que les champs de sinistre — les champs `conducteur.*`
  ne sont routés que depuis un document tagué `OWN_VEHICLE`, ce qui a été observé concrètement
  lors de la vérification HTTP de ce sprint (un même document constat n'a pas rempli `conducteur.
  nom` faute d'être aussi tagué `OWN_VEHICLE`).
- `PolicyNumberExtractor` reste dépendant de la détection de champs de formulaire par le moteur
  Layout (signalé au sprint #6, toujours vrai).
- `ArchivingStep` reste un no-op (signalé au sprint #2, toujours vrai).
- La qualité de l'extraction LLM dépend directement du modèle local configuré
  (`OLLAMA_DEFAULT_MODEL`) — aucune évaluation systématique de précision (jeu de test annoté,
  métriques de rappel/précision par champ) n'a été mise en place ; la vérification de ce sprint
  est qualitative (exécutions réelles inspectées manuellement), pas un benchmark chiffré.
- DocT/PaddleOCR restent des adaptateurs présents dans le code mais dont les librairies ne sont
  pas installées (`pyproject.toml`) — seul Tesseract tourne réellement aujourd'hui, désormais en
  mode multilingue.

## Sprint #8 — "New Claim" relié au pipeline réel, plus validation persistée et corrections manuelles

Point de départ : le bouton "New Claim" du frontend n'ouvrait qu'un formulaire manuel (external_ref/
type/date) appelant `POST /claims` — aucun lien vers le pipeline d'extraction, le formulaire fusionné,
ou la validation, alors que ces trois pièces existaient déjà côté backend (sprints #6/#7). Deux gaps
réels supplémentaires découverts en creusant avant de coder :
1. `GET /claims/{id}/validation` lisait un `ValidationDecision` persisté, mais rien ne le persistait
   automatiquement — `EvidenceGraphStep`/`CrossValidationStep` tournaient bien dans le pipeline de
   chaque document, mais leur résultat était jeté (seule l'extraction était mergée/persistée). Le
   panneau "Anomalies" aurait été vide pour tout claim créé via le nouveau flux.
2. Aucun endpoint de correction manuelle (`PATCH`) n'existait nulle part (claims, documents, ou
   formulaire fusionné).

Corrigé, vérifié par exécution réelle :

1. **Validation persistée automatiquement** : `DocumentService.ingest_document` appelle maintenant
   `ValidationService.run_validation()` (moteur existant réutilisé tel quel, non réinventé) avec
   l'`EvidenceGraphResult` déjà calculé par le pipeline pour ce document. Limite assumée et documentée
   dans le code : la validation reste par-document (pas de fusion multi-documents au niveau du graphe,
   contrairement à `FormMappingEngine` pour l'extraction) — la décision persistée reflète le dernier
   document ingéré, pas une vue consolidée du dossier.
2. **Corrections manuelles réelles** : migration ajoutant `field_overrides` (JSONB) sur `claim_file` ;
   nouveau `PATCH /claims/{id}/documents/opening-form` (`{field_path, value}`) ; `DocumentService
   .get_opening_form` applique les corrections après la fusion (statut→FOUND, confiance=1.0, source
   identifiée comme correction manuelle avec le nom de l'opérateur). Chemin de champ validé contre un
   `ClaimOpeningForm` vide avant écriture (rejette les chemins inconnus en 422) — limité aux champs
   simples, pas aux éléments de listes (`victimes.<index>.*`), documenté explicitement plutôt que caché.
   Les helpers de traversée de chemin de `FormMappingEngine` (`_get_by_path`/`_set_by_path`) ont été
   promus en méthodes publiques (`get_field`/`set_field`) pour être réutilisés ici sans dupliquer la
   logique.
3. **"New Claim" devient un assistant à 3 étapes** (`NewClaimWizard.tsx`) : (1) formulaire minimal
   existant, (2) upload multi-fichiers avec statut par fichier (en attente → envoi → traitement IA →
   terminé/erreur), traité en **série** — un choix délibéré : chaque upload coûte réellement ~60-70s
   (extraction LLM synchrone, sprint #7), le parallélisme n'aurait fait qu'empiler cette latence contre
   la même instance Ollama sans rien accélérer — et l'échec d'un fichier n'interrompt pas les autres ;
   (3) revue complète inline dans la modale (pas de redirection).
4. **`ClaimReviewPanel.tsx`** (composant partagé, utilisé à la fois dans la modale et sur `/claims/[id]`
   pour éviter la duplication) : badges de confiance codés par couleur (vert ≥85%, orange 50-85%, rouge
   <50%, sur `MappedField.confidence` réel) ; statut CONFLICT affiché avec la valeur retenue et les
   alternatives écartées (document, extracteur, confiance) ; NOT_FOUND affiche la vraie raison
   (`MappedField.reason`) ; édition inline (crayon → input → `PATCH` → rafraîchissement) sur les champs
   simples ; panneau "Anomalies détectées" permanent, alimenté par `GET /validation/{id}/validation`,
   trié par sévérité réelle (BLOCKER > CRITICAL > ERROR > WARNING > INFO).
5. **Vérifié par exécution réelle avant tout code frontend** : appel direct de `DocumentService
   .ingest_document()` puis `ValidationService.get_validation_report()` en Python — confirmation que la
   décision de validation passe de "No validation performed yet." à une vraie décision
   (`STP_APPROVED`, confiance réelle) après un seul document. `DocumentService.correct_field()` testé
   directement : correction appliquée, chemin invalide rejeté avec `BusinessValidationError`.
6. **4 nouveaux tests HTTP réels** (`tests/api/test_document_ingestion.py`) : validation persistée après
   upload, correction persistée à travers un fetch séparé (pas juste dans la réponse du PATCH),
   correction qui écrase un champ déjà FOUND par extraction automatique, rejet 422 sur chemin inconnu,
   rejet 404 sur claim inconnu. **1020/1020 tests passent** (1015 précédents + 5 nouveaux, suite
   complète), aucune régression.
7. **`tsc --noEmit` et `eslint` propres** sur tous les fichiers modifiés/ajoutés côté frontend — les
   seules erreurs restantes (`react-hooks/set-state-in-effect`, `any` dans `api-client.ts`) sont un
   pattern déjà présent partout ailleurs dans le dépôt avant ce sprint, pas une régression introduite ici.

**Incident d'infrastructure pendant ce sprint** : le disque hôte est tombé à ~3.4 Go disponibles en
cours de vérification (`ENOSPC` sur les appels shell), et Docker Desktop s'est de nouveau arrêté à ce
moment — sans lien avec le code de ce sprint. Une vérification HTTP manuelle finale du flux complet
(création → upload → validation → correction, via `curl`, à la manière du sprint #6/#7) n'a **pas** pu
être menée à son terme à cause de cet incident. Cette étape a été jugée redondante avec les tests
`pytest` réels déjà exécutés (qui frappent exactement les mêmes endpoints HTTP avec le même client de
test) plutôt que contournée silencieusement — signalé ici en toute transparence. Aucune tentative de
libérer de l'espace disque en supprimant des volumes Docker (données Postgres/Neo4j) n'a été faite sans
l'accord de l'utilisateur.

**Ce qui reste explicitement hors périmètre** :
- Les corrections manuelles ne couvrent pas les éléments de liste (`victimes.<index>.*`).
- Aucune UI de suppression/téléchargement de document, ni de retagging du rôle après upload.
- La latence ~60-70s par document reste un vrai problème d'expérience utilisateur pour un dossier à
  plusieurs documents (upload séquentiel dans l'assistant) — aucune file d'attente asynchrone n'a été
  mise en place (signalé au sprint #7, toujours vrai).
- La validation reste par-document, pas fusionnée au niveau du dossier comme l'est le formulaire
  d'ouverture — signalé au point 1 ci-dessus.
