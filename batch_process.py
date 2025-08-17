# batch_process.py
import os
import json
from pathlib import Path
from datetime import datetime
from graph.workflow import process_batch_with_graph
from utils.logging_config import setup_logging
from config import Config

def process_batch(input_directory: str, output_file: str = None):
    """Process all PDF files in a directory and save results"""
    
    logger = setup_logging()
    
    # Ensure input directory exists
    if not os.path.exists(input_directory):
        logger.error(f"Input directory not found: {input_directory}")
        return False
    
    # Find all PDF files
    pdf_files = []
    for ext in ['*.pdf', '*.PDF']:
        pdf_files.extend(Path(input_directory).glob(f"**/{ext}"))
    
    if not pdf_files:
        logger.warning(f"No PDF files found in: {input_directory}")
        return False
    
    logger.info(f"Found {len(pdf_files)} PDF files to process")
    
    # Process files using LangGraph
    try:
        results = process_batch_with_graph([str(f) for f in pdf_files])
        
        # Calculate statistics
        total_files = len(results)
        successful = len([r for r in results if r.get('validation_status') == 'passed'])
        failed = total_files - successful
        success_rate = (successful / total_files * 100) if total_files > 0 else 0
        
        # Create summary
        summary = {
            "processing_timestamp": datetime.now().isoformat(),
            "input_directory": input_directory,
            "total_files": total_files,
            "successful": successful,
            "failed": failed,
            "success_rate": round(success_rate, 2),
            "results": results
        }
        
        # Save results
        if output_file:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            logger.info(f"Results saved to: {output_file}")
        
        # Print summary
        print(f"\n📊 BATCH PROCESSING SUMMARY:")
        print(f"   Total Files: {total_files}")
        print(f"   Successful: {successful}")
        print(f"   Failed: {failed}")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in batch processing: {e}")
        return False

def main():
    """Main function for batch processing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Batch process PDF documents')
    parser.add_argument('input_dir', help='Input directory containing PDF files')
    parser.add_argument('--output', '-o', help='Output JSON file for results')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set up output file
    if not args.output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = os.path.join(Config.OUTPUT_DIR, f"batch_results_{timestamp}.json")
    
    # Process batch
    success = process_batch(args.input_dir, args.output)
    
    if success:
        print(f"\n✅ Batch processing completed successfully!")
        print(f"📁 Results saved to: {args.output}")
    else:
        print(f"\n❌ Batch processing failed!")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())