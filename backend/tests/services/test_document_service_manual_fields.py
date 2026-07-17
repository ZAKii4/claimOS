import pytest

from app.services.document_service import DocumentService
from app.utils.exceptions import BusinessValidationError


def test_assert_correctable_path_accepts_known_scalar_path():
    DocumentService._assert_correctable_path("numero_police")  # does not raise
    DocumentService._assert_correctable_path("conducteur.nom")  # nested path


def test_assert_correctable_path_rejects_unknown_path():
    with pytest.raises(BusinessValidationError):
        DocumentService._assert_correctable_path("ce_champ_nexiste_pas")


def test_assert_correctable_path_rejects_list_index_paths():
    # victimes.<index>.<field> is not supported yet — see FormMappingEngine
    # get_field/set_field docstrings, which only resolve plain attributes.
    with pytest.raises(BusinessValidationError):
        DocumentService._assert_correctable_path("victimes.0.nom")
