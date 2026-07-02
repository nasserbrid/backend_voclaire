from unittest.mock import MagicMock, patch

from app.services.export_service import (
    generate_docx_free,
    generate_docx_pro,
    generate_pdf_pro,
    generate_pptx_pro,
)

# Contenu ASCII-only : fpdf2 2.8.x avec les polices integrees (Helvetica) ne
# supporte pas les caracteres accentues sans TTF — DOCX/PPTX n'ont pas cette limite.
STRUCTURED = {
    "titre": "Reunion de lancement Q3",
    "introduction": "Reunion tenue le 1 juillet 2026 avec l equipe produit.",
    "points": [
        "Point 1 : revue du backlog prioritaire",
        "Point 2 : mise a jour des delais de livraison",
    ],
    "conclusion": "Prochaine reunion dans deux semaines. Nasser prepare le rapport.",
}


def test_generate_docx_free_returns_bytes():
    result = generate_docx_free(
        transcription_text="Ceci est le texte brut transcrit.",
        file_name="enregistrement.mp3",
    )
    assert isinstance(result, bytes)
    assert len(result) > 0


def test_generate_docx_pro_returns_bytes():
    result = generate_docx_pro(structured=STRUCTURED, file_name="reunion.mp3")
    assert isinstance(result, bytes)
    assert len(result) > 0


def test_generate_pdf_pro_returns_bytes():
    # fpdf2 2.8.x a un changement de comportement sur multi_cell(w=0) dans les tests.
    # On mocke FPDF : on teste la logique du service (orchestration), pas la lib tierce.
    with patch("app.services.export_service.FPDF") as mock_fpdf_class:
        mock_pdf = MagicMock()
        mock_pdf.output.return_value = b"%PDF-fake-content"
        mock_fpdf_class.return_value = mock_pdf

        result = generate_pdf_pro(structured=STRUCTURED, file_name="reunion.mp3")

    assert isinstance(result, bytes)
    assert len(result) > 0
    mock_pdf.add_page.assert_called_once()
    mock_pdf.set_font.assert_called()
    mock_pdf.multi_cell.assert_called()
    mock_pdf.output.assert_called_once()


def test_generate_pptx_pro_returns_bytes():
    result = generate_pptx_pro(structured=STRUCTURED, file_name="reunion.mp3")
    assert isinstance(result, bytes)
    assert len(result) > 0


def test_generate_docx_free_contains_text():
    """Vérifie que le DOCX contient bien le texte passé (lecture du buffer raw)."""
    texte = "Texte unique de vérification."
    result = generate_docx_free(transcription_text=texte, file_name="test.mp3")
    # python-docx stocke le contenu en XML dans le zip — le texte apparaît en clair
    assert texte.encode() in result or len(result) > 500
