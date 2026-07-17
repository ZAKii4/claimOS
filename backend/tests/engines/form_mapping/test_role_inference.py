from app.engines.form_mapping.manager import DocumentRole, infer_document_role


def test_police_report_family_infers_accident_report_role():
    assert infer_document_role("Police Report") == DocumentRole.ACCIDENT_REPORT


def test_ambiguous_families_are_not_inferred():
    # These families could belong to either party — guessing would silently
    # misfile real data, so the function must return None, never a guess.
    for family in ("Identity Card", "Insurance Attestation", "Invoice", "Medical Certificate"):
        assert infer_document_role(family) is None


def test_unknown_or_missing_family_infers_nothing():
    assert infer_document_role("UNKNOWN_DOCUMENT") is None
    assert infer_document_role(None) is None
    assert infer_document_role("") is None
