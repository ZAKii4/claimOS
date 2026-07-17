# Cours 1 — Décisions d'architecture : deux parcours, six agents, une cause racine

Ce cours explique les choix structurants pris pour répondre à une demande en trois parties :
1. Permettre à un opérateur d'ouvrir un sinistre **soit** en saisissant les informations à la
   main, **soit** en uploadant les documents (le pipeline automatique).
2. Corriger la cause racine documentée dans `docs/COURS_CLAIMOS.md` §4.6 : les champs "niveau
   sinistre" n'apparaissent presque jamais parce que le document constat/PV n'est presque jamais
   tagué `ACCIDENT_REPORT`.
3. Faire vivre ce travail dans "le pipeline des 6 agents avec leurs rôles" : OCR Agent, Extraction
   Agent, Fraud Agent, Legal Agent, Decision Agent, Supervisor Agent.

Chaque décision ci-dessous répond à une question que n'importe quel repo hérité pose : *qu'est-ce
qui existe déjà, qu'est-ce qui est juste une promesse marketing, et où est-ce que je branche du
nouveau code sans casser ce qui marche ?*

---

## 1. Deux systèmes candidats pour "traiter un sinistre"

En explorant `backend/app/`, on trouve **deux chemins distincts** qui prétendent tous les deux
traiter un document de sinistre :

### A. Le pipeline linéaire (`app/pipeline/`)

17 étapes séquentielles (Upload → ... → Archiving), chacune déléguant à un moteur réel dans
`app/engines/`. C'est le chemin **réellement branché** sur l'API
(`POST /claims/{claim_id}/documents` → `DocumentService.ingest_document()` →
`get_document_pipeline().execute()`). Il gère nativement le multi-page et le multi-document (un
seul PDF peut contenir un PV + une attestation + une carte grise, séparés automatiquement par
`app/pipeline/segmentation.py`). Il est couvert par des tests d'intégration
(`tests/test_pipeline.py`).

### B. Le système multi-agents (`app/agents/`)

`AgentManager.process_claim()` : un `Planner` construit un graphe d'exécution
(`ExecutionGraph`), un `Scheduler` l'exécute de façon asynchrone en respectant les dépendances,
chaque agent (`BaseAgent`) a un cycle `plan() → execute() → validate() → rollback()`. Avant ce
travail, seuls 2 agents existaient réellement : `OCRSupervisorAgent` et `FraudAgent`
(`app/agents/modules/`). Le `Planner` était câblé pour un DAG à 4 nœuds hypothétiques
(`ocr_supervisor`, `classification_supervisor`, `fraud_agent`, `validation_supervisor`) — dont 2
n'existaient même pas.

**Limite structurelle du système B** : `AgentContext` (`app/agents/context.py`) ne connaît qu'un
seul chemin d'image (`metadata.raw.image_path`) — il n'a jamais été conçu pour le cas réel
(plusieurs documents, plusieurs pages par document, segmentation). Le refaire pour égaler le
pipeline A serait un chantier à part entière, risqué, et sans bénéfice : le pipeline A fait déjà ce
travail, testé, en production interne.

### Décision

**On ne remplace pas A par B.** Le pipeline linéaire reste l'unique responsable de l'extraction
brute (OCR, classification, extraction de champs). Le système multi-agents devient la **couche de
collaboration qui s'exécute après**, sur les données déjà extraites et persistées d'un claim : elle
croise les sources, évalue la fraude, vérifie la conformité légale, produit une recommandation de
décision, et arbitre. C'est exactement la distinction que fait le document de présentation entre
"Ingestion/OCR/Extraction" (des moteurs déterministes) et "Multi-Agent AI" / "Decision
Intelligence" (du raisonnement collaboratif) — ce sont deux couches différentes, pas deux
implémentations concurrentes de la même chose.

---

## 2. Pourquoi pas LangGraph *(décision révisée — voir Cours 8)*

> **Mise à jour** : cette section documente le raisonnement initial, qui n'avait jamais été validé
> avec l'équipe avant d'écrire le code. Une fois la question posée explicitement, LangGraph a été
> intégré pour de vrai — `Planner`/`Scheduler` ont été supprimés et remplacés par
> `app/agents/graph.py`. Détail complet : [`COURS_08_LANGGRAPH_ET_MODELES.md`](COURS_08_LANGGRAPH_ET_MODELES.md).
> Section conservée ci-dessous pour l'historique du raisonnement, pas comme état actuel du code.

Le document de présentation mentionne LangGraph comme moteur d'orchestration des agents.
Vérification : `backend/pyproject.toml` ne liste **aucune dépendance LangGraph** — le repo a son
propre orchestrateur maison (`Planner` + `Scheduler` + `EventBus`), qui fait déjà ce dont on a
besoin : un graphe de tâches avec dépendances, exécuté en asynchrone, avec health-check et
rollback par nœud (`app/agents/scheduler.py`).

**Décision : ne pas ajouter LangGraph.** Ajouter une dépendance d'orchestration lourde pour
remplacer un scheduler maison qui fonctionne serait un risque architectural (nouvelle surface de
bugs, nouvelle courbe d'apprentissage, migration de tout l'existant) sans gain fonctionnel mesurable
à ce stade. Si LangGraph devient nécessaire plus tard (graphes conditionnels complexes,
multi-tenant agent swarms), ce sera une décision séparée, documentée séparément.

---

## 3. Les "6 agents" — mapping entre le document de présentation et le code

| Nom dans le document | État avant ce travail | Décision |
|---|---|---|
| OCR Agent | `OCRSupervisorAgent` existe (`app/agents/modules/ocr_supervisor.py`) | Conservé tel quel — mais son rôle change : dans la nouvelle orchestration, il **ne refait pas l'OCR** (déjà fait par le pipeline A), il *consomme* le texte déjà extrait. Voir Cours 5. |
| Extraction Agent | N'existait pas | **Créé** (`app/agents/modules/extraction_agent.py`) — lit l'`ExtractionResult` déjà produit par le pipeline A et le projette dans `AgentContext.entities`, pour que les agents suivants (Legal, Decision) travaillent sur des données structurées plutôt que du texte brut. |
| Fraud Agent | `FraudAgent` existe (`app/agents/modules/fraud_agent.py`) | Conservé tel quel — appel LLM sur le texte OCR complet, `fraud_score` 0-1. |
| Legal Agent | N'existait pas | **Créé** (`app/agents/modules/legal_agent.py`) — vérifie la cohérence légale/réglementaire : dates de police valides, permis non expiré, juridiction renseignée, victimes/procédure judiciaire cohérentes. |
| Decision Agent | N'existait pas en tant qu'agent (logique dispersée dans `app/engines/decision/`) | **Créé** (`app/agents/modules/decision_agent.py`) — agrège les artefacts des agents précédents (extraction, fraude, légal) en une recommandation explicable avec score de confiance. |
| Supervisor Agent | N'existait pas | **Créé** (`app/agents/modules/supervisor_agent.py`) — dernier maillon du graphe, dépend de tous les autres ; arbitre les conflits, écrit un résumé final dans `SharedMemory`, et est celui qui décide si le dossier peut passer en revue humaine ou non. |

Détail complet de chaque agent : Cours 4 (`docs/COURS_04_AGENTS.md`).

---

## 4. La cause racine du "aucune information du sinistre" — rappel et plan de correction

Trouvé et vérifié empiriquement (`docs/COURS_CLAIMOS.md` §4.6) : `FormMappingEngine.FIELD_MAPPING`
ne route les champs "niveau sinistre" (circonstances, lieu, date, victimes, responsabilité...) que
sous `DocumentRole.ACCIDENT_REPORT` — et sur 43 claims en base de développement, aucun ne combinait
un document `ACCIDENT_REPORT` avec les documents véhicule/police. Le rôle est un paramètre optionnel
à l'upload (`document_role: DocumentRole | None = Form(None)`), jamais rempli en pratique pour le
constat.

### Décision : inférence automatique, limitée aux familles non ambiguës

Une famille de document classifiée (`DocumentClass.family`, ex. `"Police Report"`) peut être
utilisée pour déduire le rôle **seulement quand ce rôle est le même quel que soit le contexte**.
`"Police Report"` (le constat amiable / PV) est de ce cas : ce document est toujours le rapport
d'accident, jamais "le véhicule adverse" ou "la victime". En revanche `"Identity Card"` ou
`"Insurance Attestation"` sont ambigus — ils peuvent appartenir au souscripteur ou à la partie
adverse, et deviner faux serait pire que ne rien déduire (une fausse donnée silencieusement mal
classée). Détail d'implémentation : Cours 2 (`docs/COURS_02_ROLE_AUTOMATIQUE.md`).

Cette correction résout mécaniquement le symptôme observé : dès qu'un constat/PV est uploadé (avec
ou sans rôle fourni explicitement), il est maintenant automatiquement tagué `ACCIDENT_REPORT`, donc
les ~20 champs "niveau sinistre" de `ClaimOpeningForm` deviennent atteignables sans action manuelle
supplémentaire de l'opérateur.

---

## 5. Le second parcours : saisie manuelle

Le mécanisme de correction champ-par-champ existait déjà
(`PATCH /claims/{claim_id}/documents/opening-form`, `DocumentService.correct_field()`) — il permet
de corriger *un* champ à la fois, avec traçabilité (`field_overrides` en JSON sur `ClaimFile`,
`status=FOUND, confidence=1.0, extraction_method="manual_correction"`).

Ce mécanisme n'était pas pensé pour la saisie **initiale complète** d'un sinistre : un opérateur qui
n'a aucun document (accident rapporté par téléphone, dossier ouvert avant réception des pièces)
devrait pouvoir remplir le formulaire entier en un seul appel plutôt que d'enchaîner ~40 requêtes
`PATCH`.

### Décision

Un nouvel endpoint `POST /claims/{claim_id}/opening-form/manual` qui accepte un dictionnaire plat
`{chemin_de_champ: valeur}` et réutilise **exactement** le même mécanisme de persistance
(`field_overrides`) que `correct_field()`, en bulk. Aucune nouvelle table, aucun nouveau modèle de
données — la saisie manuelle et la correction ponctuelle sont, au fond, le même geste (« ce champ
vaut X, décidé par un humain, confiance 1.0 »), seulement déclenché différemment. Détail :
Cours 3 (`docs/COURS_03_SAISIE_MANUELLE.md`).

---

## 6. Ce que ce découpage garantit

- **Rien dans le pipeline linéaire n'est modifié dans sa logique d'extraction** — seul le calcul du
  rôle à la fin du traitement d'un segment change (une fonction pure ajoutée, appelée une fois).
- **Les tests existants restent valides** : `test_extraction.py`, `test_llm_field_extractor.py`,
  `test_form_mapping.py`, `test_pipeline.py` ne testent aucun comportement modifié directement (ils
  ne passent jamais explicitement `document_role=None` en s'attendant à un rôle `None` en sortie
  pour un `"Police Report"` — à vérifier au moment des tests, Cours 6).
- **Les deux parcours (manuel / upload) convergent vers le même formulaire final**
  (`ClaimOpeningForm`), avec la même notion de provenance et de confiance — un opérateur peut
  commencer en saisie manuelle puis compléter par upload, ou l'inverse, sans incohérence.
