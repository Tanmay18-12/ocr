import pytest
import tempfile
import os
from unittest.mock import Mock, patch
from graph.state import DocumentState
from graph.workflow import process_document_with_graph
from agents.extractor_agent import ExtractorAgent
from agents.validator_agent import ValidatorAgent

class TestDocumentState:
    """Test the DocumentState class"""
    
    def test_state_initialization(self):
        """Test state initialization"""
        state = DocumentState(file_path="test.pdf")
        
        assert state.file_path == "test.pdf"
        assert state.extraction_status == "pending"
        assert state.validation_status == "pending"
        assert state.document_type == "UNKNOWN"
        assert len(state.processing_log) == 0
    
    def test_add_log(self):
        """Test adding log entries"""
        state = DocumentState(file_path="test.pdf")
        state.add_log("Test log entry")
        
        assert len(state.processing_log) == 1
        assert "Test log entry" in state.processing_log[0]
    
    def test_update_extraction_results(self):
        """Test updating extraction results"""
        state = DocumentState(file_path="test.pdf")
        
        extraction_result = {
            "status": "success",
            "extracted_data": {
                "document_type": "AADHAAR",
                "Aadhaar Number": "123456789012"
            },
            "extraction_confidence": 0.85
        }
        
        state.update_extraction_results(extraction_result)
        
        assert state.extraction_status == "success"
        assert state.document_type == "AADHAAR"
        assert state.extraction_confidence == 0.85
        assert state.extracted_data["Aadhaar Number"] == "123456789012"
    
    def test_update_validation_results(self):
        """Test updating validation results"""
        state = DocumentState(file_path="test.pdf")
        
        validation_result = {
            "validation_status": "passed",
            "errors": [],
            "warnings": ["Minor issue"],
            "overall_score": 0.92,
            "validation_details": {
                "Aadhaar Number": {"valid": True}
            }
        }
        
        state.update_validation_results(validation_result)
        
        assert state.validation_status == "passed"
        assert state.overall_score == 0.92
        assert len(state.errors) == 0
        assert len(state.warnings) == 1
        assert state.warnings[0] == "Minor issue"
    
    def test_to_final_result(self):
        """Test converting state to final result"""
        state = DocumentState(file_path="test.pdf")
        state.processing_timestamp = "2024-01-01T12:00:00"
        
        final_result = state.to_final_result()
        
        assert final_result["file_path"] == "test.pdf"
        assert final_result["processing_timestamp"] == "2024-01-01T12:00:00"
        assert final_result["document_type"] == "UNKNOWN"
        assert final_result["validation_status"] == "pending"

class TestExtractorAgent:
    """Test the ExtractorAgent class"""
    
    @patch('agents.extractor_agent.ChatOpenAI')
    def test_agent_initialization(self, mock_chat_openai):
        """Test agent initialization"""
        agent = ExtractorAgent()
        
        assert agent.tool is not None
        assert agent.llm is not None
        assert "document processing specialist" in agent.system_prompt
    
    def test_calculate_confidence(self):
        """Test confidence calculation"""
        agent = ExtractorAgent()
        
        # Test AADHAAR confidence
        aadhaar_data = {
            "document_type": "AADHAAR",
            "Aadhaar Number": "123456789012",
            "Name": "John Doe",
            "DOB": "01/01/1990"
        }
        
        confidence = agent._calculate_confidence(aadhaar_data)
        assert 0.0 <= confidence <= 1.0
        
        # Test PAN confidence
        pan_data = {
            "document_type": "PAN",
            "PAN Number": "ABCDE1234F",
            "Name": "John Doe"
        }
        
        confidence = agent._calculate_confidence(pan_data)
        assert 0.0 <= confidence <= 1.0

class TestValidatorAgent:
    """Test the ValidatorAgent class"""
    
    @patch('agents.validator_agent.ChatOpenAI')
    def test_agent_initialization(self, mock_chat_openai):
        """Test agent initialization"""
        agent = ValidatorAgent()
        
        assert agent.llm is not None
        assert "document verification specialist" in agent.system_prompt
    
    def test_validate_aadhaar(self):
        """Test Aadhaar validation"""
        agent = ValidatorAgent()
        
        extraction_result = {
            "status": "success",
            "extracted_data": {
                "document_type": "AADHAAR",
                "Aadhaar Number": "123456789012",
                "Name": "John Doe",
                "DOB": "01/01/1990"
            }
        }
        
        result = agent.validate(extraction_result)
        
        assert "validation_status" in result
        assert "validation_details" in result
        assert "errors" in result
        assert "warnings" in result
    
    def test_validate_pan(self):
        """Test PAN validation"""
        agent = ValidatorAgent()
        
        extraction_result = {
            "status": "success",
            "extracted_data": {
                "document_type": "PAN",
                "PAN Number": "ABCDE1234F",
                "Name": "John Doe"
            }
        }
        
        result = agent.validate(extraction_result)
        
        assert "validation_status" in result
        assert "validation_details" in result
        assert "errors" in result
        assert "warnings" in result
    
    def test_validate_date(self):
        """Test date validation"""
        agent = ValidatorAgent()
        
        # Valid dates
        assert agent._validate_date("01/01/1990")["valid"] == True
        assert agent._validate_date("01-01-1990")["valid"] == True
        
        # Invalid dates
        assert agent._validate_date("invalid")["valid"] == False
        assert agent._validate_date("")["valid"] == False

class TestWorkflow:
    """Test the LangGraph workflow"""
    
    @patch('graph.workflow.create_document_processing_graph')
    def test_process_document_with_graph(self, mock_create_graph):
        """Test document processing with graph"""
        # Mock the graph
        mock_app = Mock()
        mock_app.invoke.return_value = DocumentState(
            file_path="test.pdf",
            extraction_status="success",
            validation_status="passed",
            document_type="AADHAAR",
            extraction_confidence=0.85,
            overall_score=0.92
        )
        mock_create_graph.return_value = mock_app
        
        # Test processing
        result = process_document_with_graph("test.pdf")
        
        assert result["file_path"] == "test.pdf"
        assert result["document_type"] == "AADHAAR"
        assert result["validation_status"] == "passed"
        assert result["extraction_confidence"] == 0.85
        assert result["overall_score"] == 0.92

if __name__ == "__main__":
    pytest.main([__file__]) 