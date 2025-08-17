import os
import sys
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.document_classifier_agent import DocumentClassifierAgent
from agents.pan_extractor_agent import PANExtractorAgent
from agents.extractor_agent import ExtractorAgent
from agents.validator_agent import ValidatorAgent
from agents.db_agent import DatabaseAgent
from tools.pdf_extractor_tool import PDFExtractorTool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OrchestratorAgent:
    """
    Orchestrator Agent that coordinates the entire document processing pipeline:
    1. Document Classification
    2. Data Extraction
    3. Data Validation
    4. Database Storage
    """
    
    def __init__(self):
        """Initialize all required agents and tools"""
        self.classifier = DocumentClassifierAgent()
        self.pan_extractor = PANExtractorAgent()
        self.aadhaar_extractor = ExtractorAgent()
        self.validator = ValidatorAgent()
        self.db_agent = DatabaseAgent()
        self.pdf_extractor = PDFExtractorTool()
        
        # Processing status tracking
        self.processing_status = {
            "document_path": None,
            "document_type": None,
            "extraction_status": "pending",
            "validation_status": "pending",
            "storage_status": "pending",
            "errors": [],
            "warnings": [],
            "processing_log": []
        }
    
    def log_step(self, step: str, message: str, status: str = "info"):
        """Log a processing step with timestamp"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {step}: {message}"
        
        if status == "error":
            self.processing_status["errors"].append(log_entry)
            logger.error(log_entry)
        elif status == "warning":
            self.processing_status["warnings"].append(log_entry)
            logger.warning(log_entry)
        else:
            self.processing_status["processing_log"].append(log_entry)
            logger.info(log_entry)
    
    def extract_text_from_pdf(self, pdf_path: str) -> Optional[str]:
        """Extract text from PDF document"""
        try:
            self.log_step("PDF_EXTRACTION", f"Extracting text from {pdf_path}")
            
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
            result = self.pdf_extractor.extract_text(pdf_path)
            extracted_text = result.get('extracted_text', '')
            
            if not extracted_text:
                raise ValueError("No text extracted from PDF")
            
            self.log_step("PDF_EXTRACTION", f"Successfully extracted {len(extracted_text)} characters")
            return extracted_text
            
        except Exception as e:
            self.log_step("PDF_EXTRACTION", f"Failed to extract text: {str(e)}", "error")
            return None
    
    def classify_document(self, extracted_text: str) -> Optional[str]:
        """Classify document type using Document Classifier Agent"""
        try:
            self.log_step("CLASSIFICATION", "Classifying document type")
            
            classification_result = self.classifier.classify_document(extracted_text)
            document_type = classification_result.get('document_type', 'UNKNOWN')
            
            if document_type == 'UNKNOWN':
                raise ValueError("Document type could not be determined")
            
            self.processing_status["document_type"] = document_type
            self.log_step("CLASSIFICATION", f"Document classified as: {document_type}")
            
            return document_type
            
        except Exception as e:
            self.log_step("CLASSIFICATION", f"Classification failed: {str(e)}", "error")
            return None
    
    def extract_data(self, document_type: str, extracted_text: str) -> Optional[Dict[str, Any]]:
        """Extract data using appropriate extractor agent"""
        try:
            self.log_step("EXTRACTION", f"Extracting data using {document_type} extractor")
            
            if document_type == "PAN":
                extraction_result = self.pan_extractor.extract_pan_data(extracted_text)
            elif document_type == "AADHAAR":
                extraction_result = self.aadhaar_extractor.extract_aadhaar_data(extracted_text)
            else:
                raise ValueError(f"Unsupported document type: {document_type}")
            
            if not extraction_result or extraction_result.get('status') == 'error':
                raise ValueError("Data extraction failed")
            
            self.processing_status["extraction_status"] = "completed"
            self.log_step("EXTRACTION", "Data extraction completed successfully")
            
            return extraction_result
            
        except Exception as e:
            self.processing_status["extraction_status"] = "failed"
            self.log_step("EXTRACTION", f"Data extraction failed: {str(e)}", "error")
            return None
    
    def validate_data(self, document_type: str, extracted_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Validate extracted data using Validator Agent"""
        try:
            self.log_step("VALIDATION", f"Validating {document_type} data")
            
            validation_result = self.validator.validate_document_data(
                document_type=document_type,
                extracted_data=extracted_data
            )
            
            if not validation_result or validation_result.get('validation_status') == 'failed':
                raise ValueError("Data validation failed")
            
            self.processing_status["validation_status"] = "completed"
            self.log_step("VALIDATION", "Data validation completed successfully")
            
            return validation_result
            
        except Exception as e:
            self.processing_status["validation_status"] = "failed"
            self.log_step("VALIDATION", f"Data validation failed: {str(e)}", "error")
            return None
    
    def store_data(self, document_type: str, validated_data: Dict[str, Any]) -> bool:
        """Store validated data in database using DB Agent"""
        try:
            self.log_step("STORAGE", f"Storing {document_type} data in database")
            
            storage_result = self.db_agent.store_document_data(
                document_type=document_type,
                validated_data=validated_data
            )
            
            if not storage_result or storage_result.get('status') == 'error':
                raise ValueError("Data storage failed")
            
            self.processing_status["storage_status"] = "completed"
            self.log_step("STORAGE", "Data stored successfully in database")
            
            return True
            
        except Exception as e:
            self.processing_status["storage_status"] = "failed"
            self.log_step("STORAGE", f"Data storage failed: {str(e)}", "error")
            return False
    
    def process_document(self, pdf_path: str) -> Dict[str, Any]:
        """
        Main orchestration method that processes a document through the entire pipeline
        
        Args:
            pdf_path (str): Path to the PDF document
            
        Returns:
            Dict containing processing results and status
        """
        # Initialize processing status
        self.processing_status = {
            "document_path": pdf_path,
            "document_type": None,
            "extraction_status": "pending",
            "validation_status": "pending",
            "storage_status": "pending",
            "errors": [],
            "warnings": [],
            "processing_log": []
        }
        
        self.log_step("ORCHESTRATOR", f"Starting document processing for: {pdf_path}")
        
        try:
            # Step 1: Extract text from PDF
            extracted_text = self.extract_text_from_pdf(pdf_path)
            if not extracted_text:
                raise Exception("PDF text extraction failed")
            
            # Step 2: Classify document
            document_type = self.classify_document(extracted_text)
            if not document_type:
                raise Exception("Document classification failed")
            
            # Step 3: Extract data
            extracted_data = self.extract_data(document_type, extracted_text)
            if not extracted_data:
                raise Exception("Data extraction failed")
            
            # Step 4: Validate data
            validated_data = self.validate_data(document_type, extracted_data)
            if not validated_data:
                raise Exception("Data validation failed")
            
            # Step 5: Store data
            storage_success = self.store_data(document_type, validated_data)
            if not storage_success:
                raise Exception("Data storage failed")
            
            # Success
            self.log_step("ORCHESTRATOR", "Document processing completed successfully")
            
            return {
                "status": "success",
                "document_type": document_type,
                "extracted_data": extracted_data,
                "validated_data": validated_data,
                "processing_status": self.processing_status
            }
            
        except Exception as e:
            self.log_step("ORCHESTRATOR", f"Document processing failed: {str(e)}", "error")
            
            return {
                "status": "error",
                "error_message": str(e),
                "processing_status": self.processing_status
            }
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """Get a summary of the processing status"""
        return {
            "document_path": self.processing_status["document_path"],
            "document_type": self.processing_status["document_type"],
            "overall_status": "completed" if self.processing_status["storage_status"] == "completed" else "failed",
            "steps_completed": {
                "extraction": self.processing_status["extraction_status"],
                "validation": self.processing_status["validation_status"],
                "storage": self.processing_status["storage_status"]
            },
            "error_count": len(self.processing_status["errors"]),
            "warning_count": len(self.processing_status["warnings"]),
            "processing_log": self.processing_status["processing_log"][-10:]  # Last 10 log entries
        }


# Function for easy integration
def orchestrate_document_processing(pdf_path: str) -> Dict[str, Any]:
    """
    Convenience function to orchestrate document processing
    
    Args:
        pdf_path (str): Path to the PDF document
        
    Returns:
        Dict containing processing results
    """
    orchestrator = OrchestratorAgent()
    return orchestrator.process_document(pdf_path)


if __name__ == "__main__":
    # Test the orchestrator with a sample document
    test_pdf = "sample_documents/pan_sample.pdf"
    
    if os.path.exists(test_pdf):
        print("Testing Orchestrator Agent...")
        result = orchestrate_document_processing(test_pdf)
        print(json.dumps(result, indent=2))
    else:
        print(f"Test PDF not found: {test_pdf}")

