from app.agents.claim_bridge import build_agent_raw_data
from app.engines.form_mapping.schema import ClaimOpeningForm, FieldStatus, MappedField, VictimeForm


def test_build_agent_raw_data_summarizes_found_fields_only():
    form = ClaimOpeningForm()
    form.numero_police = MappedField(value="AXA123", status=FieldStatus.FOUND, confidence=0.9)
    form.lieu_survenance = MappedField(value="Casablanca", status=FieldStatus.FOUND, confidence=0.7)
    form.juridiction = MappedField.not_found("Non mappé")  # must not leak into the summary

    raw_data = build_agent_raw_data(form)

    assert "numero_police: AXA123" in raw_data["ocr_text"]
    assert "lieu_survenance: Casablanca" in raw_data["ocr_text"]
    assert "juridiction" not in raw_data["ocr_text"]
    assert raw_data["ocr_confidence"] == (0.9 + 0.7) / 2
    assert raw_data["opening_form"]["numero_police"]["value"] == "AXA123"


def test_build_agent_raw_data_on_empty_form_is_empty_not_fabricated():
    raw_data = build_agent_raw_data(ClaimOpeningForm())

    assert raw_data["ocr_text"] == ""
    assert raw_data["ocr_confidence"] == 0.0


def test_build_agent_raw_data_includes_victim_fields():
    form = ClaimOpeningForm()
    form.victimes.append(
        VictimeForm(nom=MappedField(value="ALAOUI", status=FieldStatus.FOUND, confidence=0.6))
    )

    raw_data = build_agent_raw_data(form)

    assert "victimes.0.nom: ALAOUI" in raw_data["ocr_text"]
