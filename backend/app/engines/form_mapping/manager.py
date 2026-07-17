"""
Form Mapping Engine.

Fuses ExtractedEntity data coming from *multiple* documents of a single
claim dossier (a police report, two vehicle registration titles, two
insurance attestations, medical certificates, ...) into one populated
ClaimOpeningForm, with per-field provenance and explicit NOT_FOUND status
when nothing in the supplied documents covers a field.

Role disambiguation: a raw ExtractedEntity only carries a generic
field_name (e.g. "vehicle_plate"); it doesn't know if it belongs to "our"
vehicle or the adverse party's. Today the pipeline has no automatic
document-to-party linking, so the caller must tag each document with a
DocumentRole (this is normally set by whoever routes the claim's documents,
e.g. an operator during triage, or a future document-linking engine).
Given that role, this engine knows which slot of the target form a given
field_name should fill.
"""

from collections import defaultdict
from dataclasses import dataclass
from enum import StrEnum

from app.engines.extraction.models import ExtractedEntity, ExtractionResult
from app.engines.form_mapping.schema import (
    ClaimOpeningForm,
    FieldSource,
    FieldStatus,
    MappedField,
    VictimeForm,
)


class DocumentRole(StrEnum):
    OWN_VEHICLE = "OWN_VEHICLE"
    ADVERSE_VEHICLE = "ADVERSE_VEHICLE"
    POLICY_HOLDER = "POLICY_HOLDER"
    VICTIM = "VICTIM"
    # The constat amiable / PV itself: claim-level facts (when/where/how the
    # accident happened) that belong to neither party specifically.
    ACCIDENT_REPORT = "ACCIDENT_REPORT"


@dataclass
class DocumentExtraction:
    """One document's extraction output, tagged with its role in the claim."""
    document_id: str
    role: DocumentRole
    result: ExtractionResult


# Classified families that unambiguously identify a document's role regardless
# of who uploaded it — the accident report is always "the accident report",
# never tied to a specific vehicle/party the way an ID card or an insurance
# attestation is (either could belong to the policy holder or the adverse
# party, and guessing wrong would silently misfile real data under the wrong
# party). Only families with exactly one possible role are auto-tagged here;
# everything else still requires an explicit DocumentRole from the caller.
AUTO_INFERRED_ROLES: dict[str, DocumentRole] = {
    "Police Report": DocumentRole.ACCIDENT_REPORT,
}


def infer_document_role(document_type_code: str | None) -> DocumentRole | None:
    """
    Deduces a DocumentRole from a document's classified family, when — and
    only when — that family unambiguously implies one role.

    Returns None (never guesses) for every family not in AUTO_INFERRED_ROLES,
    so the caller falls back to requiring an explicit role, exactly as before.
    """
    if not document_type_code:
        return None
    return AUTO_INFERRED_ROLES.get(document_type_code)


# Maps (role, internal extractor field_name) -> dotted path into ClaimOpeningForm.
# Fields with no mapping at all fall through to FIELDS_WITHOUT_EXTRACTOR below.
# Since LLMFieldExtractor (app/engines/extraction/extractors/llm/) started
# covering every remaining scalar ClaimOpeningForm field, every scalar field
# now has an entry here — only `victimes` (a list, handled separately by
# `_collect_victims`) and `fraud_indicators` (FraudAgent's domain, not a
# per-document extraction concern) remain unmapped.
FIELD_MAPPING: dict[tuple[DocumentRole, str], str] = {
    (DocumentRole.OWN_VEHICLE, "vehicle_plate"): "numero_immatriculation",
    (DocumentRole.OWN_VEHICLE, "owner_name"): "nom_souscripteur",
    (DocumentRole.OWN_VEHICLE, "national_id"): "numero_cin_souscripteur",
    (DocumentRole.OWN_VEHICLE, "policy_number"): "numero_police",
    (DocumentRole.OWN_VEHICLE, "prenom_souscripteur"): "prenom_souscripteur",
    (DocumentRole.OWN_VEHICLE, "categorie_vehicule"): "categorie_vehicule",
    (DocumentRole.OWN_VEHICLE, "date_effet_contrat"): "date_effet_contrat",
    (DocumentRole.OWN_VEHICLE, "date_echeance_contrat"): "date_echeance_contrat",
    (DocumentRole.OWN_VEHICLE, "conducteur_est_souscripteur"): "conducteur_est_souscripteur",
    (DocumentRole.OWN_VEHICLE, "conducteur_nom"): "conducteur.nom",
    (DocumentRole.OWN_VEHICLE, "conducteur_prenom"): "conducteur.prenom",
    (DocumentRole.OWN_VEHICLE, "conducteur_numero_cin"): "conducteur.numero_cin",
    (DocumentRole.OWN_VEHICLE, "conducteur_date_naissance"): "conducteur.date_naissance",
    (DocumentRole.OWN_VEHICLE, "conducteur_sexe"): "conducteur.sexe",
    (DocumentRole.OWN_VEHICLE, "conducteur_date_permis"): "conducteur.date_permis",
    (DocumentRole.OWN_VEHICLE, "conducteur_categorie_permis"): "conducteur.categorie_permis",
    (DocumentRole.OWN_VEHICLE, "conducteur_numero_permis"): "conducteur.numero_permis",
    (DocumentRole.OWN_VEHICLE, "conducteur_qualite"): "conducteur.qualite",
    (DocumentRole.ADVERSE_VEHICLE, "vehicle_plate"): "partie_adverse.immatriculation",
    (DocumentRole.ADVERSE_VEHICLE, "owner_name"): "partie_adverse.nom",
    (DocumentRole.ADVERSE_VEHICLE, "vehicle_brand"): "partie_adverse.marque_vehicule",
    (DocumentRole.ADVERSE_VEHICLE, "policy_number"): "partie_adverse.numero_police",
    (DocumentRole.ADVERSE_VEHICLE, "type_immatriculation"): "partie_adverse.type_immatriculation",
    (DocumentRole.ADVERSE_VEHICLE, "compagnie_adverse"): "partie_adverse.compagnie_adverse",
    (DocumentRole.ADVERSE_VEHICLE, "adverse_prenom"): "partie_adverse.prenom",
    (DocumentRole.ADVERSE_VEHICLE, "numero_attestation"): "partie_adverse.numero_attestation",
    (DocumentRole.ADVERSE_VEHICLE, "numero_sinistre"): "partie_adverse.numero_sinistre",
    (DocumentRole.ADVERSE_VEHICLE, "adverse_responsabilite"): "partie_adverse.responsabilite",
    (DocumentRole.ACCIDENT_REPORT, "numero_pv"): "numero_pv",
    (DocumentRole.ACCIDENT_REPORT, "pays_survenance"): "pays_survenance",
    (DocumentRole.ACCIDENT_REPORT, "lieu_survenance"): "lieu_survenance",
    (DocumentRole.ACCIDENT_REPORT, "juridiction"): "juridiction",
    (DocumentRole.ACCIDENT_REPORT, "date_survenance"): "date_survenance",
    (DocumentRole.ACCIDENT_REPORT, "heure_survenance"): "heure_survenance",
    (DocumentRole.ACCIDENT_REPORT, "victimes_blessees"): "victimes_blessees",
    (DocumentRole.ACCIDENT_REPORT, "victimes_decedees"): "victimes_decedees",
    (DocumentRole.ACCIDENT_REPORT, "autorite"): "autorite",
    (DocumentRole.ACCIDENT_REPORT, "circonscription"): "circonscription",
    (DocumentRole.ACCIDENT_REPORT, "reference_cabinet"): "reference_cabinet",
    (DocumentRole.ACCIDENT_REPORT, "degats_materiels_partie_adverse"): "degats_materiels_partie_adverse",
    (DocumentRole.ACCIDENT_REPORT, "cas_bareme"): "cas_bareme",
    (DocumentRole.ACCIDENT_REPORT, "circonstances_accident"): "circonstances_accident",
    (DocumentRole.ACCIDENT_REPORT, "responsabilite_pct"): "responsabilite_pct",
    (DocumentRole.ACCIDENT_REPORT, "description"): "description",
    (DocumentRole.ACCIDENT_REPORT, "procedure_judiciaire"): "procedure_judiciaire",
    (DocumentRole.ACCIDENT_REPORT, "sinistre_suspicieux"): "sinistre_suspicieux",
    (DocumentRole.ACCIDENT_REPORT, "avocat_adverse"): "avocat_adverse",
}

# Fields declared in ClaimOpeningForm that no extractor currently produces
# for any role (kept explicit, rather than inferred, so the NOT_FOUND reason
# is precise). Empty today: LLMFieldExtractor + FIELD_MAPPING above cover
# every scalar field. Kept as a real (not rhetorical) safety net for any
# future field added to the schema without a matching mapping.
FIELDS_WITHOUT_EXTRACTOR: set[str] = set()


def _to_field_source(
    entity: ExtractedEntity, document_id: str, document_class: str | None
) -> FieldSource:
    return FieldSource(
        document_id=document_id,
        document_class=document_class,
        page_index=entity.provenance.page_index,
        bounding_box=entity.provenance.bounding_box,
        extraction_method=entity.provenance.extraction_method,
        extractor_name=entity.provenance.extractor_name,
        llm_used=None,
        confidence=entity.confidence,
        raw_value=entity.raw_value,
        extracted_at=entity.provenance.timestamp,
    )


class FormMappingEngine:
    """Fuses per-document extraction results into one ClaimOpeningForm."""

    def map(self, documents: list[DocumentExtraction]) -> ClaimOpeningForm:
        form = ClaimOpeningForm()

        # 1. Bucket every candidate entity by its resolved target path.
        candidates: dict[str, list[tuple[ExtractedEntity, str, str | None]]] = defaultdict(list)
        for doc in documents:
            document_class = doc.result.document_class.family if doc.result.document_class else None
            all_entities = list(doc.result.loose_entities)
            for group in doc.result.groups:
                all_entities.extend(group.entities)

            for entity in all_entities:
                target_path = FIELD_MAPPING.get((doc.role, entity.field_name))
                if target_path is None:
                    continue
                candidates[target_path].append((entity, doc.document_id, document_class))

        # 2. Resolve each target path: highest confidence wins, rest kept as alternatives.
        for target_path, entries in candidates.items():
            entries.sort(key=lambda e: e[0].confidence, reverse=True)
            winner_entity, winner_doc_id, winner_class = entries[0]
            winner_source = _to_field_source(winner_entity, winner_doc_id, winner_class)
            alternatives = [
                _to_field_source(entity, doc_id, doc_class)
                for entity, doc_id, doc_class in entries[1:]
            ]
            status = FieldStatus.CONFLICT if alternatives else FieldStatus.FOUND
            mapped = MappedField(
                value=winner_entity.normalized_value,
                status=status,
                confidence=winner_entity.confidence,
                source=winner_source,
                alternatives=alternatives,
            )
            self.set_field(form, target_path, mapped)

        # 3. Explicitly mark every remaining declared-but-uncovered field.
        for target_path in FIELDS_WITHOUT_EXTRACTOR:
            existing = self.get_field(form, target_path)
            if existing is not None and existing.status == FieldStatus.NOT_FOUND:
                self.set_field(
                    form,
                    target_path,
                    MappedField.not_found(
                        "Aucun extracteur disponible pour ce champ (nécessite NER/LLM dédié)."
                    ),
                )

        # 4. Mark FIELD_MAPPING-covered fields that found nothing as a distinct reason.
        mapped_paths = {path for (_role, _field), path in FIELD_MAPPING.items()}
        for target_path in mapped_paths:
            existing = self.get_field(form, target_path)
            if existing is not None and existing.status == FieldStatus.NOT_FOUND:
                self.set_field(
                    form,
                    target_path,
                    MappedField.not_found(
                        "Extracteur disponible mais aucune entité trouvée dans les documents "
                        "fournis."
                    ),
                )

        # 5. Victims: a list, so it can't go through the single-MappedField
        # path logic above. Populated from any ACCIDENT_REPORT or VICTIM
        # tagged document that produced victime.<index>.<sub_field> entities
        # (LLMFieldExtractor). Victims are not fused/deduplicated across
        # documents (no automatic person-matching exists yet) — each
        # document's victims are appended as-is, in document order.
        form.victimes = self._collect_victims(documents)

        return form

    @staticmethod
    def _collect_victims(documents: list[DocumentExtraction]) -> list[VictimeForm]:
        victims: list[VictimeForm] = []
        for doc in documents:
            if doc.role not in (DocumentRole.ACCIDENT_REPORT, DocumentRole.VICTIM):
                continue

            document_class = doc.result.document_class.family if doc.result.document_class else None
            all_entities = list(doc.result.loose_entities)
            for group in doc.result.groups:
                all_entities.extend(group.entities)

            by_index: dict[int, dict[str, ExtractedEntity]] = defaultdict(dict)
            for entity in all_entities:
                if not entity.field_name.startswith("victime."):
                    continue
                parts = entity.field_name.split(".", 2)
                if len(parts) != 3:
                    continue
                _, idx_str, sub_field = parts
                try:
                    idx = int(idx_str)
                except ValueError:
                    continue
                existing = by_index[idx].get(sub_field)
                if existing is None or entity.confidence > existing.confidence:
                    by_index[idx][sub_field] = entity

            for idx in sorted(by_index):
                victim_form = VictimeForm()
                for sub_field, entity in by_index[idx].items():
                    if not hasattr(victim_form, sub_field):
                        continue
                    setattr(
                        victim_form,
                        sub_field,
                        MappedField(
                            value=entity.normalized_value,
                            status=FieldStatus.FOUND,
                            confidence=entity.confidence,
                            source=_to_field_source(entity, doc.document_id, document_class),
                        ),
                    )
                victims.append(victim_form)
        return victims

    @staticmethod
    def get_field(form: ClaimOpeningForm, path: str) -> MappedField | None:
        obj = form
        for part in path.split("."):
            obj = getattr(obj, part)
        return obj if isinstance(obj, MappedField) else None

    @staticmethod
    def set_field(form: ClaimOpeningForm, path: str, value: MappedField) -> None:
        parts = path.split(".")
        obj = form
        for part in parts[:-1]:
            obj = getattr(obj, part)
        setattr(obj, parts[-1], value)
