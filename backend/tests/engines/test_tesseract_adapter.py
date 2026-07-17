"""
Regression tests for real, bilingual Tesseract OCR.

Prior to this, the adapter never passed a `lang` argument to pytesseract,
so it silently ran English-only (Tesseract's default) even though French
and Arabic traineddata are installed locally and this product's documents
are French (with Arabic on national ID/official documents).
"""

from unittest.mock import patch

import cv2
import numpy as np
import pytest
from PIL import Image, ImageDraw, ImageFont

from app.config.settings import get_settings
from app.engines.ocr.adapters.tesseract_adapter import TesseractAdapter

pytestmark = pytest.mark.skipif(
    not TesseractAdapter().is_available(), reason="Tesseract binary not installed locally"
)


def _render_text_image(text: str) -> np.ndarray:
    img = Image.new("RGB", (900, 120), color="white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 32)
    except OSError:
        font = ImageFont.load_default()
    draw.text((20, 30), text, fill="black", font=font)
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def test_adapter_passes_configured_languages_to_pytesseract():
    adapter = TesseractAdapter()
    image = _render_text_image("Nom du souscripteur: MARTIN")

    with patch("app.engines.ocr.adapters.tesseract_adapter.pytesseract.image_to_data") as mocked:
        mocked.return_value = {
            "level": [], "text": [], "conf": [], "left": [], "top": [],
            "width": [], "height": [], "block_num": [], "line_num": [],
        }
        adapter.process(image)

    assert mocked.call_args.kwargs["lang"] == get_settings().OCR_LANGUAGES


def test_adapter_recognizes_real_french_text():
    adapter = TesseractAdapter()
    image = _render_text_image("Nom du souscripteur: MARTIN")

    page = adapter.process(image)

    assert page.language == get_settings().OCR_LANGUAGES
    full_text = " ".join(
        w.text for block in page.blocks for line in block.lines for w in line.words
    )
    assert "MARTIN" in full_text
    assert "souscripteur" in full_text.lower()
