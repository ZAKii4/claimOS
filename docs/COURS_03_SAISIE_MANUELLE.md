# Cours 3 — Le parcours de saisie manuelle

## Le besoin

Un sinistre n'arrive pas toujours avec ses pièces justificatives. Un opérateur peut l'ouvrir suite
à un appel téléphonique, avant réception du constat scanné. Il faut donc un second chemin, à côté
de l'upload, qui construise le même `ClaimOpeningForm` mais à partir de valeurs saisies à la main.

## Ce qui existait déjà — et pourquoi ce n'était pas suffisant

`PATCH /claims/{claim_id}/documents/opening-form` (`DocumentService.correct_field()`) permettait
déjà de poser une valeur sur **un seul champ** :

```python
def correct_field(self, claim_id, field_path, value, operator) -> ClaimOpeningForm:
    ...
    overrides = dict(claim.field_overrides or {})
    overrides[field_path] = {
        "value": value,
        "corrected_by": operator.full_name,
        "corrected_at": datetime.now(timezone.utc).isoformat(),
    }
    claim.field_overrides = overrides
    self._db.add(claim)
    self._db.commit()
    return self.get_opening_form(claim_id)
```

Ce mécanisme fonctionne, mais un formulaire complet a une quarantaine de champs. Faire une saisie
manuelle complète en appelant ce endpoint 40 fois — avec 40 allers-retours réseau, 40 commits — est
correct fonctionnellement mais mauvais en pratique : lent, non atomique (un crash à mi-parcours
laisse le formulaire à moitié rempli), pas d'erreur groupée en cas de typo sur plusieurs champs.

## Principe : c'est le même geste, en bulk

Une correction manuelle et une saisie manuelle initiale sont, du point de vue du modèle de
données, **exactement la même chose** : « ce champ vaut X, décidé par un humain, confiance 1.0,
prioritaire sur toute extraction automatique ». Il n'y avait donc pas besoin d'un nouveau modèle de
données ni d'une nouvelle table — seulement d'un endpoint qui applique ce même geste à plusieurs
champs dans une seule transaction.

### Refactorisation de `document_service.py`

`correct_field()` est devenu un cas particulier de `submit_manual_fields()` :

```python
def correct_field(self, claim_id, field_path, value, operator) -> ClaimOpeningForm:
    return self.submit_manual_fields(claim_id, {field_path: value}, operator)

def submit_manual_fields(
    self, claim_id: UUID, fields: dict[str, object], operator: Operator
) -> ClaimOpeningForm:
    claim = self._claims.get_by_id(claim_id)
    if claim is None:
        raise EntityNotFoundError("ClaimFile", str(claim_id))
    if not fields:
        raise BusinessValidationError("No fields supplied.")

    invalid_paths = [p for p in fields if not _is_correctable(p)]
    if invalid_paths:
        raise BusinessValidationError(
            f"The following fields are not correctable on ClaimOpeningForm: "
            f"{', '.join(sorted(invalid_paths))}"
        )

    now = datetime.now(timezone.utc).isoformat()
    overrides = dict(claim.field_overrides or {})
    for field_path, value in fields.items():
        overrides[field_path] = {"value": value, "corrected_by": operator.full_name, "corrected_at": now}
    claim.field_overrides = overrides
    self._db.add(claim)
    self._db.commit()
    return self.get_opening_form(claim_id)
```

Deux garanties volontairement conservées de l'ancien comportement :

1. **Validation avant écriture, jamais partielle** : chaque `field_path` est vérifié contre le
   schéma `ClaimOpeningForm` (`FormMappingEngine.get_field()`) *avant* toute modification. Si un
   seul chemin est invalide (typo, ou un chemin de liste comme `victimes.0.nom`, pas encore
   supporté), **tout le lot est rejeté** — pas de sauvegarde à moitié faite qui laisserait le
   formulaire dans un état incohérent sans que l'opérateur le sache.
2. **Réutilisation de `get_opening_form()`** en fin de méthode : la réponse renvoyée est le
   formulaire recalculé, overrides compris, exactement comme pour une correction simple — le
   frontend n'a pas deux formats de réponse différents à gérer selon le chemin emprunté.

### Le nouvel endpoint

```
POST /claims/{claim_id}/documents/opening-form/manual
Body: {"fields": {"numero_police": "AXA123", "lieu_survenance": "Casablanca", "conducteur.nom": "Dupont"}}
→ 200 ClaimOpeningForm (recalculé, avec les valeurs saisies en status=FOUND, confidence=1.0)
```

Défini dans `app/api/v1/endpoints/documents.py`, sous le même routeur que
`GET/PATCH .../opening-form` (préfixe `/claims/{claim_id}/documents`) — c'est cohérent avec le
reste du module : toutes les opérations qui touchent le formulaire d'ouverture d'un claim vivent au
même endroit, qu'elles viennent d'un document ou d'une saisie humaine.

Schéma de requête (`app/schemas/document.py`) :

```python
class ManualOpeningFormRequest(BaseModel):
    fields: dict[str, Any] = Field(
        description="Dotted ClaimOpeningForm path -> value, e.g. "
        "{'numero_police': 'AXA123', 'lieu_survenance': 'Casablanca'}."
    )
```

Un simple dictionnaire plat, avec la même convention de "chemin pointé" que
`FieldCorrectionRequest` — pas de nouveau format à apprendre pour le frontend.

## Les deux parcours cohabitent

Rien n'empêche un opérateur de commencer par une saisie manuelle partielle (les infos qu'il a eues
au téléphone), puis d'uploader le constat quand il arrive — l'extraction automatique remplira les
champs encore `NOT_FOUND`, sans écraser ce qui a déjà été saisi à la main : `_apply_overrides()`
(déjà existant, inchangé) applique toujours les corrections manuelles **après** la fusion des
extractions automatiques, donc une valeur manuelle reste prioritaire même si un document upload
ensuite propose une valeur différente pour le même champ. C'est le comportement voulu : une
correction humaine explicite ne doit jamais être silencieusement écrasée par une extraction
automatique ultérieure.

## Ce qui reste hors périmètre (assumé)

- Les champs de liste (`victimes.<index>.<champ>`) ne sont pas encore saisissables via ce
  mécanisme — la même limite que `correct_field()` avait déjà (`get_field`/`set_field` ne
  résolvent que des attributs, pas des index de liste). Les corriger nécessiterait d'étendre
  `FormMappingEngine.get_field`/`set_field` pour parser des chemins avec index — un chantier séparé
  si le besoin se confirme.
- La création initiale de la ligne `ClaimFile` elle-même (le `POST /claims` qui alloue un
  `claim_id`) n'a pas changé — ce cours ne couvre que ce qui se passe *après*, une fois qu'un
  `claim_id` existe. Le choix "manuel vs upload" est donc un choix fait *au niveau du remplissage
  du formulaire*, pas de la création du dossier — ce qui est plus flexible : un même claim peut
  mélanger les deux au fil du temps, comme décrit ci-dessus.
