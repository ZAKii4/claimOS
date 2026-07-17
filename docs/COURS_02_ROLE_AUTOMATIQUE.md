# Cours 2 — Inférence automatique du `DocumentRole`

## Le problème, en une phrase

`ClaimOpeningForm` a ~40 champs. 5 sont couverts par des extracteurs regex/layout, ~35 par un
extracteur LLM (`LLMFieldExtractor`) — mais **aucune de ces valeurs n'atteint le formulaire final**
tant que le document dont elles proviennent n'est pas explicitement tagué avec un `DocumentRole`
(`OWN_VEHICLE`, `ADVERSE_VEHICLE`, `POLICY_HOLDER`, `VICTIM`, `ACCIDENT_REPORT`). Ce tag était
100% manuel, optionnel, et dans les faits presque jamais renseigné pour le document qui compte le
plus : le constat/PV, seul porteur du rôle `ACCIDENT_REPORT`.

## Où ça se joue dans le code

Trois fichiers, dans l'ordre où les données les traversent :

1. **`app/engines/classification/rules.py`** — classe chaque page en une "famille"
   (`DocumentClass.family`) via des règles à base de mots-clés sur le texte OCR. Pour le constat :
   ```python
   is_constat = "constat amiable" in raw_text or "declaration d'accident" in raw_text
   is_moroccan_pv = has_authority and has_accident_ref  # préfecture/gendarmerie + accident/PV
   if is_constat or is_moroccan_pv:
       predictions.append(ClassificationPrediction(
           document_class=DocumentClass(family="Police Report", subtype=...),
           confidence=0.9 if is_constat else 0.85,
           ...
       ))
   ```
   La famille `"Police Report"` est donc déjà calculée, avec une confiance, **avant** qu'on ait
   besoin de la connaître pour le rôle.

2. **`app/pipeline/segmentation.py`** — regroupe les pages classifiées en segments contigus
   (`DocumentSegment.document_type_code`), un segment = un document logique = une future ligne
   `ClaimDocument`. C'est cette valeur (`"Police Report"`, `"Invoice"`, `"Identity Card"`, etc.)
   qui atteint `DocumentService.ingest_document()`.

3. **`app/engines/form_mapping/manager.py`** (nouveau code) — la fonction `infer_document_role()` :

   ```python
   AUTO_INFERRED_ROLES: dict[str, DocumentRole] = {
       "Police Report": DocumentRole.ACCIDENT_REPORT,
   }

   def infer_document_role(document_type_code: str | None) -> DocumentRole | None:
       if not document_type_code:
           return None
       return AUTO_INFERRED_ROLES.get(document_type_code)
   ```

## Pourquoi une seule entrée dans la table, pas cinq

Les familles connues du classifieur (§ `rules.py`) sont : `Medical Certificate`, `Police Report`,
`Insurance Attestation`, `Identity Card`, plus `Invoice`/`Repair Estimate` (venant de
`classifier.py`). On pourrait être tenté de toutes les mapper vers un rôle. C'est un piège :

- `"Police Report"` → `ACCIDENT_REPORT` : **sans ambiguïté**. Un constat/PV décrit toujours
  l'accident lui-même, jamais un véhicule ou une personne en particulier. C'est *le* cas où la
  famille du document détermine entièrement son rôle.
- `"Identity Card"` → pourrait être la CIN du souscripteur (`POLICY_HOLDER`), du conducteur adverse,
  ou d'une victime (`VICTIM`). La famille seule ne le dit pas.
- `"Insurance Attestation"` → pourrait être celle de l'assuré (`OWN_VEHICLE`/`POLICY_HOLDER`) ou de
  la partie adverse (`ADVERSE_VEHICLE`).

**Décision de conception : ne jamais deviner quand plusieurs rôles sont également plausibles.**
Une fausse déduction silencieuse (ex. tagger une CIN adverse comme `POLICY_HOLDER`) est un bug plus
grave et plus difficile à détecter qu'un champ `NOT_FOUND` — le premier pollue les données avec une
fausse confiance de 1.0 implicite, le second est un état explicite et visible dans l'UI
(`FieldStatus.NOT_FOUND`, avec `reason`). Le principe directeur : *inférer seulement ce qui serait
de toute façon la seule réponse correcte, jamais un "meilleur choix probable"*.

## Où c'est branché : `DocumentService.ingest_document()`

```python
# app/services/document_service.py
effective_role = document_role or infer_document_role(segment.document_type_code)

document = ClaimDocument(
    ...,
    document_role=effective_role.value if effective_role else None,
    ...
)
```

Règle de priorité : **le choix explicite de l'appelant (paramètre `document_role` du endpoint
`POST /claims/{claim_id}/documents`) l'emporte toujours**. L'inférence automatique n'intervient que
si l'appelant n'a rien précisé (`document_role is None`). Ça préserve deux propriétés :

- Un opérateur qui *sait* qu'un document a un rôle particulier (et le précise) n'est jamais
  contredit par le classifieur.
- Un opérateur qui *ne sait pas* / *ne pense pas à le préciser* pour le constat obtient maintenant
  automatiquement le bon comportement — c'est exactement le cas majoritaire observé en base
  (41 claims sur 43 n'avaient jamais tagué `ACCIDENT_REPORT`).

## Ce que ça corrige concrètement

Avant : un opérateur uploade un constat amiable sans préciser de rôle → `document_role=None` en
base → `DocumentService.get_opening_form()` l'exclut silencieusement
(`if not document.document_role: continue`) → tous les champs "niveau sinistre" restent
`NOT_FOUND` malgré une extraction LLM potentiellement réussie.

Après : le même upload → classification détecte `family="Police Report"` → `infer_document_role`
retourne `ACCIDENT_REPORT` → le document est persisté avec ce rôle → `FormMappingEngine.map()` peut
router `circonstances_accident`, `lieu_survenance`, `date_survenance`, `victimes`,
`responsabilite_pct`, etc. vers le formulaire final.

## Limite assumée, et piste d'amélioration future

Cette correction ne résout que le cas du constat/PV — le cas le plus fréquent et le plus impactant
(c'est lui qui porte la quasi-totalité des champs "sinistre"). Les documents ambigus
(CIN, attestations) nécessitent toujours un choix explicite. Une amélioration future légitime
serait un second signal — par exemple, un opérateur choisissant d'abord "j'ajoute les documents du
véhicule adverse" dans l'UI, qui préremplirait `document_role=ADVERSE_VEHICLE` côté frontend pour
tous les fichiers glissés dans cette zone, sans que le backend ait besoin de deviner à partir du
contenu seul. C'est un choix d'UX, pas un choix d'extraction — hors du périmètre backend actuel.
