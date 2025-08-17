#!/usr/bin/env python3
"""
Production-ready PAN & Aadhaar Document Extraction System with Validation
Multi-agent system using OCR and AI for document processing with validation
"""

import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from tools.pdf_extractor_tool import PDFExtractorTool
from agents.validator_agent import ValidatorAgent, FieldValidator
from utils.logging_config import setup_logging

class DocumentProcessorWithValidation:
    """Main document processing orchestrator with validation"""
    
    def __init__(self):
        self.logger = setup_logging()
        self.extractor = PDFExtractorTool()
        self.validator = ValidatorAgent()
    
    def process_document_with_validation(self, pdf_path: str) -> Dict[str, Any]:
        """Process a single document with validation and return comprehensive result"""
        if not os.path.exists(pdf_path):
            return self._create_error_result(pdf_path, "File not found")
        
        try:
            # Step 1: Extract data
            self.logger.info(f"Extracting data from {pdf_path}")
            extracted_data = self.extractor.extract_fields(pdf_path)
            
            # Step 2: Validate extracted data
            self.logger.info(f"Validating extracted data from {pdf_path}")
            validation_result = self.validator.validate(extracted_data)
            
            # Step 3: Create comprehensive result
            return self._create_comprehensive_result(pdf_path, extracted_data, validation_result)
            
        except Exception as e:
            self.logger.error(f"Processing error for {pdf_path}: {e}")
            return self._create_error_result(pdf_path, str(e))
    
    def process_batch_with_validation(self, directory_path: str) -> List[Dict[str, Any]]:
        """Process all PDF files in directory with validation"""
        if not os.path.exists(directory_path):
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        pdf_files = list(Path(directory_path).glob("**/*.pdf"))
        if not pdf_files:
            self.logger.warning(f"No PDF files found in {directory_path}")
            return []
        
        results = []
        for pdf_file in pdf_files:
            result = self.process_document_with_validation(str(pdf_file))
            results.append(result)
            self.logger.info(f"Processed {pdf_file}: {result['status']}")
        
        return results
    
    def _create_comprehensive_result(self, file_path: str, extracted_data: Dict[str, Any], 
                                   validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive result with extraction and validation"""
        has_extraction_error = "error" in extracted_data
        extraction_status = "failed" if has_extraction_error else "success"
        
        # Combine extraction and validation results
        result = {
            "timestamp": datetime.now().isoformat(),
            "file_path": file_path,
            "status": extraction_status,
            "document_type": extracted_data.get("document_type", "UNKNOWN"),
            "extraction": {
                "confidence": extracted_data.get("extraction_confidence", 0.0),
                "errors": [extracted_data.get("error")] if has_extraction_error else [],
                "warnings": extracted_data.get("warnings", []),
                "extracted_fields": extracted_data.get("extracted_data", {})
            },
            "validation": {
                "status": validation_result.get("validation_status", "unknown"),
                "is_valid": validation_result.get("is_valid", False),
                "overall_score": validation_result.get("overall_score", 0.0),
                "errors": validation_result.get("errors", []),
                "warnings": validation_result.get("warnings", []),
                "field_validations": validation_result.get("validation_details", {})
            }
        }
        
        return result
    
    def _create_error_result(self, file_path: str, error_msg: str) -> Dict[str, Any]:
        """Create standardized error result"""
        return {
            "timestamp": datetime.now().isoformat(),
            "file_path": file_path,
            "status": "error",
            "document_type": "UNKNOWN",
            "extraction": {
                "confidence": 0.0,
                "errors": [error_msg],
                "warnings": [],
                "extracted_fields": {}
            },
            "validation": {
                "status": "failed",
                "is_valid": False,
                "overall_score": 0.0,
                "errors": [error_msg],
                "warnings": [],
                "field_validations": {}
            }
        }

class ResultFormatter:
    """Handles result formatting and display"""
    
    @staticmethod
    def print_banner():
        print("=" * 80)
        print("    PAN & AADHAAR DOCUMENT EXTRACTION & VALIDATION SYSTEM")
        print("    Production-Ready Multi-Agent OCR Pipeline with Validation")
        print("=" * 80)
    
    @staticmethod
    def print_result(result: Dict[str, Any]):
        """Print single result in formatted way"""
        status_icon = "✅" if result["status"] == "success" else "❌"
        
        print(f"\n{status_icon} {Path(result['file_path']).name}")
        print(f"   Type: {result['document_type']}")
        print(f"   Status: {result['status'].upper()}")
        
        # Extraction details
        extraction = result.get("extraction", {})
        print(f"   Extraction Confidence: {extraction.get('confidence', 0.0):.1%}")
        
        # Validation details
        validation = result.get("validation", {})
        validation_status = validation.get("status", "unknown")
        is_valid = validation.get("is_valid", False)
        overall_score = validation.get("overall_score", 0.0)
        
        print(f"   Validation Status: {validation_status.upper()}")
        print(f"   Is Valid: {'✅ YES' if is_valid else '❌ NO'}")
        print(f"   Overall Score: {overall_score:.1%}")
        
        # Show field validations
        field_validations = validation.get("field_validations", {})
        if field_validations:
            print(f"   Field Validations:")
            for field_name, field_result in field_validations.items():
                field_status = "✅" if field_result.get("valid", False) else "❌"
                field_type = field_result.get("type", "unknown")
                field_reason = field_result.get("reason", "N/A")
                print(f"     {field_status} {field_name}: {field_type} ({field_reason})")
        
        # Show errors and warnings
        errors = validation.get("errors", [])
        warnings = validation.get("warnings", [])
        
        if errors:
            print(f"   Errors: {', '.join(errors)}")
        if warnings:
            print(f"   Warnings: {', '.join(warnings)}")
    
    @staticmethod
    def print_batch_summary(results: List[Dict[str, Any]]):
        """Print batch processing summary"""
        if not results:
            print("\nNo results to display.")
            return
        
        total = len(results)
        successful = sum(1 for r in results if r["status"] == "success")
        failed = total - successful
        
        valid_count = sum(1 for r in results 
                         if r.get("validation", {}).get("is_valid", False))
        
        print(f"\n{'='*60}")
        print(f"BATCH PROCESSING SUMMARY")
        print(f"{'='*60}")
        print(f"Total Documents: {total}")
        print(f"Successfully Processed: {successful}")
        print(f"Failed Processing: {failed}")
        print(f"Valid Documents: {valid_count}")
        print(f"Invalid Documents: {total - valid_count}")
        print(f"Success Rate: {(successful/total*100):.1f}%")
        print(f"Validation Rate: {(valid_count/total*100):.1f}%")

class CLIHandler:
    """Handles command line interface operations"""
    
    @staticmethod
    def create_parser() -> argparse.ArgumentParser:
        """Create command line argument parser"""
        parser = argparse.ArgumentParser(
            description='Production-ready PAN & Aadhaar document extraction and validation system',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python main_with_validation.py document.pdf                    # Process single document
  python main_with_validation.py --batch documents/              # Process directory
  python main_with_validation.py --output results.json           # Save to JSON file
  python main_with_validation.py --version                       # Show version
            """
        )
        
        parser.add_argument('input', nargs='?', help='PDF file or directory to process')
        parser.add_argument('--batch', action='store_true', help='Process all PDFs in directory')
        parser.add_argument('--output', '-o', help='Output JSON file path')
        parser.add_argument('--quiet', '-q', action='store_true', help='Suppress detailed output')
        parser.add_argument('--version', action='version', version='1.0.0')
        
        return parser
    
    @staticmethod
    def handle_single_document(processor: DocumentProcessorWithValidation, 
                              formatter: ResultFormatter, file_path: str, 
                              output_file: str = None, quiet: bool = False) -> int:
        """Handle single document processing"""
        if not quiet:
            formatter.print_banner()
        
        result = processor.process_document_with_validation(file_path)
        
        if not quiet:
            formatter.print_result(result)
        
        # Save to JSON if output file specified
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\nResults saved to: {output_file}")
        
        return 0 if result["status"] == "success" else 1
    
    @staticmethod
    def handle_batch_processing(processor: DocumentProcessorWithValidation, 
                               formatter: ResultFormatter, directory_path: str,
                               output_file: str = None, quiet: bool = False) -> int:
        """Handle batch processing"""
        if not quiet:
            formatter.print_banner()
        
        results = processor.process_batch_with_validation(directory_path)
        
        if not quiet:
            for result in results:
                formatter.print_result(result)
            formatter.print_batch_summary(results)
        
        # Save to JSON if output file specified
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"\nResults saved to: {output_file}")
        
        successful = sum(1 for r in results if r["status"] == "success")
        return 0 if successful == len(results) else 1

def main():
    """Main entry point"""
    parser = CLIHandler.create_parser()
    args = parser.parse_args()
    
    if not args.input:
        parser.print_help()
        return 1
    
    processor = DocumentProcessorWithValidation()
    formatter = ResultFormatter()
    
    try:
        if args.batch:
            return CLIHandler.handle_batch_processing(
                processor, formatter, args.input, args.output, args.quiet
            )
        else:
            return CLIHandler.handle_single_document(
                processor, formatter, args.input, args.output, args.quiet
            )
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 