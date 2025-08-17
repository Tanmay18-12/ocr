from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from tools.pdf_extractor_tool import PDFExtractorTool
from typing import Dict, Any
from config import Config
import logging

class ExtractorAgent:
    """Agent responsible for document extraction and field identification"""
    
    def __init__(self):
        self.tool = PDFExtractorTool()
        self.llm = ChatOpenAI(
            model=Config.OPENAI_MODEL,
            temperature=0.1,
            api_key=Config.OPENAI_API_KEY
        )
        
        self.system_prompt = """You are an expert document processing specialist with years of experience 
        in extracting information from Indian government documents like PAN cards and Aadhaar cards. 
        You understand the various formats, orientations, and quality issues that can occur with scanned documents.
        
        Your role is to:
        1. Analyze extracted text from documents
        2. Identify document type (PAN or Aadhaar)
        3. Extract relevant fields accurately
        4. Provide confidence scores for extraction quality
        5. Handle various document formats and orientations
        
        For PAN cards, extract: PAN Number, Name, Father's Name, DOB (if available)
        For Aadhaar cards, extract: Aadhaar Number, Name, DOB, Gender, Address, Father's/Guardian's Name"""
    
    def run(self, pdf_path: str) -> Dict[str, Any]:
        """Extract fields from PDF document"""
        try:
            # Use the tool directly for extraction
            extracted_data = self.tool.extract_fields(pdf_path)
            
            # If extraction was successful, enhance with LLM analysis
            if extracted_data and "error" not in extracted_data:
                enhanced_data = self._enhance_extraction_with_llm(extracted_data, pdf_path)
                extracted_data.update(enhanced_data)
            
            # Add metadata
            extraction_result = {
                "status": "success",
                "file_path": pdf_path,
                "extracted_data": extracted_data,
                "extraction_confidence": self._calculate_confidence(extracted_data)
            }
            
            logging.info(f"Successfully extracted data from {pdf_path}")
            return extraction_result
            
        except Exception as e:
            error_result = {
                "status": "error",
                "file_path": pdf_path,
                "error_message": str(e),
                "extracted_data": {}
            }
            logging.error(f"Error extracting from {pdf_path}: {e}")
            return error_result
    
    def _enhance_extraction_with_llm(self, extracted_data: Dict[str, Any], pdf_path: str) -> Dict[str, Any]:
        """Enhance extraction results using LLM analysis"""
        try:
            prompt = f"""
            Analyze the following extracted document data and enhance it if needed:
            
            Document Path: {pdf_path}
            Document Type: {extracted_data.get('document_type', 'Unknown')}
            Extracted Data: {extracted_data}
            
            Please:
            1. Review the extracted fields for accuracy
            2. Suggest any missing fields that should be extracted
            3. Validate the document type detection
            4. Provide confidence scores for each field
            5. Identify any potential issues or inconsistencies
            
            Return your analysis as a JSON object with the following structure:
            {{
                "enhanced_fields": {{}},
                "missing_fields": [],
                "confidence_scores": {{}},
                "issues": [],
                "recommendations": []
            }}
            """
            
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            
            # Parse LLM response and enhance data
            enhanced_data = {}
            
            # Add any enhanced fields or corrections
            if "enhanced_fields" in response.content:
                # Parse and apply enhancements
                pass
            
            return enhanced_data
            
        except Exception as e:
            logging.warning(f"LLM enhancement failed: {e}")
            return {}
    
    def _calculate_confidence(self, extracted_data: Dict[str, Any]) -> float:
        """Calculate confidence score based on extracted fields"""
        if "error" in extracted_data:
            return 0.0
        
        doc_type = extracted_data.get("document_type", "UNKNOWN")
        
        if doc_type == "AADHAAR":
            required_fields = ["Aadhaar Number", "Name", "DOB"]
            optional_fields = ["Gender", "Address", "Father's/Guardian's Name"]
        elif doc_type == "PAN":
            required_fields = ["PAN Number", "Name"]
            optional_fields = ["Father's Name", "DOB"]
        else:
            return 0.3  # Low confidence for unknown document type
        
        # Calculate score
        required_score = sum(1 for field in required_fields if field in extracted_data and extracted_data[field]) / len(required_fields)
        optional_score = sum(1 for field in optional_fields if field in extracted_data and extracted_data[field]) / len(optional_fields)
        
        # Weight required fields more heavily
        confidence = (required_score * 0.7 + optional_score * 0.3)
        
        return round(confidence, 2)