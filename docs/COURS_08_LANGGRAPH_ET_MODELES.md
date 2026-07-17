# Cours 8 — LangGraph et routage multi-modèles : recherche, décisions, contraintes réelles

## Pourquoi ce chapitre existe

Le document de présentation initial du projet listait explicitement deux choses que le Cours 1
avait délibérément écartées sans les valider avec l'équipe : *"ces agents collaborent via
LangGraph"*, et *"le routage [de modèle] est dynamique selon la tâche"*. Ce chapitre revient sur
ces deux points : ce que la recherche a montré, ce qui a été implémenté, et — partie la plus
instructive — ce qu'une contrainte matérielle réelle rencontrée en cours de route a changé au
plan initial.

## 1. Recherche — quel modèle pour quelle tâche

Objectif explicite : pour chaque agent qui appelle un LLM (Fraud, Legal, Decision), trouver **le
plus petit modèle qui fait bien le travail** — pas le plus gros disponible par défaut.

Recherche menée (web, pas seulement la connaissance d'entraînement, le sujet évolue vite) :

- **Qwen 2.5 1.5B** : 95,7 % de taux de parsing JSON valide, très rapide — excellent pour la
  fiabilité structurelle mais probablement trop limité pour un raisonnement nuancé (fraude,
  cohérence légale).
- **Phi-4** : meilleur en raisonnement pur (MATH 80%+, dépasse Llama 2 70B sur certains
  benchmarks) — mais son point d'équilibre taille/qualité est à 14B ; sa variante *mini* (3,8B)
  est plus comparable à Llama 3.2 3B qu'à un vrai concurrent de Phi-4.
- **DeepSeek-R1 (distillé)** : disponible en 1,5B/7B/8B/14B, licence MIT, spécifiquement fort en
  raisonnement logique/mathématique — un candidat naturel pour `legal_agent` (raisonnement sur des
  règles).
- **Qwen3** : nouvelle génération, "un modèle dense 8B atteint la qualité d'un Qwen2.5-14B" selon
  les benchmarks trouvés — un gain d'efficacité par paramètre significatif par rapport à la
  génération précédente. Qwen3 propose aussi un "mode réflexion" optionnel pour les tâches plus
  dures, activable sans changer de modèle.

**Conclusion de la recherche** : `qwen3:4b`/`qwen3:8b` pour la qualité générale au meilleur ratio
taille/performance, `deepseek-r1:7b` comme spécialiste raisonnement pour `legal_agent`. Aucun de
ces trois modèles n'était installé localement (seul `qwen2.5-coder:14b`/9 Go et
`deepseek-r1:14b`/9 Go l'étaient).

## 2. Ce qui s'est réellement passé au moment de télécharger

Trois `ollama pull` lancés : `qwen3:4b` (2,5 Go), `deepseek-r1:7b` (4,7 Go), `qwen3:8b` (5,2 Go).

- `qwen3:4b` a réussi.
- **`deepseek-r1:7b` et `qwen3:8b` ont échoué** : `Error: write ... no space left on device`.
  `df -h /` a confirmé : 360 Mo disponibles sur un disque de 228 Go (98 % plein, `~/.ollama/models`
  pesait déjà 38 Go à lui seul).

C'est exactement le genre de contrainte que la demande initiale ("le moindre de milliards de
paramètres pour la meilleure solution") anticipait, mais qui s'est confirmée en pratique plutôt
qu'en théorie : ce n'était pas un choix esthétique de préférer un petit modèle, c'était devenu la
**seule option qui tienne sur la machine**.

### Décision prise sur le moment

1. Nettoyage des blobs de téléchargement partiels (`~/.ollama/models/blobs/*-partial*`) — artefacts
   des deux tentatives échouées, sans rapport avec les données de l'utilisateur, ~5,7 Go récupérés.
2. **Abandon de `deepseek-r1:7b` et `qwen3:8b`** — retenter avec si peu de marge aurait risqué un
   nouvel échec, voire de saturer le disque au point de gêner Postgres/Neo4j qui tournent sur la
   même machine.
3. **`qwen3:4b` retenu comme modèle unique pour les 3 agents** (`Fraud`, `Legal`, `Decision`),
   plutôt que trois modèles différenciés par tâche comme la recherche initiale le suggérait.

Un seul modèle plutôt que trois n'est pas une régression au vu de l'objectif réel de la demande —
c'est littéralement la lecture la plus stricte de "le moins de ressources matérielles possible" :
un seul modèle chargé en mémoire Ollama à la fois pour l'ensemble des 3 agents, 2,5 Go au lieu de
9 Go (l'ancien défaut `qwen2.5-coder:14b`), une génération plus récente et mieux optimisée par
paramètre d'après la recherche.

## 3. Le routage reste configurable, même à modèle égal aujourd'hui

Plutôt que de coder en dur un seul modèle partagé, chaque agent lit sa **propre** clé de
configuration (`app/config/settings.py`) :

```python
OLLAMA_FRAUD_MODEL: str = os.getenv("OLLAMA_FRAUD_MODEL", "qwen3:4b")
OLLAMA_LEGAL_MODEL: str = os.getenv("OLLAMA_LEGAL_MODEL", "qwen3:4b")
OLLAMA_DECISION_MODEL: str = os.getenv("OLLAMA_DECISION_MODEL", "qwen3:4b")
```

Câblé dans chaque agent (`fraud_agent.py`, `legal_agent.py`, `decision_agent.py`) à la place de
l'ancien `OLLAMA_DEFAULT_MODEL` partagé. Conséquence pratique : le jour où plus d'espace disque est
disponible, basculer `legal_agent` vers un modèle de raisonnement plus poussé (ex.
`deepseek-r1:7b`) est un simple changement de variable d'environnement — **aucun code à toucher**.
C'est la réalisation concrète du "routage dynamique selon la tâche" du document initial : pas
encore trois modèles différents en pratique, mais l'infrastructure qui le permet sans friction.

`OllamaProvider` (`app/llm/providers/ollama_provider.py`) ne fait de remapping que pour
`"qwen2.5"` exact et toute chaîne contenant `"llama"` — un tag déjà exact comme `"qwen3:4b"`
traverse tel quel jusqu'à l'appel `/api/chat` d'Ollama, aucune modification nécessaire de ce côté.

## 4. LangGraph — la migration

### Ce qui existait avant

`app/agents/planner.py` (`Planner.create_plan()`) construisait un `ExecutionGraph` statique (liste
de nœuds + dépendances). `app/agents/scheduler.py` (`Scheduler.execute_graph()`) l'exécutait :
une boucle `while pending or running_tasks` maison, calculant à chaque itération quels agents
étaient prêts (toutes leurs dépendances dans `results`), les lançait avec `asyncio.create_task`,
attendait `asyncio.wait(..., FIRST_COMPLETED)`. Fonctionnel (72 tests le prouvaient), mais c'est
exactement ce que LangGraph fait nativement, en mieux testé et documenté.

### Ce qui existe maintenant : `app/agents/graph.py`

`Planner` et `Scheduler` ont été **supprimés**, pas laissés en parallèle inutilisés (`grep` a
confirmé qu'aucun autre module ne les important avant suppression — cohérent avec la convention du
projet de ne jamais garder du code mort).

```python
from langgraph.graph import StateGraph, START, END

class GraphState(TypedDict):
    results: Annotated[dict[str, AgentResult | None], _merge_results]

def build_graph(agents, context, memory) -> CompiledStateGraph:
    builder = StateGraph(GraphState)
    ...  # add_node par agent présent, add_edge selon GRAPH_EDGES
    return builder.compile()
```

Décision de conception centrale : **`context` (`AgentContext`) et `memory` (`SharedMemory`) ne
transitent pas par l'état géré par LangGraph.** Ce sont des objets Python mutables, déjà modifiés
en place par chaque `BaseAgent` (`context.ocr_results = ...`, `memory.add_observation(...)`) —
exactement comme le faisait l'ancien `Scheduler`. Les faire transiter par l'état LangGraph aurait
nécessité un reducer par champ pour gérer les écritures concurrentes (`ocr_supervisor` et
`extraction_agent` tournent en parallèle, sans dépendance entre eux) — inutile puisque c'est déjà
le même objet partagé par fermeture (`_make_node(agent, context, memory)`). Seul `results` — un
`AgentResult` par agent — a besoin d'un état géré par LangGraph, avec un reducer `_merge_results`
qui fusionne les dictionnaires plutôt que d'écraser (nécessaire dès que deux nœuds sans dépendance
mutuelle écrivent dans le même superstep).

Le graphe de dépendances (`GRAPH_EDGES`) reste la même structure que documentée au Cours 4 — seul
le moteur d'exécution a changé, pas la forme du DAG :

```python
GRAPH_EDGES = [
    ("ocr_supervisor", []),
    ("extraction_agent", []),
    ("fraud_agent", ["ocr_supervisor"]),
    ("legal_agent", ["extraction_agent"]),
    ("decision_agent", ["fraud_agent", "legal_agent"]),
    ("supervisor_agent", ["decision_agent"]),
]
```

`AgentManager.process_claim()` (`app/agents/manager.py`) est passé de
`Planner.create_plan() + Scheduler.execute_graph()` à `build_graph(...).ainvoke(...)` — le contrat
externe (forme du dict retourné : `status`, `context`, `history`, `agent_results`) est **resté
identique**, donc aucun appelant (`app/api/v1/endpoints/agents.py`, `app/agents/claim_bridge.py`)
n'a eu besoin d'être modifié.

### Tests

`tests/agents/test_planner_six_agent_dag.py` (ancien) supprimé, remplacé par
`tests/agents/test_langgraph_six_agent_dag.py` : mêmes propriétés vérifiées (les 6 agents
découverts, la forme exacte du DAG, dégradation propre si un agent manque) plus deux tests que
l'ancienne suite ne pouvait pas faire aussi simplement : `test_build_graph_compiles_with_all_six_agents`
(le graphe compile réellement, pas seulement "la structure de données a la bonne forme") et
`test_full_graph_runs_end_to_end_without_a_document` (un run réel via `graph.ainvoke()`,
reproduisant le scénario de `tests/agents/test_multi_agent_platform.py::test_agent_manager_no_document_fails_honestly`
mais au niveau du graphe directement). Les 72 tests de `tests/agents/` passent, y compris
`test_agent_manager_full_flow` (`requires_ollama`, un run complet avec une vraie image et un vrai
appel `fraud_agent` — désormais vers `qwen3:4b`).

## 5. Limite de vérification assumée

La suite complète du dépôt (1053 tests) n'a pas pu être exécutée jusqu'au bout dans cette session :
deux tentatives se sont bloquées sur une machine dont le swap était quasi saturé
(`vm.swapusage` : 8,65 Go / 9,2 Go utilisés), un état de contention généralisé plutôt qu'un bug —
confirmé par `pytest --collect-only` qui valide sans erreur les 1053 tests (aucun import cassé par
la suppression de `planner.py`/`scheduler.py`) et par `tests/agents/` qui passe intégralement en
isolation. Documenté ici plutôt que laissé implicite : la suite complète reste à revalider quand la
machine aura plus de marge mémoire disponible.
