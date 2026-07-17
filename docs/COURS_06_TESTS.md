# Cours 6 — Tester ce qui a été ajouté

## Principe directeur : tester ce qui peut casser silencieusement

Chaque pièce ajoutée (Cours 2 à 5) a un test dédié, choisi pour couvrir le comportement qui
pourrait régresser sans qu'on s'en aperçoive — pas une couverture mécanique ligne par ligne.

## Où sont les tests

```
tests/engines/form_mapping/test_role_inference.py   → infer_document_role() (Cours 2)
tests/services/test_document_service_manual_fields.py → validation des chemins (Cours 3)
tests/agents/test_extraction_agent.py                → ExtractionAgent (Cours 4)
tests/agents/test_legal_agent.py                      → LegalAgent (Cours 4)
tests/agents/test_decision_agent.py                   → DecisionAgent (Cours 4)
tests/agents/test_supervisor_agent.py                 → SupervisorAgent (Cours 4)
tests/agents/test_planner_six_agent_dag.py             → le graphe à 6 agents (Cours 4)
tests/agents/test_claim_bridge.py                      → build_agent_raw_data (Cours 5)
```

Tous unitaires, sans base de données — voir "Ce qui n'est pas testé" plus bas pour pourquoi, et ce
que ça implique.

## Le pattern répété : `LLMManager` mocké, jamais un vrai appel Ollama dans les tests unitaires

Chaque agent qui appelle un LLM (`LegalAgent`, `DecisionAgent`) est testé avec un
`LLMManager` **mocké** (`unittest.mock.MagicMock` + `AsyncMock` sur `.generate()`), exactement le
pattern déjà utilisé par `tests/engines/extraction/test_llm_field_extractor.py` :

```python
mock_manager = MagicMock()
mock_manager.generate = AsyncMock(return_value=_mock_llm_response({"issues": [], "confidence": 0.9}))
agent = LegalAgent(llm_manager=mock_manager)
```

Pourquoi mocker plutôt qu'utiliser le vrai Ollama local (disponible dans cet environnement,
vérifié §"Vérification empirique" du Cours 1) : un test unitaire doit être rapide, déterministe, et
ne pas dépendre d'un service externe pour passer en CI (qui, rappel du `CLAUDE.md` racine, n'a pas
Ollama configuré). Le comportement "vrai LLM, vraie réponse" appartient aux tests marqués
`requires_ollama` — aucun n'a été ajouté ici parce qu'aucune des logiques nouvelles ne dépend de la
*qualité* d'une vraie réponse LLM pour être correcte (le test porte sur le routage/agrégation
autour de l'appel, pas sur le contenu généré).

## Ce que chaque test vérifie, et pourquoi c'est le bon test

### `test_role_inference.py`
Vérifie explicitement que les familles ambiguës (`Identity Card`, `Insurance Attestation`,
`Invoice`) ne sont **jamais** inférées — c'est la propriété la plus importante de
`infer_document_role()` (Cours 2, §"Pourquoi une seule entrée"). Un futur ajout imprudent à
`AUTO_INFERRED_ROLES` qui casserait cette garantie ferait échouer ce test immédiatement.

### `test_document_service_manual_fields.py`
Vérifie que `victimes.0.nom` (chemin de liste) est bien rejeté — documente une limite connue
(Cours 3) plutôt que de la laisser échouer silencieusement plus tard sans explication.

### `test_extraction_agent.py`
Vérifie qu'un champ jamais rempli (`date_survenance` dans le formulaire de test) reste présent
dans `context.entities` avec `status: NOT_FOUND` — **pas absent du dictionnaire**. C'est la
propriété qui a permis, au départ, de diagnostiquer le bug du Cours 1 : un champ manquant doit
toujours être visible comme "cherché mais pas trouvé", jamais silencieusement omis.

### `test_legal_agent.py`
Le test le plus important du lot : `test_llm_failure_degrades_to_deterministic_findings_only`
vérifie que quand l'appel LLM lève une exception, **les vérifications de dates déterministes
survivent quand même** dans le résultat final. Sans ce test, un futur refactoring pourrait
facilement faire disparaître les deux couches ensemble en cas d'échec LLM (`try/except` mal placé
englobant tout), ce qui masquerait une vraie non-conformité légale (police expirée, permis
invalide) juste parce qu'Ollama était indisponible ce jour-là.

### `test_decision_agent.py`
`test_high_fraud_score_forces_fraud_review_without_calling_llm` et les deux tests similaires
vérifient `mock_manager.generate.assert_not_called()` — **pas seulement** que la décision est
correcte, mais que le LLM n'a **même pas été appelé** quand une règle déterministe suffit. C'est
le test qui protège la propriété de sécurité du Cours 4 : les règles qui escaladent la vigilance
doivent primer sur toute nuance qu'un LLM pourrait introduire.

`test_llm_failure_never_silently_auto_approves` est le test qui compte le plus dans tout ce
travail : il vérifie qu'un échec technique (Ollama down) ne peut **jamais** se traduire par une
approbation automatique silencieuse — le pire résultat possible pour un système de décision
d'assurance serait qu'une panne LLM approuve un sinistre par défaut.

### `test_supervisor_agent.py`
`test_failed_upstream_agent_forces_human_review_override` vérifie que même une décision à haute
confiance (0.95) est écrasée si un agent en amont n'a produit aucune observation — le filet de
sécurité du Cours 4 ne doit pas dépendre uniquement du score de confiance de `decision_agent`, qui
pourrait être artificiellement élevé sur des données partielles.

### `test_planner_six_agent_dag.py`
Fige le graphe de dépendances exact (Cours 4, schéma ASCII) en assertions automatisées — un futur
changement du `Planner` qui casserait l'ordre (ex. `decision_agent` déclenché avant que
`legal_agent` ait fini) serait détecté immédiatement plutôt que découvert en observant un
comportement bizarre en production.

### `test_claim_bridge.py`
Vérifie que **seuls** les champs `FOUND` apparaissent dans le résumé texte envoyé aux agents
(`test_build_agent_raw_data_summarizes_found_fields_only` vérifie explicitement que `juridiction`,
laissé `NOT_FOUND`, n'apparaît pas) — protège contre une régression qui enverrait du bruit
(`None`, des chaînes vides) aux agents d'analyse LLM.

## Ce qui n'est pas testé, et pourquoi c'est documenté plutôt que caché

**`DocumentService.ingest_document()` (inférence de rôle en conditions réelles) et
`DocumentService.submit_manual_fields()` (persistance en base) n'ont pas de test d'intégration
avec une vraie base de données.**

Raison : `backend/tests/conftest.py` ne fournit aucune fixture de base de données (confirmé dans
`CLAUDE.md` racine — "no dedicated test-DB fixture setup at the root ... individual test modules
manage their own fixtures"), et aucun test existant dans le repo ne construit de `ClaimFile`
avant ce travail — il n'y avait pas de pattern établi à suivre. En créer un uniquement pour ces
deux méthodes aurait été disproportionné par rapport au risque réel : la logique métier qui compte
(résolution du chemin de champ, priorité de l'override manuel, fusion) est déjà couverte
indirectement par `test_form_mapping.py` (fusion) et les tests unitaires ci-dessus (validation des
chemins). Ce que les tests actuels **ne couvrent pas** : que `effective_role` soit bien la valeur
réellement écrite en base par SQLAlchemy, et que `submit_manual_fields` gère bien une vraie
transaction concurrente.

**Ce gap est un candidat naturel pour une prochaine session** : construire une fixture
`tests/conftest.py` (ou un module partagé `tests/db_fixtures.py`) avec une base de test dédiée
(Postgres de test, pas SQLite — les modèles utilisent des types spécifiques à Postgres comme
`UUID`, `JSONB`) serait un investissement qui profiterait à bien plus que ce seul travail : aucun
test de `ClaimFile`/`ClaimDocument` n'existe nulle part dans le repo aujourd'hui.
