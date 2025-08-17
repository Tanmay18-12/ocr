#!/usr/bin/env python3
"""
Debug script to see raw text from Aadhaar PDF
"""

from pdf2image import convert_from_path
import pytesseract

def main():
    print("🔍 Debug: Raw Text Extraction")
    print("=" * 50)
    
    pdf_path = "sample_documents/aadhar_sample 1.pdf"
    
    try:
        # Convert PDF to images
        pages = convert_from_path(pdf_path, dpi=300)
        print(f"📄 Converted {len(pages)} pages")
        
        # Extract text from first page
        raw_text = pytesseract.image_to_string(pages[0], lang='eng')
        
        print("\n📝 RAW TEXT FROM PDF:")
        print("-" * 30)
        print(raw_text)
        print("-" * 30)
        
        # Also try with Hindi language
        print("\n📝 RAW TEXT WITH HINDI:")
        print("-" * 30)
        hindi_text = pytesseract.image_to_string(pages[0], lang='hin+eng')
        print(hindi_text)
        print("-" * 30)
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()




