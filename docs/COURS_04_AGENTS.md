# Cours 4 — Le pipeline des 6 agents

## Le framework qu'on réutilise

`app/agents/` fournit déjà tout ce qu'il faut pour faire collaborer plusieurs agents, sans
LangGraph :

- **`BaseAgent`** (`app/agents/base.py`) — contrat que chaque agent implémente : `plan()`
  (dois-je m'exécuter ?), `execute()` (fait le travail, renvoie un `AgentResult`), `validate()`
  (mon propre résultat est-il crédible ?), `rollback()` (annuler si invalide — optionnel).
- **`AgentRegistry`** (`app/agents/registry.py`) — scanne `app/agents/modules/` au démarrage,
  instancie toute classe qui hérite de `BaseAgent`. Ajouter un agent = ajouter un fichier, rien à
  enregistrer ailleurs.
- **`Planner`** (`app/agents/planner.py`) — construit un `ExecutionGraph` (liste de nœuds, chacun
  avec ses dépendances par `agent_id`).
- **`Scheduler`** (`app/agents/scheduler.py`) — exécute le graphe : à chaque itération, lance tous
  les agents dont les dépendances sont déjà résolues, attend qu'au moins une tâche se termine,
  recommence. C'est un ordonnanceur DAG asynchrone classique, en ~50 lignes.
- **`SharedMemory`** — bus d'observations : chaque agent y dépose ce qu'il a trouvé
  (`memory.add_observation(agent_id, data, confidence)`), les agents suivants peuvent le lire.
- **`AgentContext`** (`app/agents/context.py`) — l'état partagé qui traverse tout le graphe
  (`ocr_results`, `entities`, `validation_report`, `decision`, `metadata`).

## Les 6 agents et leur rôle

### 1. `ocr_supervisor` (déjà existant, `app/agents/modules/ocr_supervisor.py`)

Rôle inchangé : `plan()` retourne `True` seulement si `context.ocr_results` est vide. Dans
l'orchestration décrite au Cours 5, le texte OCR est déjà connu (on ne relance pas l'OCR — le
pipeline linéaire l'a déjà fait) : `context.ocr_results` est pré-rempli avant de lancer le graphe,
donc cet agent **saute son exécution** — c'est le comportement voulu, pas un bug : il "supervise"
au sens où il vérifie qu'un texte OCR existe déjà et ne refait rien s'il est satisfait.

### 2. `extraction_agent` (nouveau, `app/agents/modules/extraction_agent.py`)

**Pas d'appel LLM.** Son rôle est un aplatissement déterministe : il prend le `ClaimOpeningForm`
déjà fusionné (produit par `FormMappingEngine`, transmis via
`context.metadata["raw"]["opening_form"]`) et le transforme en un dictionnaire plat
`context.entities = {"numero_police": {"value": ..., "status": ..., "confidence": ...}, "conducteur.nom": {...}, "victimes.0.nom": {...}, ...}`.

Pourquoi un agent dédié plutôt que de laisser chaque agent suivant parser le schéma Pydantic
lui-même : ça isole la connaissance de la structure de `ClaimOpeningForm` (imbrications,
`ConducteurForm`, `PartieAdverseForm`, liste `victimes`) à un seul endroit. Si le formulaire évolue,
un seul fichier à toucher.

Il calcule aussi une métrique utilisée plus loin par `decision_agent` :
`context.metadata["extraction_completeness"]` = proportion de champs `FOUND` parmi tous les champs
déclarés.

### 3. `fraud_agent` (déjà existant, `app/agents/modules/fraud_agent.py`)

Rôle inchangé : appel LLM (`get_settings().OLLAMA_DEFAULT_MODEL`, `temperature=0.0`) sur le texte
de `context.ocr_results["text"]`, retourne un `fraud_score` 0-1. Écrit
`context.metadata["fraud_score"]`.

### 4. `legal_agent` (nouveau, `app/agents/modules/legal_agent.py`)

Deux couches, volontairement séparées :

1. **Règles déterministes** (`_run_deterministic_checks`), toujours exécutées, jamais dépendantes
   du LLM :
   - la police d'assurance était-elle valide à la date du sinistre
     (`date_effet_contrat ≤ date_survenance ≤ date_echeance_contrat`) ?
   - le permis de conduire a-t-il été obtenu avant l'accident
     (`conducteur.date_permis ≤ date_survenance`) ?
   - une procédure judiciaire est-elle mentionnée sans juridiction précisée ?
2. **Analyse LLM** best-effort sur un résumé texte des champs juridiques libres (circonstances,
   procédure judiciaire, avocat adverse, exclusions de garantie des victimes) — capte ce qu'aucune
   règle fixe n'anticipe. **Si l'appel LLM échoue, l'agent renvoie quand même les résultats
   déterministes** au lieu d'échouer entièrement — même politique de dégradation que
   `LLMFieldExtractor` (Cours de `docs/COURS_CLAIMOS.md` §4.4) : ne jamais perdre un résultat fiable
   à cause d'un composant probabiliste indisponible.

Écrit `context.validation_report = {"compliant": bool, "issues": [...], "llm_enriched": bool}`.

**Pourquoi une vérification de dates en Python plutôt qu'en LLM** : une comparaison de dates a une
réponse binaire et exacte — demander à un LLM d'évaluer `date_effet_contrat ≤ date_survenance` est
plus lent, plus cher, et introduit un risque d'erreur là où il n'y en avait aucun. Le principe
directeur : **utiliser le LLM seulement là où le raisonnement est vraiment nécessaire**
(texte libre, contexte), jamais pour remplacer un calcul déterministe.

### 5. `decision_agent` (nouveau, `app/agents/modules/decision_agent.py`)

Synthétise `extraction_completeness` (agent 2), `fraud_score` (agent 3), `validation_report`
(agent 4) en une recommandation. Utilise le même vocabulaire que le moteur de décision
déterministe existant (`app.engines.decision.models.DecisionType`) pour que les deux systèmes
parlent le même langage, **sans réutiliser ce moteur directement** — il a besoin d'un
`EvidenceGraphResult` + `ValidationReport` complets, produits en mémoire pendant l'exécution du
pipeline linéaire sur *un* document, non reconstructibles proprement pour un claim entier après
coup (voir Cours 5, §"Ce qu'on n'a pas essayé de reconstruire"). Le moteur déterministe reste donc
la source de vérité pour la décision *par document*, pendant que `decision_agent` raisonne au
niveau du claim entier avec les signaux dont on dispose réellement.

**Propriété de sécurité, non négociable** : une couche de règles déterministes tourne d'abord et ne
peut qu'escalader la vigilance, jamais approuver automatiquement :

```python
if fraud_score > 0.7:            return FRAUD_REVIEW
if legal_issues:                 return HUMAN_REVIEW
if completeness < 0.5:           return REQUEST_MORE_DOCUMENTS
# sinon seulement : appel LLM pour une recommandation nuancée
```

Le LLM n'est consulté que si aucune de ces règles ne s'est déclenchée, et **si l'appel LLM échoue,
la décision retombe sur `HUMAN_REVIEW` avec confiance 0.0** — jamais sur une approbation
automatique par défaut. Un dossier n'est jamais silencieusement approuvé parce qu'un composant a
échoué.

### 6. `supervisor_agent` (nouveau, `app/agents/modules/supervisor_agent.py`)

**Pas d'appel LLM non plus** — un arbitre final doit être déterministe et auditable, pas lui-même
une opinion probabiliste. Deux responsabilités :

1. Agrège les résultats de tous les agents (`SharedMemory.get_observations_by_agent()`) en un
   résumé unique.
2. Filet de sécurité final : si `decision_agent` a rendu un verdict avec une confiance faible
   (`< 0.4`) ou si un agent en amont n'a produit aucun résultat, le superviseur **écrase** la
   décision vers `HUMAN_REVIEW`, quelle que soit la recommandation initiale. Une décision
   automatique peu fiable ne doit jamais atteindre l'utilisateur final comme si elle était fiable.

## Le graphe de dépendances (`app/agents/planner.py`)

```
        ocr_supervisor        extraction_agent
              |                       |
              v                       v
         fraud_agent            legal_agent
              \\                     /
               v                   v
                decision_agent
                      |
                      v
               supervisor_agent
```

`ocr_supervisor` et `extraction_agent` n'ont aucune dépendance l'un envers l'autre — ils lisent
deux parties différentes des données brutes du claim (texte OCR vs formulaire déjà fusionné) et
peuvent s'exécuter en parallèle (`Scheduler.execute_graph()` les lance simultanément dès que le
graphe démarre). Chaque nœud est ajouté sous garde `if agent_id in available_agents` : si un
déploiement donné n'enregistre pas tous les modules, le plan dégrade en sautant le nœud concerné,
jamais en cassant tout le graphe.

Vérification que le graphe se construit correctement (fait pendant ce travail, reproductible) :

```python
from app.agents.registry import AgentRegistry
from app.agents.planner import Planner
from app.agents.context import AgentContext
import asyncio

r = AgentRegistry(); r.discover()
graph = asyncio.run(Planner(r).create_plan(AgentContext(claim_id="test")))
for n in graph.nodes:
    print(n.agent_id, "<-", n.dependencies)
# ocr_supervisor <- []
# extraction_agent <- []
# fraud_agent <- ['ocr_supervisor']
# legal_agent <- ['extraction_agent']
# decision_agent <- ['fraud_agent', 'legal_agent']
# supervisor_agent <- ['decision_agent']
```

## Ce que ce chapitre ne couvre pas encore

Ces 6 agents existent et forment un graphe correct, mais rien n'appelle encore
`AgentManager.process_claim()` avec de vraies données de claim — `AgentContext` est aujourd'hui
construit à la main dans les tests. Le branchement sur un vrai claim (comment
`context.metadata["raw"]["opening_form"]` et `context.ocr_results` sont peuplés à partir de
données persistées, et via quel endpoint) est le sujet du Cours 5.
