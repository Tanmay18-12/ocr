import os
import shutil
from pathlib import Path
from typing import List, Optional
import hashlib
import json
from datetime import datetime

class FileUtils:
    @staticmethod
    def ensure_directory(directory: str) -> None:
        """Create directory if it doesn't exist"""
        os.makedirs(directory, exist_ok=True)
    
    @staticmethod
    def get_file_hash(file_path: str) -> str:
        """Calculate MD5 hash of a file"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""
    
    @staticmethod
    def find_pdf_files(directory: str, recursive: bool = True) -> List[str]:
        """Find all PDF files in a directory"""
        pdf_files = []
        directory_path = Path(directory)
        
        if recursive:
            pattern = "**/*.pdf"
        else:
            pattern = "*.pdf"
        
        for pdf_file in directory_path.glob(pattern):
            if pdf_file.is_file():
                pdf_files.append(str(pdf_file))
        
        # Also check for uppercase extension
        if recursive:
            pattern = "**/*.PDF"
        else:
            pattern = "*.PDF"
        
        for pdf_file in directory_path.glob(pattern):
            if pdf_file.is_file():
                pdf_files.append(str(pdf_file))
        
        return sorted(pdf_files)
    
    @staticmethod
    def backup_file(file_path: str, backup_dir: str) -> Optional[str]:
        """Create a backup of a file"""
        try:
            FileUtils.ensure_directory(backup_dir)
            filename = os.path.basename(file_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{timestamp}_{filename}"
            backup_path = os.path.join(backup_dir, backup_filename)
            shutil.copy2(file_path, backup_path)
            return backup_path
        except Exception:
            return None
    
    @staticmethod
    def save_json(data: dict, file_path: str, pretty: bool = True) -> bool:
        """Save data as JSON file"""
        try:
            FileUtils.ensure_directory(os.path.dirname(file_path))
            with open(file_path, 'w', encoding='utf-8') as f:
                if pretty:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                else:
                    json.dump(data, f, ensure_ascii=False)
            return True
        except Exception:
            return False
    
    @staticmethod
    def load_json(file_path: str) -> Optional[dict]:
        """Load data from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
    
    @staticmethod
    def get_file_size(file_path: str) -> int:
        """Get file size in bytes"""
        try:
            return os.path.getsize(file_path)
        except Exception:
            return 0
    
    @staticmethod
    def is_valid_pdf(file_path: str) -> bool:
        """Check if file is a valid PDF"""
        try:
            with open(file_path, 'rb') as f:
                header = f.read(4)
                return header == b'%PDF'
        except Exception:
            return False
