#!/usr/bin/env python3
"""
Standalone demonstration of Document Classifier Agent
Shows how the classifier works with sample documents and routing logic
"""

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

def demonstrate_classification():
    """Demonstrate document classification with sample documents"""
    
    print("Document Classifier Agent Demonstration")
    print("=" * 60)
    print("This agent uses regex patterns to classify documents as Aadhaar, PAN, or UNKNOWN")
    print("No external APIs or LLMs are used - only local regex pattern matching")
    print()
    
    # Initialize classifier
    classifier = DocumentClassifierAgent()
    
    # Sample documents
    sample_documents = [
        {
            "name": "Sample Aadhaar Document",
            "text": """
            Government of India
            Unique Identification Authority of India
            Aadhaar Number: 1234 5678 9012
            Name: John Doe
            Date of Birth: 01/01/1990
            Address: 123 Main Street, City, State
            """
        },
        {
            "name": "Sample PAN Document", 
            "text": """
            Income Tax Department
            Government of India
            Permanent Account Number: ABCDE1234F
            Name: Jane Smith
            Date of Birth: 15/05/1985
            """
        },
        {
            "name": "Sample Unknown Document",
            "text": """
            Some random document
            This could be any type of document
            No specific identifiers found
            """
        },
        {
            "name": "Sample Mixed Document",
            "text": """
            This document contains both:
            Aadhaar Number: 9876 5432 1098
            PAN: XYZAB5678C
            This would be classified as UNKNOWN
            """
        }
    ]
    
    # Process each document
    for i, doc in enumerate(sample_documents, 1):
        print(f"Document {i}: {doc['name']}")
        print("-" * 40)
        print(f"Text: {doc['text'].strip()}")
        
        # Classify document
        result = classifier.classify_document(doc['text'])
        document_type = result['document_type']
        
        print(f"Classification: {document_type}")
        
        # Show routing decision
        if document_type == "AADHAAR":
            print("Routing: → aadhar_extractor_agent_with_sql")
        elif document_type == "PAN":
            print("Routing: → pan_extractor_agent_with_sql")
        else:
            print("Routing: → manual_review")
        
        print(f"Confidence: Aadhaar={result['confidence']['aadhaar_score']}, PAN={result['confidence']['pan_score']}")
        print()

def demonstrate_json_output():
    """Demonstrate the JSON output format"""
    
    print("JSON Output Format Demonstration")
    print("=" * 40)
    print("The classifier returns JSON in this format:")
    print('{"document_type": "<AADHAAR|PAN|UNKNOWN>"}')
    print()
    
    classifier = DocumentClassifierAgent()
    
    test_texts = [
        "Aadhaar Number: 1234 5678 9012\nGovernment of India",
        "PAN: ABCDE1234F\nPermanent Account Number",
        "Random text without identifiers"
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"Input {i}: {text}")
        json_result = classifier.process(text)
        print(f"Output: {json_result}")
        print()

def demonstrate_regex_patterns():
    """Demonstrate the regex patterns used"""
    
    print("Regex Patterns Used")
    print("=" * 30)
    print()
    
    print("Aadhaar Pattern:")
    print(r'\b\d{4}\s\d{4}\s\d{4}\b')
    print("Matches: 12-digit numbers in format 'XXXX XXXX XXXX'")
    print("Examples: 1234 5678 9012, 9876 5432 1098")
    print()
    
    print("PAN Pattern:")
    print(r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b')
    print("Matches: 10-character alphanumeric codes")
    print("Format: 5 uppercase letters + 4 digits + 1 uppercase letter")
    print("Examples: ABCDE1234F, XYZAB5678C")
    print()
    
    print("Additional Keywords:")
    print("Aadhaar: aadhaar, aadhar, government of india, unique identification, uidai, आधार, भारत सरकार")
    print("PAN: pan, permanent account number, income tax, tax department")
    print()

def demonstrate_workflow_integration():
    """Demonstrate how it integrates with LangGraph workflow"""
    
    print("LangGraph Workflow Integration")
    print("=" * 40)
    print()
    print("1. Document is extracted (OCR/PDF)")
    print("2. Raw text is passed to Document Classifier Agent")
    print("3. Agent uses regex patterns to classify document type")
    print("4. Based on classification, document is routed:")
    print("   - AADHAAR → aadhar_extractor_agent_with_sql")
    print("   - PAN → pan_extractor_agent_with_sql")
    print("   - UNKNOWN → manual_review")
    print("5. Appropriate agent processes the document")
    print()

if __name__ == "__main__":
    demonstrate_regex_patterns()
    demonstrate_classification()
    demonstrate_json_output()
    demonstrate_workflow_integration()
    
    print("=" * 60)
    print("Document Classifier Agent is ready for integration!")
    print("✅ No external APIs required")
    print("✅ Uses only regex pattern matching")
    print("✅ Returns standardized JSON output")
    print("✅ Integrates with LangGraph workflow")

