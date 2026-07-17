# Cours 5 — Brancher les 6 agents sur un vrai claim

Le Cours 4 a construit un graphe de 6 agents qui fonctionne — mais uniquement quand on lui fournit
un `AgentContext` à la main, avec un `image_path` unique. Ce cours explique comment le brancher sur
de vraies données de claim, persistées, potentiellement multi-documents.

## Le problème de raccordement

`AgentManager.process_claim(claim_id, raw_data)` construit :
```python
context = AgentContext(claim_id=claim_id, metadata={"raw": raw_data})
```
`raw_data` est un simple dictionnaire. Les agents lisent dedans (`context.metadata["raw"]`). Deux
choses manquaient pour l'utiliser sur un vrai claim :

1. **D'où vient `raw_data` ?** Il faut le construire à partir de ce qui existe déjà pour un claim
   en base — le `ClaimOpeningForm` fusionné (`DocumentService.get_opening_form()`).
2. **Le texte OCR brut n'est persisté nulle part.** `ClaimDocument.extracted_data` ne stocke que le
   `ExtractionResult` structuré (champs déjà extraits), pas le texte OCR ligne par ligne. Or
   `FraudAgent` et la couche LLM de `LegalAgent` ont besoin d'un texte libre à analyser.

## Décision : un résumé texte construit depuis le formulaire fusionné, pas une reconstruction d'OCR

Deux options existaient :

- **(a)** Persister le texte OCR brut quelque part (nouvelle colonne sur `DocumentPage` ou
  `ClaimDocument`) pour pouvoir le relire tel quel plus tard.
- **(b)** Construire, à la volée, un résumé texte à partir des champs `FOUND` du formulaire déjà
  fusionné.

**Choix : (b).** Ajouter une colonne de stockage de texte brut est un changement de schéma
(migration Alembic, volume de stockage supplémentaire pour du texte potentiellement long) pour un
gain marginal : les champs `FOUND` du `ClaimOpeningForm` **sont** déjà l'information utile — c'est
littéralement le texte OCR *après* qu'on en a extrait le signal. Un résumé du type
`"lieu_survenance: Casablanca\ndate_survenance: 2026-07-10\ncirconstances_accident: ..."` donne à
un LLM d'analyse de fraude ou de conformité légale un signal au moins aussi bon qu'un mur de texte
OCR brut, sans changement de schéma. C'est documenté comme un choix explicite, pas une omission,
dans `app/agents/claim_bridge.py`.

### `app/agents/claim_bridge.py` — le pont

```python
def build_agent_raw_data(form: ClaimOpeningForm) -> dict:
    lines, confidences = _collect_found_lines(form)  # walk récursif de tous les MappedField FOUND
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    return {
        "opening_form": form.model_dump(mode="json"),
        "ocr_text": "\n".join(lines),
        "ocr_confidence": avg_confidence,
    }
```

Deux clés dans `raw_data`, consommées différemment :
- `opening_form` → lu par `extraction_agent` (Cours 4) pour peupler `context.entities`.
- `ocr_text` / `ocr_confidence` → lus par `ocr_supervisor` pour peupler `context.ocr_results`, ce
  qui débloque ensuite `fraud_agent`.

### Adaptation minime de `OCRSupervisorAgent`

Son rôle historique (rejouer l'OCR sur `image_path`) ne s'applique pas ici — le texte est déjà
connu, produit par le pipeline linéaire. Plutôt que de le contourner, on lui apprend un second mode
d'exécution, dans `app/agents/modules/ocr_supervisor.py` :

```python
if not image_path and raw.get("ocr_text"):
    context.ocr_results = {"text": raw["ocr_text"], "confidence": float(raw.get("ocr_confidence", 1.0))}
    ...
    return AgentResult(status="SUCCESS", ...)
```

Le comportement historique (`image_path` fourni → vraie exécution OCR) est **inchangé** — c'est
toujours le chemin utilisé par le endpoint générique `POST /agents/run` si un appelant fournit une
image directement. Le nouveau chemin (`ocr_text` fourni sans `image_path`) est purement additif :
aucun test existant ne pouvait dépendre d'un comportement qui n'existait pas avant.

## Le nouvel endpoint

```
POST /claims/{claim_id}/agents/run
```

Défini dans `app/api/v1/endpoints/agents.py`, sur un routeur dédié `claim_agents_router` (préfixe
`/claims/{claim_id}/agents`), distinct du routeur générique existant `/agents` (qui garde son
`POST /agents/run` bas niveau, où l'appelant construit `raw_data` lui-même — utile pour des tests
ou un futur usage direct sur une image seule).

```python
@claim_agents_router.post("/run")
async def run_agents_for_claim(
    claim_id: UUID,
    service: DocumentService = Depends(get_document_service),
    _operator: Operator = Depends(get_current_operator),
) -> dict[str, Any]:
    opening_form = service.get_opening_form(claim_id)
    raw_data = build_agent_raw_data(opening_form)
    return await manager.process_claim(str(claim_id), raw_data)
```

Trois lignes : récupérer le formulaire déjà fusionné (peu importe qu'il vienne de documents
uploadés, de saisie manuelle, ou d'un mélange des deux — Cours 3), le transformer en `raw_data`,
lancer le graphe d'agents. C'est délibérément fin — toute la logique intéressante vit dans les
agents eux-mêmes (Cours 4) et dans `DocumentService.get_opening_form()` (déjà existant, inchangé).

## Le parcours complet, de bout en bout

```
1. Upload constat  → POST /claims/{id}/documents (document_role auto-inféré ACCIDENT_REPORT, Cours 2)
   ou
   Saisie manuelle → POST /claims/{id}/documents/opening-form/manual (Cours 3)
2. Lecture du formulaire → GET /claims/{id}/documents/opening-form
3. Collaboration multi-agents → POST /claims/{id}/agents/run
   → OCR Agent (adopte le texte déjà connu)
   → Extraction Agent (aplati le formulaire en entités)
   → Fraud Agent (score de fraude LLM sur le résumé texte)
   → Legal Agent (règles de dates + LLM sur les champs juridiques)
   → Decision Agent (recommandation, jamais d'auto-approbation silencieuse)
   → Supervisor Agent (arbitrage final, filet de sécurité sur faible confiance)
```

La réponse de `POST /claims/{id}/agents/run` contient `agent_results` (statut/confiance/artefacts
par agent), `context` (l'état final, y compris `context.metadata["supervisor_summary"]` — le
résumé d'arbitrage) et `history` (le journal d'exécution horodaté).

## Ce qu'on n'a pas essayé de reconstruire

Le vrai `DecisionEngine` déterministe (`app/engines/decision/manager.py`) a besoin d'un
`EvidenceGraphResult` + `ValidationReport` complets — produits en mémoire pendant l'exécution du
pipeline linéaire sur *un document*, jamais persistés sous une forme réutilisable au niveau du
claim entier (`DocumentService._run_validation()` persiste des `ValidationDecision` en base, mais
documente déjà sa propre limite : "reflects the most recently ingested document's graph, not a
claim-wide view"). Reconstruire cet objet à partir de plusieurs documents aurait été un chantier à
part entière, plus risqué que la solution retenue : `decision_agent` (Cours 4) raisonne à un niveau
plus agrégé (complétude, score de fraude, conformité légale), avec le même vocabulaire
(`DecisionType`) mais des entrées différentes, adaptées à ce qui existe réellement au niveau claim.
C'est un choix de portée assumé, pas un oubli — documenté ici pour que la prochaine personne qui
lira ce code ne pense pas qu'il manque un branchement évident.

## Ce qui reste pour une V2

- Persister le texte OCR brut si l'analyse de fraude/légal s'avère insuffisante sur le seul résumé
  structuré (voir §"Décision" ci-dessus — un choix révisable si les retours utilisateurs le
  justifient).
- Déclencher `POST /claims/{id}/agents/run` automatiquement à la fin de l'ingestion/de la saisie
  manuelle plutôt que de laisser le frontend l'appeler explicitement — actuellement volontairement
  séparé pour rester simple à tester et à débugger (chaque étape a son propre endpoint, son propre
  résultat inspectable).
