import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Tesseract configuration
    TESSERACT_CMD = os.getenv('TESSERACT_CMD', 'tesseract')
    
    # PDF processing settings
    PDF_DPI = int(os.getenv('PDF_DPI', '400'))
    MAX_PAGES_TO_PROCESS = int(os.getenv('MAX_PAGES_TO_PROCESS', '2'))
    
    # Output directories
    OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'output')
    LOGS_DIR = os.getenv('LOGS_DIR', 'logs')
    
    # Validation settings
    MIN_CONFIDENCE_SCORE = float(os.getenv('MIN_CONFIDENCE_SCORE', '0.7'))
    
    # LangGraph settings
    LANGGRAPH_VERBOSE = os.getenv('LANGGRAPH_VERBOSE', 'True').lower() == 'true'
    
    # OCR settings
    OCR_LANGUAGES = os.getenv('OCR_LANGUAGES', 'eng')
    OCR_PSM_MODES = [int(x) for x in os.getenv('OCR_PSM_MODES', '6,8,13').split(',')]
    
    # Processing settings
    ENABLE_IMAGE_PREPROCESSING = os.getenv('ENABLE_IMAGE_PREPROCESSING', 'True').lower() == 'true'
    ENABLE_ORIENTATION_CORRECTION = os.getenv('ENABLE_ORIENTATION_CORRECTION', 'True').lower() == 'true'
    MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', '50'))
    
    # OpenAI settings
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4')