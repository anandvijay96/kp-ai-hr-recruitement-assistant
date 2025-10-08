import pytest
from pathlib import Path
import tempfile
import os
from unittest.mock import Mock, patch

from services.document_processor import DocumentProcessor
from models.schemas import ResumeAnalysis, AuthenticityScore, MatchingScore


class TestDocumentProcessor:
    """Test cases for document processing functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.processor = DocumentProcessor()
        self.test_dir = Path(__file__).parent / "test_files"

    def test_extract_text_from_pdf(self):
        """Test PDF text extraction"""
        # Create a mock PDF file for testing
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Test with non-existent file should handle gracefully
            result = self.processor.extract_text("nonexistent.pdf")
            assert "Error processing document" in result or "not available" in result
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

        """Test DOCX text extraction"""
        # Test with non-existent file
        result = self.processor.extract_text("nonexistent.docx")
        assert "Error processing document" in result or "not available" in result

    def test_ocr_fallback(self):
        """Test OCR fallback mechanism"""
        # This tests that OCR method exists and handles errors gracefully
        try:
            result = self.processor._extract_with_ocr("nonexistent.pdf")
            # Should return empty string or handle gracefully
            assert isinstance(result, str)
        except Exception as e:
            # OCR libraries might not be installed, which is okay
            assert "not available" in str(e).lower() or "not found" in str(e).lower()

    def test_extract_text_unsupported_format(self):
        """Test unsupported file format handling"""
        result = self.processor.extract_text("test.txt")
        assert "Unsupported file format" in result

    def test_analyze_document_structure_pdf(self):
        result = self.processor.analyze_document_structure("nonexistent.pdf")

        # Should return default structure even for non-existent files
        assert "font_analysis" in result
        assert "layout_analysis" in result
        assert "page_count" in result

    def test_analyze_document_structure_docx(self):
        """Test DOCX structure analysis"""
        result = self.processor.analyze_document_structure("nonexistent.docx")

        assert "font_analysis" in result
        assert "layout_analysis" in result
        assert "page_count" in result

    @patch('services.document_processor.fitz')
    def test_pdf_structure_analysis_with_fitz(self, mock_fitz):
        """Test PDF structure analysis when PyMuPDF is available"""
        # Mock fitz.open to return a mock document
        mock_doc = Mock()
        mock_page = Mock()
        mock_fitz.open.return_value = mock_doc
        mock_doc.page_count = 2
        mock_doc.load_page.return_value = mock_page
        mock_page.get_text.return_value = "Sample text"
        mock_page.get_text.return_value.__getitem__ = Mock(return_value={"blocks": []})

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            result = self.processor.analyze_document_structure(tmp_path)

            assert result["page_count"] == 2
            assert "font_analysis" in result
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    @patch('services.document_processor.Document')
    def test_docx_structure_analysis_with_docx(self, mock_document_class):
        """Test DOCX structure analysis when python-docx is available"""
        # Mock Document class
        mock_doc = Mock()
        mock_paragraph = Mock()
        mock_run = Mock()
        mock_font = Mock()

        mock_document_class.return_value = mock_doc
        mock_doc.paragraphs = [mock_paragraph]
        mock_paragraph.runs = [mock_run]
        mock_run.font.name = "Arial"

        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            result = self.processor.analyze_document_structure(tmp_path)

            assert result["page_count"] == 1
            assert "font_analysis" in result
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


class TestResumeAnalysis:
    """Test cases for resume analysis functionality"""

    def test_authenticity_score_creation(self):
        """Test AuthenticityScore model creation"""
        score = AuthenticityScore(
            overall_score=85.0,
            font_consistency=90.0,
            grammar_score=80.0,
            formatting_score=85.0,
            visual_consistency=85.0,
            details=["Document structure analysis completed"]
        )

        assert score.overall_score == 85.0
        assert score.font_consistency == 90.0
        assert len(score.details) == 1

    def test_matching_score_creation(self):
        """Test MatchingScore model creation"""
        score = MatchingScore(
            overall_match=75.0,
            skills_match=80.0,
            experience_match=70.0,
            education_match=75.0
        )

        assert score.overall_match == 75.0
        assert score.skills_match == 80.0

    def test_resume_analysis_creation(self):
        """Test ResumeAnalysis model creation"""
        analysis = ResumeAnalysis(
            id="test-123",
            filename="test_resume.pdf",
            file_size=1024,
            authenticity_score=AuthenticityScore(overall_score=85.0),
            matching_score=MatchingScore(overall_match=75.0)
        )

        assert analysis.id == "test-123"
        assert analysis.filename == "test_resume.pdf"
        assert analysis.authenticity_score.overall_score == 85.0


class TestIntegration:
    """Integration tests for the complete flow"""

    def test_full_resume_processing_pipeline(self):
        """Test the complete resume processing pipeline"""
        processor = DocumentProcessor()

        # Test with non-existent file (should handle gracefully)
        text = processor.extract_text("nonexistent.pdf")
        structure = processor.analyze_document_structure("nonexistent.pdf")

        # Should return fallback responses
        assert isinstance(text, str)
        assert isinstance(structure, dict)
        assert "font_analysis" in structure

    def test_error_handling_in_pipeline(self):
        """Test error handling throughout the pipeline"""
        processor = DocumentProcessor()

        # All operations should handle errors gracefully
        for filename in ["missing.pdf", "missing.docx", "missing.txt"]:
            text = processor.extract_text(filename)
            structure = processor.analyze_document_structure(filename)

            assert isinstance(text, str)
            assert isinstance(structure, dict)
