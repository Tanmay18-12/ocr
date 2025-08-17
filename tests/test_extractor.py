import unittest
import os
import tempfile
from unittest.mock import patch, MagicMock
from tools.pdf_extractor_tool import PDFExtractorTool
from agents.extractor_agent import ExtractorAgent

class TestPDFExtractorTool(unittest.TestCase):
    def setUp(self):
        self.extractor = PDFExtractorTool()
    
    def test_detect_document_type_aadhaar(self):
        """Test Aadhaar document type detection"""
        aadhaar_text = "GOVERNMENT OF INDIA AADHAAR 1234 5678 9012"
        doc_type = self.extractor._detect_document_type(aadhaar_text)
        self.assertEqual(doc_type, 'AADHAAR')
    
    def test_detect_document_type_pan(self):
        """Test PAN document type detection"""
        pan_text = "INCOME TAX DEPARTMENT PERMANENT ACCOUNT NUMBER ABCDE1234F"
        doc_type = self.extractor._detect_document_type(pan_text)
        self.assertEqual(doc_type, 'PAN')
    
    def test_extract_aadhaar_fields(self):
        """Test Aadhaar field extraction"""
        text = """
        GOVERNMENT OF INDIA
        Name: JOHN DOE
        DOB: 15/08/1990
        Gender: Male
        Aadhaar: 1234 5678 9012
        """
        fields = self.extractor._extract_aadhaar_fields(text)
        
        self.assertIn('Name', fields)
        self.assertIn('DOB', fields)
        self.assertIn('Gender', fields)
        self.assertIn('Aadhaar Number', fields)
        self.assertEqual(fields['Name'], 'JOHN DOE')
        self.assertEqual(fields['DOB'], '15/08/1990')
        self.assertEqual(fields['Gender'], 'Male')
    
    def test_extract_pan_fields(self):
        """Test PAN field extraction"""
        text = """
        INCOME TAX DEPARTMENT
        Name: JANE SMITH
        Father's Name: ROBERT SMITH
        PAN: ABCDE1234F
        """
        fields = self.extractor._extract_pan_fields(text)
        
        self.assertIn('Name', fields)
        self.assertIn('Father\'s Name', fields)
        self.assertIn('PAN Number', fields)
        self.assertEqual(fields['PAN Number'], 'ABCDE1234F')

class TestExtractorAgent(unittest.TestCase):
    def setUp(self):
        self.agent = ExtractorAgent()
    
    def test_calculate_confidence(self):
        """Test confidence calculation"""
        # Test Aadhaar confidence
        aadhaar_data = {
            'document_type': 'AADHAAR',
            'Aadhaar Number': '123456789012',
            'Name': 'John Doe',
            'DOB': '15/08/1990',
            'Gender': 'Male'
        }
        confidence = self.agent._calculate_confidence(aadhaar_data)
        self.assertGreater(confidence, 0.5)
        
        # Test PAN confidence
        pan_data = {
            'document_type': 'PAN',
            'PAN Number': 'ABCDE1234F',
            'Name': 'Jane Smith'
        }
        confidence = self.agent._calculate_confidence(pan_data)
        self.assertGreater(confidence, 0.5)
