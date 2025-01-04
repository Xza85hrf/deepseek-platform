import pytest
import os
from unittest.mock import patch, MagicMock
from src.file_ops.operations import FileTextExtractor
from pypdf import PdfReader

TEST_DOCX_PATH = os.path.join(os.path.dirname(__file__), "test.docx")


@pytest.fixture
def text_extractor():
    return FileTextExtractor()


@pytest.mark.asyncio
async def test_extract_text_from_pdf_success(text_extractor):
    mock_pdf = MagicMock(spec=PdfReader)
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Sample PDF text"
    mock_pdf.pages = [mock_page]

    with patch("pypdf.PdfReader", return_value=mock_pdf):
        result = await text_extractor._extract_text_from_pdf("test.pdf")
        assert result == "Sample PDF text"


@pytest.mark.asyncio
async def test_extract_text_from_pdf_empty(text_extractor):
    mock_pdf = MagicMock(spec=PdfReader)
    mock_page = MagicMock()
    mock_page.extract_text.return_value = ""
    mock_pdf.pages = [mock_page]

    with patch("pypdf.PdfReader", return_value=mock_pdf):
        result = await text_extractor._extract_text_from_pdf("test.pdf")
        assert result == ""


@pytest.mark.asyncio
async def test_extract_text_from_pdf_error(text_extractor):
    with patch("pypdf.PdfReader", side_effect=Exception("PDF read error")):
        with pytest.raises(RuntimeError) as exc_info:
            await text_extractor._extract_text_from_pdf("test.pdf")
        assert "Failed to extract text from PDF" in str(exc_info.value)


    @pytest.mark.asyncio
    async def test_extract_text_from_docx_success(text_extractor):
        mock_doc = MagicMock()
        mock_paragraph = MagicMock()
        mock_paragraph.text = "Sample DOCX text"
        mock_doc.paragraphs = [mock_paragraph]

        with patch("docx.Document", return_value=mock_doc, autospec=True) as mock_document:
            result = await text_extractor._extract_text_from_docx("test.docx")
            assert result == "Sample DOCX text"
            mock_document.assert_called_once_with("test.docx")

    @pytest.mark.asyncio
    async def test_extract_text_from_docx_empty(text_extractor):
        mock_doc = MagicMock()
        mock_paragraph = MagicMock()
        mock_paragraph.text = ""
        mock_doc.paragraphs = [mock_paragraph]

        with patch("docx.Document", return_value=mock_doc) as mock_document:
            result = await text_extractor._extract_text_from_docx("test.docx")
            assert result == ""
            mock_document.assert_called_once_with("test.docx")

    @pytest.mark.asyncio
    async def test_extract_text_from_docx_error(text_extractor):
        with patch(
            "docx.Document", side_effect=Exception("DOCX read error")
        ) as mock_document:
            with pytest.raises(RuntimeError) as exc_info:
                await text_extractor._extract_text_from_docx("test.docx")
            assert str(exc_info.value) == "Failed to extract text from DOCX file"
            mock_document.assert_called_once_with("test.docx")
