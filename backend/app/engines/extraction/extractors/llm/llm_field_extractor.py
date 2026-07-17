"""
LLM-based structured field extractor.

The five regex/layout extractors under app/engines/extraction/extractors/
only ever covered 5 of the ~40 fields ClaimOpeningForm declares (vehicle
plate, policy number, national id, owner name, vehicle brand) — regex
patterns don't generalize to free-text fields like accident circumstances,
driver details, or victim information, and can't be written per document
template for "any type of document". This extractor asks a real local LLM
(via the same LLMManager/GuardrailsEngine JSON pattern already used by
ReasoningEngine/PlanningEngine) to read the OCR'd page text once and return
every field it can actually find, each with its own confidence — instead of
one regex per field, one model call covers all of them and degrades
gracefully (per-field, not per-document) when a field simply isn't present.
"""

import json
import logging

from app.config.settings import get_settings
from app.engines.classification.models import DocumentClassificationResult
from app.engines.extraction.async_bridge import run_async
from app.engines.extraction.base import BaseExtractor
from app.engines.extraction.confidence import ConfidenceAdjuster
from app.engines.extraction.models import ExtractedEntity, Provenance
from app.engines.layout.models import LayoutAnalysisResult
from app.engines.ocr.models import OCRResult
from app.llm.guardrails import GuardrailsEngine
from app.llm.manager import LLMManager
from app.llm.models import LLMRequest, Message

logger = logging.getLogger("claimOS.extraction.llm")

# field_name -> (french description shown to the LLM, value type)
# value type drives both the prompt's expected JSON shape and light
# post-parse validation (date format, bool coercion).
SCALAR_FIELD_SPECS: dict[str, tuple[str, str]] = {
    # Accident report / claim-level facts (independent of any one party)
    "numero_pv": ("Numéro du procès-verbal (PV) établi par les autorités", "text"),
    "pays_survenance": ("Pays où l'accident est survenu", "text"),
    "lieu_survenance": ("Lieu précis de survenance de l'accident (ville, adresse, route)", "text"),
    "juridiction": ("Juridiction ou tribunal compétent mentionné", "text"),
    "date_survenance": ("Date de survenance de l'accident", "date"),
    "heure_survenance": ("Heure de survenance de l'accident, format HH:MM", "text"),
    "victimes_blessees": ("Y a-t-il des victimes blessées mentionnées dans le document", "boolean"),
    "victimes_decedees": ("Y a-t-il des victimes décédées mentionnées dans le document", "boolean"),
    "autorite": ("Autorité ou service ayant établi le constat (police, gendarmerie...)", "text"),
    "circonscription": ("Circonscription ou secteur administratif mentionné", "text"),
    "reference_cabinet": ("Référence du cabinet d'expertise mentionnée", "text"),
    "degats_materiels_partie_adverse": (
        "Description des dégâts matériels constatés sur le véhicule adverse", "text"
    ),
    "cas_bareme": ("Cas du barème de responsabilité applicable (ex: 'Cas 4')", "text"),
    "circonstances_accident": ("Description des circonstances de l'accident", "text"),
    "responsabilite_pct": (
        "Pourcentage de responsabilité attribué à l'assuré, un nombre entre 0 et 100", "number"
    ),
    "description": ("Description générale du sinistre", "text"),
    "procedure_judiciaire": ("Description d'une procédure judiciaire en cours, si mentionnée", "text"),
    "sinistre_suspicieux": (
        "Des éléments du document suggèrent-ils un sinistre suspect ou frauduleux "
        "(incohérences, déclarations contradictoires...)", "boolean",
    ),
    "avocat_adverse": ("Nom de l'avocat de la partie adverse, si mentionné", "text"),
    # Own vehicle / policy holder
    "categorie_vehicule": ("Catégorie ou type du véhicule assuré", "text"),
    "date_effet_contrat": ("Date d'effet du contrat d'assurance", "date"),
    "date_echeance_contrat": ("Date d'échéance du contrat d'assurance", "date"),
    "conducteur_est_souscripteur": (
        "Le conducteur du véhicule est-il la même personne que le souscripteur de la police",
        "boolean",
    ),
    "prenom_souscripteur": ("Prénom du souscripteur de la police (assuré)", "text"),
    "conducteur_nom": ("Nom de famille du conducteur du véhicule au moment de l'accident", "text"),
    "conducteur_prenom": ("Prénom du conducteur du véhicule au moment de l'accident", "text"),
    "conducteur_numero_cin": ("Numéro de carte d'identité nationale (CIN) du conducteur", "text"),
    "conducteur_date_naissance": ("Date de naissance du conducteur", "date"),
    "conducteur_sexe": ("Sexe du conducteur (M/F)", "text"),
    "conducteur_date_permis": ("Date d'obtention du permis de conduire du conducteur", "date"),
    "conducteur_categorie_permis": ("Catégorie du permis de conduire du conducteur", "text"),
    "conducteur_numero_permis": ("Numéro du permis de conduire du conducteur", "text"),
    "conducteur_qualite": (
        "Qualité du conducteur par rapport au véhicule (propriétaire, locataire, salarié...)", "text"
    ),
    # Adverse party
    "type_immatriculation": ("Type d'immatriculation du véhicule adverse", "text"),
    "compagnie_adverse": ("Compagnie d'assurance de la partie adverse", "text"),
    "adverse_prenom": ("Prénom du conducteur/propriétaire du véhicule adverse", "text"),
    "numero_attestation": ("Numéro d'attestation d'assurance de la partie adverse", "text"),
    "numero_sinistre": ("Numéro de sinistre de la partie adverse, si mentionné", "text"),
    "adverse_responsabilite": (
        "Description de la responsabilité attribuée à la partie adverse", "text"
    ),
}

# Each victim entity in the "victimes" list uses these sub-fields.
VICTIM_FIELD_SPECS: dict[str, tuple[str, str]] = {
    "nature_victime": ("Nature de la victime (conducteur, passager, piéton...)", "text"),
    "numero_cin": ("Numéro de carte d'identité nationale de la victime", "text"),
    "nom": ("Nom de famille de la victime", "text"),
    "prenom": ("Prénom de la victime", "text"),
    "numero_telephone": ("Numéro de téléphone de la victime", "text"),
    "qualite_victime": ("Qualité de la victime", "text"),
    "classe": ("Classe de la victime, si mentionnée", "text"),
    "type_procedure_recommandee": ("Type de procédure recommandée pour cette victime", "text"),
    "type_profession": ("Profession de la victime", "text"),
    "accident_travail": ("S'agit-il d'un accident du travail pour cette victime", "boolean"),
    "disponibilite_itt": ("Une ITT (incapacité temporaire totale) a-t-elle été prononcée", "boolean"),
    "itt_jours": ("Nombre de jours d'ITT prononcés", "number"),
    "opposition": ("La victime a-t-elle fait opposition", "boolean"),
    "ville": ("Ville de résidence de la victime", "text"),
    "adresse": ("Adresse de la victime", "text"),
    "exclue_garantie": ("La victime est-elle exclue de la garantie", "boolean"),
}

_TYPE_LABELS = {"text": "chaîne ou null", "date": "'AAAA-MM-JJ' ou null", "boolean": "true/false/null", "number": "nombre ou null"}


def _build_prompt(raw_text: str) -> str:
    fields_desc = "\n".join(
        f'  - "{name}" ({_TYPE_LABELS[kind]}): {desc}'
        for name, (desc, kind) in SCALAR_FIELD_SPECS.items()
    )
    victim_desc = "\n".join(
        f'    - "{name}" ({_TYPE_LABELS[kind]}): {desc}'
        for name, (desc, kind) in VICTIM_FIELD_SPECS.items()
    )
    return (
        "Tu es un système d'extraction d'information pour un assureur. Lis le texte "
        "OCR d'un document de sinistre automobile ci-dessous et extrais uniquement les "
        "informations réellement présentes. N'invente jamais une valeur : si un champ "
        "n'apparaît pas dans le texte, sa valeur doit être `null` et sa confiance `0.0`.\n\n"
        "Réponds avec UNIQUEMENT un objet JSON de la forme :\n"
        "{\n"
        '  "fields": {\n'
        '    "<nom_du_champ>": {"value": <valeur ou null>, "confidence": <0.0-1.0>},\n'
        "    ...\n"
        "  },\n"
        '  "victimes": [\n'
        "    {\n"
        f"{victim_desc}\n"
        "    }\n"
        "  ]\n"
        "}\n\n"
        f"Champs possibles pour \"fields\" (inclus une entrée pour chacun) :\n{fields_desc}\n\n"
        "Le tableau \"victimes\" ne contient que les personnes explicitement décrites comme "
        "victimes/blessées dans le document — liste vide si aucune.\n\n"
        f"Texte OCR du document :\n\"\"\"\n{raw_text}\n\"\"\""
    )


def _full_text(ocr_result: OCRResult) -> str:
    if not ocr_result.page:
        return ""
    lines = []
    for block in ocr_result.page.blocks:
        for line in block.lines:
            lines.append(" ".join(w.text for w in line.words))
    return "\n".join(lines)


def _coerce_value(raw_value, value_type: str) -> tuple[object, bool]:
    """Returns (normalized_value, is_valid) for the declared field type."""
    if raw_value is None:
        return None, True
    if value_type == "boolean":
        if isinstance(raw_value, bool):
            return raw_value, True
        return bool(raw_value), False
    if value_type == "number":
        try:
            return float(raw_value), True
        except (TypeError, ValueError):
            return raw_value, False
    # "date" and "text" both pass through as strings; date format validity
    # is a soft signal (still recorded) rather than a hard rejection, since
    # OCR'd dates come in many real-world formats.
    text = str(raw_value).strip()
    if value_type == "date":
        import re

        is_valid = bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", text))
        return text, is_valid
    return text, True


class LLMFieldExtractor(BaseExtractor):
    """Fills every field a regex/layout extractor doesn't cover, via a real LLM call."""

    def __init__(self, llm_manager: LLMManager | None = None) -> None:
        self._llm_manager = llm_manager

    @property
    def name(self) -> str:
        return "llm.field_extractor"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def priority(self) -> int:
        # Lower than every deterministic extractor: regex/layout wins ties
        # on fields both can produce (e.g. it re-derives vehicle_plate too,
        # as a cross-check candidate, but should not outrank the dedicated
        # extractor when confidences are close).
        return 40

    @property
    def supported_document_families(self) -> list[str]:
        return ["*"]

    def extract(
        self,
        ocr_result: OCRResult,
        layout_result: LayoutAnalysisResult,
        classification: DocumentClassificationResult,
    ) -> list[ExtractedEntity]:
        raw_text = _full_text(ocr_result)
        if not raw_text.strip():
            return []

        parsed = run_async(self._call_llm(raw_text))
        if parsed is None:
            return []

        entities: list[ExtractedEntity] = []
        entities.extend(self._scalar_entities(parsed.get("fields") or {}))
        entities.extend(self._victim_entities(parsed.get("victimes") or []))
        return entities

    async def _call_llm(self, raw_text: str) -> dict | None:
        llm = self._llm_manager or LLMManager()
        request = LLMRequest(
            model=get_settings().OLLAMA_DEFAULT_MODEL,
            messages=[Message(role="user", content=_build_prompt(raw_text))],
            temperature=0.0,
            response_format={"type": "json_object"},
        )
        try:
            response = await llm.generate(request)
            return GuardrailsEngine.validate_json_output(response.choices[0].content)
        except Exception as e:
            logger.warning("LLM field extraction failed, degrading to no entities: %s", e)
            return None

    def _scalar_entities(self, fields: dict) -> list[ExtractedEntity]:
        entities = []
        for field_name, (_, value_type) in SCALAR_FIELD_SPECS.items():
            payload = fields.get(field_name)
            if not isinstance(payload, dict):
                continue
            raw_value = payload.get("value")
            if raw_value is None:
                continue

            normalized, is_valid = _coerce_value(raw_value, value_type)
            llm_confidence = payload.get("confidence")
            try:
                base_confidence = max(0.0, min(1.0, float(llm_confidence)))
            except (TypeError, ValueError):
                base_confidence = 0.5

            entity = ExtractedEntity(
                field_name=field_name,
                raw_value=str(raw_value),
                normalized_value=normalized,
                entity_type=value_type,
                confidence=base_confidence,
                provenance=Provenance(
                    page_index=0,
                    extractor_name=self.name,
                    extraction_method="llm",
                ),
            )
            entity.confidence = ConfidenceAdjuster.adjust(entity, is_valid)
            if entity.confidence > 0.3:
                entities.append(entity)
        return entities

    def _victim_entities(self, victims: list) -> list[ExtractedEntity]:
        entities = []
        for idx, victim in enumerate(victims):
            if not isinstance(victim, dict):
                continue
            for sub_field, (_, value_type) in VICTIM_FIELD_SPECS.items():
                raw_value = victim.get(sub_field)
                if raw_value is None:
                    continue
                normalized, is_valid = _coerce_value(raw_value, value_type)
                entity = ExtractedEntity(
                    field_name=f"victime.{idx}.{sub_field}",
                    raw_value=str(raw_value),
                    normalized_value=normalized,
                    entity_type=value_type,
                    confidence=0.6,
                    provenance=Provenance(
                        page_index=0,
                        extractor_name=self.name,
                        extraction_method="llm",
                    ),
                )
                entity.confidence = ConfidenceAdjuster.adjust(entity, is_valid)
                if entity.confidence > 0.3:
                    entities.append(entity)
        return entities

    def normalize(self, raw_value):
        return raw_value
