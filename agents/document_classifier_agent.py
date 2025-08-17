import re
import json
from typing import Dict, Any


class DocumentClassifierAgent:
    """
    Document Classifier Agent that determines whether extracted text is from an Aadhaar card or PAN card.
    Uses regex pattern matching only - no external APIs or LLMs.
    """
    
    def __init__(self):
        # Aadhaar pattern: 12-digit number in format "XXXX XXXX XXXX"
        self.aadhaar_pattern = r'\b\d{4}\s\d{4}\s\d{4}\b'
        
        # PAN pattern: 10-character alphanumeric code (5 letters + 4 digits + 1 letter)
        self.pan_pattern = r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b'
        
        # Additional Aadhaar keywords for better detection
        self.aadhaar_keywords = [
            'aadhaar', 'aadhar', 'government of india', 'unique identification',
            'uidai', 'unique id', 'आधार', 'भारत सरकार'
        ]
        
        # Additional PAN keywords for better detection
        self.pan_keywords = [
            'pan', 'permanent account number', 'income tax', 'tax department',
            'permanent account', 'account number'
        ]
    
    def classify_document(self, extracted_text: str) -> Dict[str, Any]:
        """
        Classify the document type based on regex patterns.
        
        Args:
            extracted_text (str): Text extracted from OCR/PDF tool
            
        Returns:
            Dict containing the classification result
        """
        if not extracted_text or not isinstance(extracted_text, str):
            return {"document_type": "UNKNOWN"}
        
        # Normalize text for better matching
        normalized_text = extracted_text.lower().strip()
        
        # Check for Aadhaar patterns
        aadhaar_matches = re.findall(self.aadhaar_pattern, extracted_text)
        aadhaar_keyword_matches = any(keyword in normalized_text for keyword in self.aadhaar_keywords)
        
        # Check for PAN patterns
        pan_matches = re.findall(self.pan_pattern, extracted_text)
        pan_keyword_matches = any(keyword in normalized_text for keyword in self.pan_keywords)
        
        # Classification logic - prioritize exact pattern matches over keywords
        aadhaar_score = len(aadhaar_matches) * 2 + (1 if aadhaar_keyword_matches else 0)
        pan_score = len(pan_matches) * 2 + (1 if pan_keyword_matches else 0)
        
        # Decision logic - require at least one exact pattern match for classification
        if len(aadhaar_matches) > 0 and len(pan_matches) == 0:
            document_type = "AADHAAR"
        elif len(pan_matches) > 0 and len(aadhaar_matches) == 0:
            document_type = "PAN"
        elif len(aadhaar_matches) > 0 and len(pan_matches) > 0:
            # If both have exact matches, prefer the one with more matches
            if len(aadhaar_matches) > len(pan_matches):
                document_type = "AADHAAR"
            elif len(pan_matches) > len(aadhaar_matches):
                document_type = "PAN"
            else:
                document_type = "UNKNOWN"
        else:
            document_type = "UNKNOWN"
        
        return {
            "document_type": document_type,
            "confidence": {
                "aadhaar_score": aadhaar_score,
                "pan_score": pan_score,
                "aadhaar_matches": aadhaar_matches,
                "pan_matches": pan_matches
            }
        }
    
    def process(self, extracted_text: str) -> str:
        """
        Process the extracted text and return JSON result.
        
        Args:
            extracted_text (str): Text extracted from OCR/PDF tool
            
        Returns:
            JSON string with document type classification
        """
        result = self.classify_document(extracted_text)
        
        # Return only the document_type as specified in requirements
        return json.dumps({
            "document_type": result["document_type"]
        }, indent=2)


# Function for LangGraph integration
def classify_document(extracted_text: str) -> str:
    """
    Function to classify document type for LangGraph workflow.
    
    Args:
        extracted_text (str): Text extracted from OCR/PDF tool
        
    Returns:
        JSON string with document type classification
    """
    classifier = DocumentClassifierAgent()
    return classifier.process(extracted_text)


if __name__ == "__main__":
    # Test the classifier
    classifier = DocumentClassifierAgent()
    
    # Test cases
    test_cases = [
        # Aadhaar test cases
        "Aadhaar Number: 1234 5678 9012\nGovernment of India",
        "आधार संख्या: 9876 5432 1098\nभारत सरकार",
        "UID: 1111 2222 3333\nUnique Identification Authority of India",
        
        # PAN test cases
        "PAN: ABCDE1234F\nPermanent Account Number",
        "Income Tax Department\nPAN: XYZAB5678C",
        "Permanent Account Number: MNOPQ9012R",
        
        # Mixed/Unknown test cases
        "This is just some random text",
        "Aadhaar: 1234 5678 9012\nPAN: ABCDE1234F",  # Both present
        "",
        None
    ]
    
    print("Testing Document Classifier Agent:")
    print("=" * 50)
    
    for i, test_text in enumerate(test_cases, 1):
        if test_text is None:
            test_text = ""
        result = classifier.classify_document(test_text)
        print(f"Test {i}:")
        print(f"Input: {test_text[:50]}{'...' if len(str(test_text)) > 50 else ''}")
        print(f"Result: {result['document_type']}")
        print(f"Confidence: Aadhaar={result['confidence']['aadhaar_score']}, PAN={result['confidence']['pan_score']}")
        print("-" * 30)
