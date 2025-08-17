#!/usr/bin/env python3
"""
Production-ready PAN & Aadhaar Document Extraction System
Multi-agent system using OCR and AI for document processing
"""

import sys
import os
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from tools.pdf_extractor_tool import PDFExtractorTool
from utils.logging_config import setup_logging

class DocumentProcessor:
    """Main document processing orchestrator"""
    
    def __init__(self):
        self.logger = setup_logging()
        self.extractor = PDFExtractorTool()
    
    def process_document(self, pdf_path: str) -> Dict[str, Any]:
        """Process a single document and return standardized result"""
        if not os.path.exists(pdf_path):
            return self._create_error_result(pdf_path, "File not found")
        
        try:
            extracted_data = self.extractor.extract_fields(pdf_path)
            return self._create_success_result(pdf_path, extracted_data)
            
        except Exception as e:
            self.logger.error(f"Processing error for {pdf_path}: {e}")
            return self._create_error_result(pdf_path, str(e))
    
    def process_batch(self, directory_path: str) -> List[Dict[str, Any]]:
        """Process all PDF files in directory"""
        if not os.path.exists(directory_path):
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        pdf_files = list(Path(directory_path).glob("**/*.pdf"))
        if not pdf_files:
            self.logger.warning(f"No PDF files found in {directory_path}")
            return []
        
        results = []
        for pdf_file in pdf_files:
            result = self.process_document(str(pdf_file))
            results.append(result)
            self.logger.info(f"Processed {pdf_file}: {result['status']}")
        
        return results
    
    def _create_success_result(self, file_path: str, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create standardized success result"""
        has_error = "error" in extracted_data
        return {
            "timestamp": datetime.now().isoformat(),
            "file_path": file_path,
            "status": "failed" if has_error else "success",
            "document_type": extracted_data.get("document_type", "UNKNOWN"),
            "confidence": extracted_data.get("extraction_confidence", 0.0),
            "errors": [extracted_data.get("error")] if has_error else [],
            "warnings": extracted_data.get("warnings", []),
            "data": extracted_data
        }
    
    def _create_error_result(self, file_path: str, error_msg: str) -> Dict[str, Any]:
        """Create standardized error result"""
        return {
            "timestamp": datetime.now().isoformat(),
            "file_path": file_path,
            "status": "error",
            "document_type": "UNKNOWN",
            "confidence": 0.0,
            "errors": [error_msg],
            "warnings": [],
            "data": {}
        }

class ResultFormatter:
    """Handles result formatting and display"""
    
    @staticmethod
    def print_banner():
        print("=" * 60)
        print("    PAN & AADHAAR DOCUMENT EXTRACTION SYSTEM")
        print("    Production-Ready Multi-Agent OCR Pipeline")
        print("=" * 60)
    
    @staticmethod
    def print_result(result: Dict[str, Any]):
        """Print single result in formatted way"""
        status_icon = "✅" if result["status"] == "success" else "❌"
        
        print(f"\n{status_icon} {Path(result['file_path']).name}")
        print(f"   Type: {result['document_type']}")
        print(f"   Confidence: {result['confidence']:.1%}")
        print(f"   Status: {result['status'].upper()}")
        
        if result["errors"]:
            print(f"   Errors: {'; '.join(result['errors'])}")
        
        if result["warnings"]:
            print(f"   Warnings: {'; '.join(result['warnings'])}")
        
        # Print extracted fields
        data = result.get("data", {})
        key_fields = ["Name", "PAN Number", "Aadhaar Number", "DOB", "Father's Name", "Gender", "Address"]
        
        extracted_fields = {k: v for k, v in data.items() 
                          if k in key_fields and v and k not in ["raw_text", "document_type"]}
        
        if extracted_fields:
            print("   Fields:")
            for field, value in extracted_fields.items():
                # Truncate long values (like address)
                display_value = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                print(f"     {field}: {display_value}")
    
    @staticmethod
    def print_batch_summary(results: List[Dict[str, Any]]):
        """Print batch processing summary"""
        if not results:
            print("\n📊 No results to display")
            return
        
        total = len(results)
        successful = sum(1 for r in results if r["status"] == "success")
        failed = total - successful
        
        print(f"\n📊 BATCH SUMMARY")
        print(f"   Total: {total} | Success: {successful} | Failed: {failed}")
        print(f"   Success Rate: {(successful/total*100):.1f}%")
        
        # Document type distribution
        doc_types = {}
        for result in results:
            doc_type = result["document_type"]
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
        
        if doc_types:
            print(f"   Document Types: {dict(doc_types)}")

class CLIHandler:
    """Handles command line interface operations"""
    
    @staticmethod
    def create_parser() -> argparse.ArgumentParser:
        """Create command line argument parser"""
        parser = argparse.ArgumentParser(
            description='Production-ready PAN & Aadhaar document extraction system',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python main.py document.pdf                    # Process single document
  python main.py --batch documents/              # Process directory
  python main.py --version                       # Show version
            """
        )
        
        parser.add_argument('input', nargs='?', 
                           help='PDF file path or directory for batch processing')
        parser.add_argument('--batch', action='store_true', 
                           help='Process all PDF files in directory')
        parser.add_argument('--quiet', action='store_true', 
                           help='Minimal output mode')
        parser.add_argument('--version', action='version', version='%(prog)s 1.0.0')
        
        return parser
    
    @staticmethod
    def handle_single_document(processor: DocumentProcessor, formatter: ResultFormatter, 
                              file_path: str, quiet: bool) -> int:
        """Handle single document processing"""
        result = processor.process_document(file_path)
        
        if not quiet:
            formatter.print_result(result)
        
        if result["status"] != "success":
            return 1
        else:
            print("\n🎉 Processing completed successfully!")
            return 0
    
    @staticmethod
    def handle_batch_processing(processor: DocumentProcessor, formatter: ResultFormatter, 
                               directory_path: str, quiet: bool) -> int:
        """Handle batch document processing"""
        results = processor.process_batch(directory_path)
        
        if not quiet:
            for result in results:
                formatter.print_result(result)
            formatter.print_batch_summary(results)
        
        # Exit with error code if any processing failed
        failed_count = sum(1 for r in results if r["status"] != "success")
        return 1 if failed_count > 0 else 0

def main():
    """Main application entry point"""
    parser = CLIHandler.create_parser()
    args = parser.parse_args()
    
    if not args.input:
        parser.print_help()
        return
    
    processor = DocumentProcessor()
    formatter = ResultFormatter()
    
    try:
        if not args.quiet:
            formatter.print_banner()
        
        if args.batch:
            exit_code = CLIHandler.handle_batch_processing(
                processor, formatter, args.input, args.quiet
            )
        else:
            exit_code = CLIHandler.handle_single_document(
                processor, formatter, args.input, args.quiet
            )
        
        sys.exit(exit_code)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Processing interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()