#!/usr/bin/env python3
"""
Duplicate Prevention Service for Unique User Management System
Prevents duplicate document entries across all databases
"""

import sqlite3
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

class DuplicatePreventionService:
    """Prevents duplicate document entries across all tables"""
    
    def __init__(self, aadhaar_db_path: str = "aadhaar_documents.db", 
                 pan_db_path: str = "pan_documents.db"):
        self.aadhaar_db_path = aadhaar_db_path
        self.pan_db_path = pan_db_path
        self.logger = self._setup_logging()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for duplicate prevention operations"""
        logger = logging.getLogger('DuplicatePreventionService')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def normalize_aadhaar(self, aadhaar_number: str) -> str:
        """Normalize Aadhaar number by removing spaces, hyphens, and converting to uppercase"""
        if not aadhaar_number:
            return ""
        
        # Remove all non-digit characters except X (for masked Aadhaar)
        normalized = re.sub(r'[^\dX]', '', str(aadhaar_number).upper())
        
        # Validate length (should be 12 characters)
        if len(normalized) != 12:
            self.logger.warning(f"Invalid Aadhaar length: {len(normalized)} for {aadhaar_number}")
        
        return normalized
    
    def normalize_pan(self, pan_number: str) -> str:
        """Normalize PAN number by removing spaces, hyphens, and converting to uppercase"""
        if not pan_number:
            return ""
        
        # Remove all non-alphanumeric characters and convert to uppercase
        normalized = re.sub(r'[^A-Z0-9]', '', str(pan_number).upper())
        
        # Validate PAN format (5 letters + 4 digits + 1 letter)
        if len(normalized) != 10:
            self.logger.warning(f"Invalid PAN length: {len(normalized)} for {pan_number}")
        elif not re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]$', normalized):
            self.logger.warning(f"Invalid PAN format: {normalized}")
        
        return normalized
    
    def check_aadhaar_exists(self, aadhaar_number: str) -> Optional[Dict]:
        """Check if Aadhaar number already exists in database"""
        if not aadhaar_number:
            return None
        
        normalized_aadhaar = self.normalize_aadhaar(aadhaar_number)
        
        try:
            with sqlite3.connect(self.aadhaar_db_path) as conn:
                cursor = conn.cursor()
                
                # Check in extracted_fields table
                cursor.execute('''
                    SELECT ef.id, ef.document_id, ef."Aadhaar Number", ef."Name", 
                           ad.file_path, ad.created_at
                    FROM extracted_fields ef
                    JOIN aadhaar_documents ad ON ef.document_id = ad.id
                    WHERE ef."Aadhaar Number" = ?
                ''', (normalized_aadhaar,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'exists': True,
                        'field_id': row[0],
                        'document_id': row[1],
                        'aadhaar_number': row[2],
                        'name': row[3],
                        'file_path': row[4],
                        'created_at': row[5],
                        'database': 'aadhaar',
                        'table': 'extracted_fields'
                    }
                
        except Exception as e:
            self.logger.error(f"Error checking Aadhaar existence: {e}")
        
        return None
    
    def check_pan_exists(self, pan_number: str) -> Optional[Dict]:
        """Check if PAN number already exists in database"""
        if not pan_number:
            return None
        
        normalized_pan = self.normalize_pan(pan_number)
        
        try:
            with sqlite3.connect(self.pan_db_path) as conn:
                cursor = conn.cursor()
                
                # Check in extracted_fields table
                cursor.execute('''
                    SELECT ef.id, ef.document_id, ef."PAN Number", ef."Name", 
                           pd.file_path, pd.created_at
                    FROM extracted_fields ef
                    JOIN pan_documents pd ON ef.document_id = pd.id
                    WHERE ef."PAN Number" = ?
                ''', (normalized_pan,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'exists': True,
                        'field_id': row[0],
                        'document_id': row[1],
                        'pan_number': row[2],
                        'name': row[3],
                        'file_path': row[4],
                        'created_at': row[5],
                        'database': 'pan',
                        'table': 'extracted_fields'
                    }
                
        except Exception as e:
            self.logger.error(f"Error checking PAN existence: {e}")
        
        return None
    
    def find_duplicate_aadhaar_numbers(self) -> List[Dict]:
        """Find all duplicate Aadhaar numbers in the database"""
        duplicates = []
        
        try:
            with sqlite3.connect(self.aadhaar_db_path) as conn:
                cursor = conn.cursor()
                
                # Find Aadhaar numbers that appear more than once
                cursor.execute('''
                    SELECT "Aadhaar Number", COUNT(*) as count
                    FROM extracted_fields
                    WHERE "Aadhaar Number" IS NOT NULL AND "Aadhaar Number" != ''
                    GROUP BY "Aadhaar Number"
                    HAVING COUNT(*) > 1
                    ORDER BY count DESC
                ''')
                
                duplicate_aadhaar_numbers = cursor.fetchall()
                
                for aadhaar_number, count in duplicate_aadhaar_numbers:
                    # Get all records for this Aadhaar number
                    cursor.execute('''
                        SELECT ef.id, ef.document_id, ef."Name", ef."DOB", ef."Gender", 
                               ef."Address", ad.file_path, ad.created_at, ad.extraction_confidence
                        FROM extracted_fields ef
                        JOIN aadhaar_documents ad ON ef.document_id = ad.id
                        WHERE ef."Aadhaar Number" = ?
                        ORDER BY ad.created_at DESC
                    ''', (aadhaar_number,))
                    
                    records = cursor.fetchall()
                    
                    duplicate_info = {
                        'aadhaar_number': aadhaar_number,
                        'count': count,
                        'records': []
                    }
                    
                    for record in records:
                        duplicate_info['records'].append({
                            'field_id': record[0],
                            'document_id': record[1],
                            'name': record[2],
                            'dob': record[3],
                            'gender': record[4],
                            'address': record[5],
                            'file_path': record[6],
                            'created_at': record[7],
                            'confidence': record[8]
                        })
                    
                    duplicates.append(duplicate_info)
                
        except Exception as e:
            self.logger.error(f"Error finding duplicate Aadhaar numbers: {e}")
        
        return duplicates
    
    def find_duplicate_pan_numbers(self) -> List[Dict]:
        """Find all duplicate PAN numbers in the database"""
        duplicates = []
        
        try:
            with sqlite3.connect(self.pan_db_path) as conn:
                cursor = conn.cursor()
                
                # Find PAN numbers that appear more than once
                cursor.execute('''
                    SELECT "PAN Number", COUNT(*) as count
                    FROM extracted_fields
                    WHERE "PAN Number" IS NOT NULL AND "PAN Number" != ''
                    GROUP BY "PAN Number"
                    HAVING COUNT(*) > 1
                    ORDER BY count DESC
                ''')
                
                duplicate_pan_numbers = cursor.fetchall()
                
                for pan_number, count in duplicate_pan_numbers:
                    # Get all records for this PAN number
                    cursor.execute('''
                        SELECT ef.id, ef.document_id, ef."Name", ef."Father's Name", ef."DOB", 
                               pd.file_path, pd.created_at, pd.extraction_confidence
                        FROM extracted_fields ef
                        JOIN pan_documents pd ON ef.document_id = pd.id
                        WHERE ef."PAN Number" = ?
                        ORDER BY pd.created_at DESC
                    ''', (pan_number,))
                    
                    records = cursor.fetchall()
                    
                    duplicate_info = {
                        'pan_number': pan_number,
                        'count': count,
                        'records': []
                    }
                    
                    for record in records:
                        duplicate_info['records'].append({
                            'field_id': record[0],
                            'document_id': record[1],
                            'name': record[2],
                            'fathers_name': record[3],
                            'dob': record[4],
                            'file_path': record[5],
                            'created_at': record[6],
                            'confidence': record[7]
                        })
                    
                    duplicates.append(duplicate_info)
                
        except Exception as e:
            self.logger.error(f"Error finding duplicate PAN numbers: {e}")
        
        return duplicates
    
    def get_duplicate_report(self) -> Dict:
        """Generate comprehensive duplicate report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'aadhaar_duplicates': self.find_duplicate_aadhaar_numbers(),
            'pan_duplicates': self.find_duplicate_pan_numbers(),
            'summary': {}
        }
        
        # Calculate summary statistics
        aadhaar_duplicate_count = len(report['aadhaar_duplicates'])
        pan_duplicate_count = len(report['pan_duplicates'])
        
        total_aadhaar_records = sum(dup['count'] for dup in report['aadhaar_duplicates'])
        total_pan_records = sum(dup['count'] for dup in report['pan_duplicates'])
        
        report['summary'] = {
            'aadhaar_duplicate_groups': aadhaar_duplicate_count,
            'pan_duplicate_groups': pan_duplicate_count,
            'total_duplicate_aadhaar_records': total_aadhaar_records,
            'total_duplicate_pan_records': total_pan_records,
            'total_duplicate_groups': aadhaar_duplicate_count + pan_duplicate_count
        }
        
        return report
    
    def validate_document_uniqueness(self, document_type: str, document_data: Dict) -> Tuple[bool, Optional[Dict]]:
        """Validate that a document is unique before insertion"""
        if document_type.upper() == 'AADHAAR':
            aadhaar_number = document_data.get('Aadhaar Number')
            if aadhaar_number:
                existing = self.check_aadhaar_exists(aadhaar_number)
                if existing:
                    return False, existing
        
        elif document_type.upper() == 'PAN':
            pan_number = document_data.get('PAN Number')
            if pan_number:
                existing = self.check_pan_exists(pan_number)
                if existing:
                    return False, existing
        
        return True, None
    
    def log_duplicate_attempt(self, document_type: str, attempted_data: Dict, 
                            existing_record: Dict) -> None:
        """Log duplicate insertion attempts for audit purposes"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'document_type': document_type,
            'attempted_data': {
                'aadhaar_number': attempted_data.get('Aadhaar Number', ''),
                'pan_number': attempted_data.get('PAN Number', ''),
                'name': attempted_data.get('Name', ''),
                'file_path': attempted_data.get('file_path', '')
            },
            'existing_record': {
                'document_id': existing_record.get('document_id'),
                'file_path': existing_record.get('file_path'),
                'created_at': existing_record.get('created_at')
            }
        }
        
        self.logger.warning(f"Duplicate {document_type} attempt blocked: {log_entry}")
    
    def get_data_quality_metrics(self) -> Dict:
        """Get data quality metrics including duplicate statistics"""
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'aadhaar_metrics': {},
            'pan_metrics': {}
        }
        
        # Aadhaar metrics
        try:
            with sqlite3.connect(self.aadhaar_db_path) as conn:
                cursor = conn.cursor()
                
                # Total records
                cursor.execute('SELECT COUNT(*) FROM extracted_fields WHERE "Aadhaar Number" IS NOT NULL')
                total_aadhaar = cursor.fetchone()[0]
                
                # Unique Aadhaar numbers
                cursor.execute('SELECT COUNT(DISTINCT "Aadhaar Number") FROM extracted_fields WHERE "Aadhaar Number" IS NOT NULL')
                unique_aadhaar = cursor.fetchone()[0]
                
                # Records with valid format (12 digits)
                cursor.execute('''
                    SELECT COUNT(*) FROM extracted_fields 
                    WHERE "Aadhaar Number" IS NOT NULL 
                    AND LENGTH(REPLACE(REPLACE("Aadhaar Number", ' ', ''), '-', '')) = 12
                ''')
                valid_format_aadhaar = cursor.fetchone()[0]
                
                metrics['aadhaar_metrics'] = {
                    'total_records': total_aadhaar,
                    'unique_numbers': unique_aadhaar,
                    'duplicate_records': total_aadhaar - unique_aadhaar,
                    'valid_format_records': valid_format_aadhaar,
                    'duplicate_percentage': ((total_aadhaar - unique_aadhaar) / total_aadhaar * 100) if total_aadhaar > 0 else 0
                }
                
        except Exception as e:
            self.logger.error(f"Error calculating Aadhaar metrics: {e}")
        
        # PAN metrics
        try:
            with sqlite3.connect(self.pan_db_path) as conn:
                cursor = conn.cursor()
                
                # Total records
                cursor.execute('SELECT COUNT(*) FROM extracted_fields WHERE "PAN Number" IS NOT NULL')
                total_pan = cursor.fetchone()[0]
                
                # Unique PAN numbers
                cursor.execute('SELECT COUNT(DISTINCT "PAN Number") FROM extracted_fields WHERE "PAN Number" IS NOT NULL')
                unique_pan = cursor.fetchone()[0]
                
                # Records with valid format (10 characters, 5 letters + 4 digits + 1 letter)
                cursor.execute('''
                    SELECT COUNT(*) FROM extracted_fields 
                    WHERE "PAN Number" IS NOT NULL 
                    AND LENGTH("PAN Number") = 10
                    AND "PAN Number" GLOB '[A-Z][A-Z][A-Z][A-Z][A-Z][0-9][0-9][0-9][0-9][A-Z]'
                ''')
                valid_format_pan = cursor.fetchone()[0]
                
                metrics['pan_metrics'] = {
                    'total_records': total_pan,
                    'unique_numbers': unique_pan,
                    'duplicate_records': total_pan - unique_pan,
                    'valid_format_records': valid_format_pan,
                    'duplicate_percentage': ((total_pan - unique_pan) / total_pan * 100) if total_pan > 0 else 0
                }
                
        except Exception as e:
            self.logger.error(f"Error calculating PAN metrics: {e}")
        
        return metrics

def main():
    """Test the DuplicatePreventionService"""
    print("🔍 Duplicate Prevention Service Test")
    print("=" * 50)
    
    service = DuplicatePreventionService()
    
    # Test normalization
    print("\n📝 Testing normalization...")
    test_aadhaar = "1234 5678 9012"
    normalized_aadhaar = service.normalize_aadhaar(test_aadhaar)
    print(f"Aadhaar: '{test_aadhaar}' -> '{normalized_aadhaar}'")
    
    test_pan = "ABCDE-1234-F"
    normalized_pan = service.normalize_pan(test_pan)
    print(f"PAN: '{test_pan}' -> '{normalized_pan}'")
    
    # Test duplicate detection
    print("\n🔍 Testing duplicate detection...")
    aadhaar_exists = service.check_aadhaar_exists("123456789012")
    if aadhaar_exists:
        print(f"Found existing Aadhaar: {aadhaar_exists['name']}")
    else:
        print("No existing Aadhaar found")
    
    # Generate duplicate report
    print("\n📊 Generating duplicate report...")
    report = service.get_duplicate_report()
    print(f"Aadhaar duplicate groups: {report['summary']['aadhaar_duplicate_groups']}")
    print(f"PAN duplicate groups: {report['summary']['pan_duplicate_groups']}")
    
    # Get data quality metrics
    print("\n📈 Data quality metrics...")
    metrics = service.get_data_quality_metrics()
    
    if metrics['aadhaar_metrics']:
        aadhaar_metrics = metrics['aadhaar_metrics']
        print(f"Aadhaar - Total: {aadhaar_metrics['total_records']}, "
              f"Unique: {aadhaar_metrics['unique_numbers']}, "
              f"Duplicates: {aadhaar_metrics['duplicate_records']} "
              f"({aadhaar_metrics['duplicate_percentage']:.1f}%)")
    
    if metrics['pan_metrics']:
        pan_metrics = metrics['pan_metrics']
        print(f"PAN - Total: {pan_metrics['total_records']}, "
              f"Unique: {pan_metrics['unique_numbers']}, "
              f"Duplicates: {pan_metrics['duplicate_records']} "
              f"({pan_metrics['duplicate_percentage']:.1f}%)")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()