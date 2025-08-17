#!/usr/bin/env python3
"""
Comprehensive Demo: Aadhaar and PAN Card Extraction with SQL Integration
Demonstrates both document extraction systems working together
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from aadhaar_extractor_with_sql import AadhaarExtractionTool
from pan_extractor_with_sql import PANExtractionTool
from agents.validator_agent import ValidatorAgent
from agents.pan_extractor_agent import PANExtractorAgent
import json
import sqlite3
from datetime import datetime

class DocumentProcessingDemo:
    """Demo class for processing both Aadhaar and PAN documents"""
    
    def __init__(self):
        self.aadhaar_extractor = AadhaarExtractionTool("aadhaar_documents.db")
        self.pan_extractor = PANExtractionTool("pan_documents.db")
        self.validator = ValidatorAgent()
        self.pan_agent = PANExtractorAgent()
    
    def demo_aadhaar_extraction(self, pdf_path: str = None):
        """Demo Aadhaar card extraction"""
        print("🔍 AADHAAR CARD EXTRACTION DEMO")
        print("=" * 60)
        
        if pdf_path and os.path.exists(pdf_path):
            print(f"📄 Processing Aadhaar PDF: {pdf_path}")
            result = self.aadhaar_extractor.extract_and_store(pdf_path)
            
            print("\n📊 EXTRACTION RESULTS:")
            print(json.dumps(result["extraction"], indent=2))
            
            if result["extraction"].get("status") == "success":
                extracted_data = result["extraction"].get("extracted_data", {})
                print("\n✅ EXTRACTED FIELDS:")
                for field, value in extracted_data.items():
                    print(f"  {field}: {value}")
                
                # Validate extracted data
                print("\n🔍 VALIDATION RESULTS:")
                validation_result = self.validator.validate(result["extraction"])
                print(json.dumps(validation_result, indent=2))
        else:
            print("⚠️  No Aadhaar PDF provided or file not found")
            print("Using sample data for demonstration...")
            
            # Sample Aadhaar data for demo
            sample_data = {
                "status": "success",
                "extracted_data": {
                    "Name": "John Doe",
                    "DOB": "15/03/1985",
                    "Gender": "Male",
                    "Address": "123 Main Street, City, State 123456",
                    "Aadhaar Number": "123456789012"
                }
            }
            
            print("\n📊 SAMPLE EXTRACTION RESULTS:")
            print(json.dumps(sample_data, indent=2))
            
            # Validate sample data
            print("\n🔍 VALIDATION RESULTS:")
            validation_result = self.validator.validate(sample_data)
            print(json.dumps(validation_result, indent=2))
    
    def demo_pan_extraction(self, pdf_path: str = None):
        """Demo PAN card extraction"""
        print("\n🔍 PAN CARD EXTRACTION DEMO")
        print("=" * 60)
        
        if pdf_path and os.path.exists(pdf_path):
            print(f"📄 Processing PAN PDF: {pdf_path}")
            result = self.pan_extractor.extract_and_store(pdf_path)
            
            print("\n📊 EXTRACTION RESULTS:")
            print(json.dumps(result["extraction"], indent=2))
            
            if result["extraction"].get("status") == "success":
                extracted_data = result["extraction"].get("extracted_data", {})
                print("\n✅ EXTRACTED FIELDS:")
                for field, value in extracted_data.items():
                    print(f"  {field}: {value}")
                
                # Validate extracted data
                print("\n🔍 VALIDATION RESULTS:")
                validation_result = self.validator.validate(result["extraction"])
                print(json.dumps(validation_result, indent=2))
        else:
            print("⚠️  No PAN PDF provided or file not found")
            print("Using sample data for demonstration...")
            
            # Sample PAN data for demo
            sample_text = """
            PERMANENT ACCOUNT NUMBER CARD
            
            Name: Jane Smith
            Father's Name: Robert Smith
            Date of Birth: 20/07/1990
            PAN: ABCDE1234F
            
            Government of India
            Income Tax Department
            """
            
            print("\n📄 SAMPLE PAN CARD TEXT:")
            print(sample_text)
            
            # Extract using PAN agent
            print("\n🔍 EXTRACTING FIELDS...")
            extraction_result = self.pan_agent.extract_pan_fields(sample_text)
            
            print("\n📊 EXTRACTION RESULTS:")
            print(json.dumps(extraction_result, indent=2))
            
            if extraction_result.get("status") == "success":
                extracted_data = extraction_result.get("extracted_data", {})
                print("\n✅ EXTRACTED FIELDS:")
                for field, value in extracted_data.items():
                    print(f"  {field}: {value}")
                
                # Validate PAN number
                pan_number = extracted_data.get("PAN Number")
                if pan_number:
                    print(f"\n🔍 VALIDATING PAN NUMBER: {pan_number}")
                    pan_validation = self.pan_agent.validate_pan_number(pan_number)
                    print(json.dumps(pan_validation, indent=2))
    
    def demo_database_operations(self):
        """Demo database operations for both document types"""
        print("\n🗄️  DATABASE OPERATIONS DEMO")
        print("=" * 60)
        
        # Show Aadhaar database contents
        print("\n📋 AADHAAR DATABASE CONTENTS:")
        aadhaar_data = self.aadhaar_extractor.get_all_extracted_data()
        if aadhaar_data.get("status") == "success":
            print(f"Total Aadhaar records: {aadhaar_data.get('total_records', 0)}")
            for record in aadhaar_data.get("data", [])[:3]:  # Show first 3 records
                print(f"  Document ID: {record['document_id']}")
                print(f"  File: {record['file_path']}")
                print(f"  Confidence: {record['extraction_confidence']}")
                print(f"  Extracted: {record['extracted_data']}")
                print()
        else:
            print(f"❌ Failed to retrieve Aadhaar data: {aadhaar_data.get('error_message')}")
        
        # Show PAN database contents
        print("\n📋 PAN DATABASE CONTENTS:")
        pan_data = self.pan_extractor.get_all_extracted_data()
        if pan_data.get("status") == "success":
            print(f"Total PAN records: {pan_data.get('total_records', 0)}")
            for record in pan_data.get("data", [])[:3]:  # Show first 3 records
                print(f"  Document ID: {record['document_id']}")
                print(f"  File: {record['file_path']}")
                print(f"  Confidence: {record['extraction_confidence']}")
                print(f"  Extracted: {record['extracted_data']}")
                print()
        else:
            print(f"❌ Failed to retrieve PAN data: {pan_data.get('error_message')}")
    
    def demo_validation_patterns(self):
        """Demo validation patterns for both document types"""
        print("\n🔍 VALIDATION PATTERNS DEMO")
        print("=" * 60)
        
        # Test Aadhaar validation patterns
        print("\n📋 AADHAAR VALIDATION PATTERNS:")
        aadhaar_tests = self.validator.test_invalid_patterns()
        aadhaar_results = aadhaar_tests.get("aadhaar_tests", {})
        
        for description, test_data in list(aadhaar_results.items())[:5]:  # Show first 5
            input_value = test_data["input"]
            is_invalid = test_data["is_invalid"]
            reason = test_data["validation_result"].get("reason", "unknown")
            status = "❌ INVALID" if is_invalid else "✅ VALID"
            print(f"{status} | {input_value:15} | {description} | Reason: {reason}")
        
        # Test PAN validation patterns
        print("\n📋 PAN VALIDATION PATTERNS:")
        pan_results = aadhaar_tests.get("pan_tests", {})
        
        for description, test_data in list(pan_results.items())[:5]:  # Show first 5
            input_value = test_data["input"]
            is_invalid = test_data["is_invalid"]
            reason = test_data["validation_result"].get("reason", "unknown")
            status = "❌ INVALID" if is_invalid else "✅ VALID"
            print(f"{status} | {input_value:15} | {description} | Reason: {reason}")
        
        # Show summary
        summary = aadhaar_tests.get("summary", {})
        print(f"\n📊 VALIDATION SUMMARY:")
        print(f"Aadhaar: {summary.get('total_aadhaar_tests', 0)} tests, {summary.get('invalid_aadhaar_count', 0)} invalid")
        print(f"PAN: {summary.get('total_pan_tests', 0)} tests, {summary.get('invalid_pan_count', 0)} invalid")
    
    def demo_combined_workflow(self):
        """Demo a combined workflow processing both document types"""
        print("\n🔄 COMBINED WORKFLOW DEMO")
        print("=" * 60)
        
        # Simulate processing multiple documents
        documents = [
            {"type": "aadhaar", "name": "John Doe", "number": "123456789012", "file": "aadhaar_sample.pdf"},
            {"type": "pan", "name": "Jane Smith", "number": "ABCDE1234F", "file": "pan_sample.pdf"},
            {"type": "aadhaar", "name": "Bob Johnson", "number": "987654321098", "file": "aadhaar_sample2.pdf"},
            {"type": "pan", "name": "Alice Brown", "number": "XYZAB5678C", "file": "pan_sample2.pdf"},
        ]
        
        print("📋 Processing Multiple Documents:")
        for i, doc in enumerate(documents, 1):
            print(f"\n{i}. {doc['type'].upper()} Document:")
            print(f"   Name: {doc['name']}")
            print(f"   Number: {doc['number']}")
            print(f"   File: {doc['file']}")
            
            # Simulate validation
            if doc['type'] == 'aadhaar':
                validation = self.validator.validate({
                    "status": "success",
                    "extracted_data": {
                        "Name": doc['name'],
                        "Aadhaar Number": doc['number']
                    }
                })
            else:  # PAN
                validation = self.validator.validate({
                    "status": "success",
                    "extracted_data": {
                        "Name": doc['name'],
                        "PAN Number": doc['number']
                    }
                })
            
            status = "✅ VALID" if validation.get("is_valid", False) else "❌ INVALID"
            print(f"   Status: {status}")
            print(f"   Confidence: {validation.get('overall_score', 0):.2%}")
    
    def run_full_demo(self, aadhaar_pdf: str = None, pan_pdf: str = None):
        """Run the complete demo"""
        print("🎯 COMPREHENSIVE DOCUMENT PROCESSING DEMO")
        print("=" * 80)
        print("This demo showcases both Aadhaar and PAN card extraction systems")
        print("with SQL database integration and comprehensive validation.")
        print("=" * 80)
        
        try:
            # Demo Aadhaar extraction
            self.demo_aadhaar_extraction(aadhaar_pdf)
            
            # Demo PAN extraction
            self.demo_pan_extraction(pan_pdf)
            
            # Demo database operations
            self.demo_database_operations()
            
            # Demo validation patterns
            self.demo_validation_patterns()
            
            # Demo combined workflow
            self.demo_combined_workflow()
            
            print("\n" + "=" * 80)
            print("🎉 DEMO COMPLETED SUCCESSFULLY!")
            print("=" * 80)
            print("\n📋 SUMMARY:")
            print("✅ Aadhaar card extraction with SQL integration")
            print("✅ PAN card extraction with SQL integration")
            print("✅ Comprehensive validation for both document types")
            print("✅ Database operations and data retrieval")
            print("✅ Pattern validation and error detection")
            print("✅ Combined workflow processing")
            
        except Exception as e:
            print(f"❌ Error during demo: {e}")
            import traceback
            traceback.print_exc()

def main():
    """Main function to run the demo"""
    demo = DocumentProcessingDemo()
    
    # You can provide actual PDF paths here
    aadhaar_pdf = "sample_documents/aadhar_sample 1.pdf"  # Update with your Aadhaar sample
    pan_pdf = "sample_documents/pan_sample.pdf"  # Update with your PAN sample
    
    # Run the full demo
    demo.run_full_demo(aadhaar_pdf, pan_pdf)

if __name__ == "__main__":
    main()



