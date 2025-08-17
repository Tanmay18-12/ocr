from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime

class DocumentState(BaseModel):
    """State for document processing workflow"""
    
    # Input
    file_path: str
    processing_timestamp: Optional[str] = None
    
    # Extraction results
    extraction_status: str = "pending"
    extraction_error: Optional[str] = None
    extracted_text: Optional[str] = None  # Raw extracted text for classification
    extracted_data: Dict[str, Any] = {}
    extraction_confidence: float = 0.0
    
    # Validation results
    validation_status: str = "pending"
    validation_error: Optional[str] = None
    validation_details: Dict[str, Any] = {}
    errors: List[str] = []
    warnings: List[str] = []
    overall_score: float = 0.0
    
    # Final results
    document_type: str = "UNKNOWN"
    final_status: str = "pending"
    
    # Metadata
    processing_log: List[str] = []
    
    def add_log(self, message: str):
        """Add a log message to the processing log"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.processing_log.append(f"[{timestamp}] {message}")
    
    def update_extraction_results(self, results: Dict[str, Any]):
        """Update extraction results in state"""
        self.extraction_status = results.get("status", "unknown")
        self.extracted_text = results.get("extracted_text", "")  # Store raw text
        self.extracted_data = results.get("extracted_data", {})
        self.extraction_confidence = results.get("extraction_confidence", 0.0)
        self.document_type = self.extracted_data.get("document_type", "UNKNOWN")
        
        if self.extraction_status == "error":
            self.extraction_error = results.get("error_message", "Unknown error")
    
    def update_validation_results(self, results: Dict[str, Any]):
        """Update validation results in state"""
        self.validation_status = results.get("validation_status", "unknown")
        self.validation_details = results.get("validation_details", {})
        self.errors = results.get("errors", [])
        self.warnings = results.get("warnings", [])
        self.overall_score = results.get("overall_score", 0.0)
        
        if self.validation_status == "error":
            self.validation_error = results.get("error_message", "Unknown error")
    
    def to_final_result(self) -> Dict[str, Any]:
        """Convert state to final result format"""
        return {
            "processing_timestamp": self.processing_timestamp or datetime.now().isoformat(),
            "file_path": self.file_path,
            "document_type": self.document_type,
            "validation_status": self.validation_status,
            "extraction_confidence": self.extraction_confidence,
            "overall_score": self.overall_score,
            "errors": self.errors,
            "warnings": self.warnings,
            "extracted_data": self.extracted_data,
            "validation_details": self.validation_details,
            "processing_log": self.processing_log
        } 