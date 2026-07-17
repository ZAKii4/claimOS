"""
Target schema for the "Formulaire d'Ouverture" (claim opening form).

Field layout mirrors the 4-step form (datasets/raw/Formulaire Ouverture.docx):
  1. Informations sur la police (+ conducteur, if different from the policy holder)
  2. Informations sur le sinistre (+ dégâts matériels de la partie adverse)
  3. Circonstances d'accident (+ informations sur les victimes)
  4. Détection de la fraude

Every leaf value is wrapped in a MappedField so no value is ever presented
without its confidence, provenance, and extraction method attached. Fields
with no matching extracted entity are explicit NOT_FOUND records, never
omitted or silently defaulted.
"""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class FieldStatus(StrEnum):
    FOUND = "FOUND"
    CONFLICT = "CONFLICT"  # found, but multiple sources disagreed; highest-confidence value kept
    NOT_FOUND = "NOT_FOUND"


class FieldSource(BaseModel):
    """Where a mapped value came from, one entry per contributing document."""
    document_id: str
    document_class: str | None = None
    page_index: int | None = None
    bounding_box: dict[str, float] | None = None
    extraction_method: str | None = None
    extractor_name: str | None = None
    llm_used: str | None = None
    confidence: float
    raw_value: str | None = None
    extracted_at: datetime


class MappedField(BaseModel):
    """A single form field with full traceability."""
    value: Any = None
    status: FieldStatus = FieldStatus.NOT_FOUND
    confidence: float = 0.0
    reason: str | None = Field(
        default=None,
        description="Explanation when status is NOT_FOUND (e.g. no extractor covers this field, "
        "or extractors ran but found nothing in the supplied documents).",
    )
    source: FieldSource | None = Field(
        default=None, description="Winning source. Present only when status != NOT_FOUND."
    )
    alternatives: list[FieldSource] = Field(
        default_factory=list,
        description="Other candidate sources that lost the conflict resolution, kept for audit.",
    )

    @classmethod
    def not_found(cls, reason: str) -> "MappedField":
        return cls(status=FieldStatus.NOT_FOUND, reason=reason)


def _unmapped() -> MappedField:
    return MappedField.not_found("Non mappé")


class ConducteurForm(BaseModel):
    nom: MappedField = Field(default_factory=_unmapped)
    prenom: MappedField = Field(default_factory=_unmapped)
    numero_cin: MappedField = Field(default_factory=_unmapped)
    date_naissance: MappedField = Field(default_factory=_unmapped)
    sexe: MappedField = Field(default_factory=_unmapped)
    date_permis: MappedField = Field(default_factory=_unmapped)
    categorie_permis: MappedField = Field(default_factory=_unmapped)
    numero_permis: MappedField = Field(default_factory=_unmapped)
    qualite: MappedField = Field(default_factory=_unmapped)


class PartieAdverseForm(BaseModel):
    marque_vehicule: MappedField = Field(default_factory=_unmapped)
    type_immatriculation: MappedField = Field(default_factory=_unmapped)
    immatriculation: MappedField = Field(default_factory=_unmapped)
    compagnie_adverse: MappedField = Field(default_factory=_unmapped)
    prenom: MappedField = Field(default_factory=_unmapped)
    nom: MappedField = Field(default_factory=_unmapped)
    numero_police: MappedField = Field(default_factory=_unmapped)
    numero_attestation: MappedField = Field(default_factory=_unmapped)
    numero_sinistre: MappedField = Field(default_factory=_unmapped)
    responsabilite: MappedField = Field(default_factory=_unmapped)


class VictimeForm(BaseModel):
    nature_victime: MappedField = Field(default_factory=_unmapped)
    numero_cin: MappedField = Field(default_factory=_unmapped)
    nom: MappedField = Field(default_factory=_unmapped)
    prenom: MappedField = Field(default_factory=_unmapped)
    numero_telephone: MappedField = Field(default_factory=_unmapped)
    qualite_victime: MappedField = Field(default_factory=_unmapped)
    classe: MappedField = Field(default_factory=_unmapped)
    type_procedure_recommandee: MappedField = Field(default_factory=_unmapped)
    type_profession: MappedField = Field(default_factory=_unmapped)
    accident_travail: MappedField = Field(default_factory=_unmapped)
    disponibilite_itt: MappedField = Field(default_factory=_unmapped)
    itt_jours: MappedField = Field(default_factory=_unmapped)
    opposition: MappedField = Field(default_factory=_unmapped)
    ville: MappedField = Field(default_factory=_unmapped)
    adresse: MappedField = Field(default_factory=_unmapped)
    exclue_garantie: MappedField = Field(default_factory=_unmapped)


class ClaimOpeningForm(BaseModel):
    """Full target schema for the "Pré-ouvrir un sinistre" form."""

    # ── Step 1: Informations sur la police ──────────────────────────
    numero_police: MappedField = Field(default_factory=_unmapped)
    nom_souscripteur: MappedField = Field(default_factory=_unmapped)
    prenom_souscripteur: MappedField = Field(default_factory=_unmapped)
    numero_cin_souscripteur: MappedField = Field(default_factory=_unmapped)
    numero_immatriculation: MappedField = Field(default_factory=_unmapped)
    categorie_vehicule: MappedField = Field(default_factory=_unmapped)
    date_effet_contrat: MappedField = Field(default_factory=_unmapped)
    date_echeance_contrat: MappedField = Field(default_factory=_unmapped)
    conducteur_est_souscripteur: MappedField = Field(default_factory=_unmapped)
    conducteur: ConducteurForm = Field(default_factory=ConducteurForm)

    # ── Step 2: Informations sur le sinistre ────────────────────────
    numero_pv: MappedField = Field(default_factory=_unmapped)
    pays_survenance: MappedField = Field(default_factory=_unmapped)
    lieu_survenance: MappedField = Field(default_factory=_unmapped)
    juridiction: MappedField = Field(default_factory=_unmapped)
    date_survenance: MappedField = Field(default_factory=_unmapped)
    heure_survenance: MappedField = Field(default_factory=_unmapped)
    victimes_blessees: MappedField = Field(default_factory=_unmapped)
    victimes_decedees: MappedField = Field(default_factory=_unmapped)
    autorite: MappedField = Field(default_factory=_unmapped)
    circonscription: MappedField = Field(default_factory=_unmapped)
    reference_cabinet: MappedField = Field(default_factory=_unmapped)
    degats_materiels_partie_adverse: MappedField = Field(default_factory=_unmapped)
    partie_adverse: PartieAdverseForm = Field(default_factory=PartieAdverseForm)

    # ── Step 3: Circonstances d'accident + victimes ─────────────────
    cas_bareme: MappedField = Field(default_factory=_unmapped)
    circonstances_accident: MappedField = Field(default_factory=_unmapped)
    responsabilite_pct: MappedField = Field(default_factory=_unmapped)
    description: MappedField = Field(default_factory=_unmapped)
    procedure_judiciaire: MappedField = Field(default_factory=_unmapped)
    victimes: list[VictimeForm] = Field(default_factory=list)

    # ── Step 4: Détection de la fraude ──────────────────────────────
    sinistre_suspicieux: MappedField = Field(default_factory=_unmapped)
    avocat_adverse: MappedField = Field(default_factory=_unmapped)
    fraud_indicators: list[str] = Field(
        default_factory=list,
        description="Free-text fraud signals surfaced by the Fraud Detection agent, if any.",
    )
