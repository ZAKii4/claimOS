from datetime import UTC, datetime

from app.engines.classification.models import DocumentClass
from app.engines.extraction.models import EntityGroup, ExtractedEntity, ExtractionResult, Provenance
from app.engines.form_mapping.manager import DocumentExtraction, DocumentRole, FormMappingEngine
from app.engines.form_mapping.schema import FieldStatus


def _entity(field_name: str, value: str, confidence: float, page_index: int = 0) -> ExtractedEntity:
    return ExtractedEntity(
        field_name=field_name,
        raw_value=value,
        normalized_value=value,
        entity_type="text",
        confidence=confidence,
        provenance=Provenance(
            page_index=page_index,
            extractor_name="test.extractor",
            extraction_method="regex",
            timestamp=datetime.now(UTC),
        ),
    )


def _extraction_result(document_class: str, entities: list[ExtractedEntity]) -> ExtractionResult:
    return ExtractionResult(
        document_class=DocumentClass(family=document_class),
        groups=[EntityGroup(group_type="Global", entities=entities)],
        global_confidence=0.8,
        execution_time_ms=1,
        extractors_used=["test.extractor"],
    )


def test_fusion_routes_same_field_name_to_different_slots_by_role():
    own_doc = DocumentExtraction(
        document_id="doc-own-vehicle",
        role=DocumentRole.OWN_VEHICLE,
        result=_extraction_result(
            "Vehicle Registration", [_entity("vehicle_plate", "10-019331", 0.9)]
        ),
    )
    adverse_doc = DocumentExtraction(
        document_id="doc-adverse-vehicle",
        role=DocumentRole.ADVERSE_VEHICLE,
        result=_extraction_result(
            "Vehicle Registration", [_entity("vehicle_plate", "8-020442", 0.85)]
        ),
    )

    form = FormMappingEngine().map([own_doc, adverse_doc])

    assert form.numero_immatriculation.status == FieldStatus.FOUND
    assert form.numero_immatriculation.value == "10-019331"
    assert form.numero_immatriculation.source.document_id == "doc-own-vehicle"

    assert form.partie_adverse.immatriculation.status == FieldStatus.FOUND
    assert form.partie_adverse.immatriculation.value == "8-020442"
    assert form.partie_adverse.immatriculation.source.document_id == "doc-adverse-vehicle"


def test_conflict_keeps_highest_confidence_and_records_alternative():
    doc_a = DocumentExtraction(
        document_id="doc-a",
        role=DocumentRole.OWN_VEHICLE,
        result=_extraction_result("Vehicle Registration", [_entity("owner_name", "MARTIN", 0.6)]),
    )
    doc_b = DocumentExtraction(
        document_id="doc-b",
        role=DocumentRole.OWN_VEHICLE,
        result=_extraction_result("Insurance Attestation", [_entity("owner_name", "MARTINE", 0.9)]),
    )

    form = FormMappingEngine().map([doc_a, doc_b])

    assert form.nom_souscripteur.status == FieldStatus.CONFLICT
    assert form.nom_souscripteur.value == "MARTINE"
    assert form.nom_souscripteur.source.document_id == "doc-b"
    assert len(form.nom_souscripteur.alternatives) == 1
    assert form.nom_souscripteur.alternatives[0].document_id == "doc-a"


def test_every_scalar_field_now_has_a_mapping_or_extractor():
    """
    FIELDS_WITHOUT_EXTRACTOR used to list every field LLMFieldExtractor now
    covers (conducteur.*, dates, circumstances...) — it's an empty set today,
    kept only as a safety net for a future schema field added without a
    matching FIELD_MAPPING entry. An unmapped field with no documents
    supplied gets the generic "aucune entité trouvée" reason, not "Aucun
    extracteur disponible", since a mapping now genuinely exists for it.
    """
    form = FormMappingEngine().map([])

    assert form.date_survenance.status == FieldStatus.NOT_FOUND
    assert "aucune entité trouvée" in form.date_survenance.reason
    assert form.conducteur.nom.status == FieldStatus.NOT_FOUND
    assert "aucune entité trouvée" in form.conducteur.nom.reason


def test_field_with_extractor_but_no_matching_entity_has_distinct_reason():
    doc = DocumentExtraction(
        document_id="doc-a",
        role=DocumentRole.OWN_VEHICLE,
        result=_extraction_result("Vehicle Registration", []),
    )

    form = FormMappingEngine().map([doc])

    assert form.numero_immatriculation.status == FieldStatus.NOT_FOUND
    assert "aucune entité trouvée" in form.numero_immatriculation.reason


def test_conducteur_fields_map_from_own_vehicle_role():
    doc = DocumentExtraction(
        document_id="doc-a",
        role=DocumentRole.OWN_VEHICLE,
        result=_extraction_result(
            "Police Report",
            [
                _entity("conducteur_nom", "BENALI", 0.9),
                _entity("conducteur_prenom", "Ahmed", 0.9),
            ],
        ),
    )

    form = FormMappingEngine().map([doc])

    assert form.conducteur.nom.status == FieldStatus.FOUND
    assert form.conducteur.nom.value == "BENALI"
    assert form.conducteur.prenom.value == "Ahmed"


def test_accident_report_role_maps_claim_level_facts():
    doc = DocumentExtraction(
        document_id="doc-a",
        role=DocumentRole.ACCIDENT_REPORT,
        result=_extraction_result(
            "Police Report",
            [
                _entity("date_survenance", "2026-07-10", 0.9),
                _entity("lieu_survenance", "Casablanca", 0.8),
            ],
        ),
    )

    form = FormMappingEngine().map([doc])

    assert form.date_survenance.status == FieldStatus.FOUND
    assert form.date_survenance.value == "2026-07-10"
    assert form.lieu_survenance.value == "Casablanca"


def test_victims_are_collected_from_accident_report_document():
    entities = [
        _entity("victime.0.nom", "DUPONT", 0.9),
        _entity("victime.0.prenom", "Jean", 0.9),
        _entity("victime.1.nom", "DURAND", 0.8),
    ]
    doc = DocumentExtraction(
        document_id="doc-a",
        role=DocumentRole.ACCIDENT_REPORT,
        result=_extraction_result("Police Report", entities),
    )

    form = FormMappingEngine().map([doc])

    assert len(form.victimes) == 2
    assert form.victimes[0].nom.value == "DUPONT"
    assert form.victimes[0].prenom.value == "Jean"
    assert form.victimes[1].nom.value == "DURAND"
    assert form.victimes[1].prenom.status == FieldStatus.NOT_FOUND


def test_victims_ignored_for_unrelated_document_roles():
    doc = DocumentExtraction(
        document_id="doc-a",
        role=DocumentRole.OWN_VEHICLE,
        result=_extraction_result("Vehicle Registration", [_entity("victime.0.nom", "DUPONT", 0.9)]),
    )

    form = FormMappingEngine().map([doc])

    assert form.victimes == []
