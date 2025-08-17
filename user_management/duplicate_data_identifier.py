#!/usr/bin/env python3
"""
Duplicate Data Identification Script for Unique User Management System
Scans existing databases for duplicate records and generates detailed reports
"""

import sqlite3
import json
import csv
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import logging
import argparse

class DuplicateDataIdentifier:
    """Identifies and reports duplicate data across databases"""
    
    def __init__(self, aadhaar_db_path: str = "aadhaar_documents.db", 
                 pan_db_path: str = "pan_documents.db", 
                 output_dir: str = "duplicate_reports"):
        self.aadhaar_db_path = aadhaar_db_path
        self.pan_db_path = pan_db_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.logger = self._setup_logging()
        
        # Report data
        self.report_data = {
            'scan_timestamp': datetime.now().isoformat(),
            'databases_scanned': [],
            'aadhaar_duplicates': [],
            'pan_duplicates': [],
            'cross_database_matches': [],
            'data_quality_issues': [],
            'summary': {}
        }
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for duplicate identification"""
        logger = logging.getLogger('DuplicateDataIdentifier')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def normalize_aadhaar(self, aadhaar: str) -> str:
        """Normalize Aadhaar number for comparison"""
        if not aadhaar:
            return ""
        import re
        return re.sub(r'[^\dX]', '', str(aadhaar).upper())
    
    def normalize_pan(self, pan: str) -> str:
        """Normalize PAN number for comparison"""
        if not pan:
            return ""
        import re
        return re.sub(r'[^A-Z0-9]', '', str(pan).upper())
    
    def check_database_exists(self, db_path: str) -> bool:
        """Check if database file exists and is accessible"""
        try:
            if not Path(db_path).exists():
                self.logger.warning(f"Database file not found: {db_path}")
                return False
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
            self.logger.info(f"Database {db_path} accessible with {len(tables)} tables")
            return True
            
        except Exception as e:
            self.logger.error(f"Cannot access database {db_path}: {e}")
            return False
    
    def scan_aadhaar_duplicates(self) -> List[Dict]:
        """Scan for duplicate Aadhaar numbers"""
        duplicates = []
        
        if not self.check_database_exists(self.aadhaar_db_path):
            return duplicates
        
        self.logger.info("Scanning for Aadhaar duplicates...")
        
        try:
            with sqlite3.connect(self.aadhaar_db_path) as conn:
                cursor = conn.cursor()
                
                # Find Aadhaar numbers with multiple entries
                cursor.execute('''
                    SELECT "Aadhaar Number", COUNT(*) as count
                    FROM extracted_fields
                    WHERE "Aadhaar Number" IS NOT NULL 
                    AND "Aadhaar Number" != ''
                    AND LENGTH(TRIM("Aadhaar Number")) > 0
                    GROUP BY "Aadhaar Number"
                    HAVING COUNT(*) > 1
                    ORDER BY count DESC, "Aadhaar Number"
                ''')
                
                duplicate_groups = cursor.fetchall()
                self.logger.info(f"Found {len(duplicate_groups)} Aadhaar duplicate groups")
                
                for aadhaar_number, count in duplicate_groups:
                    # Get detailed information for each duplicate
                    cursor.execute('''
                        SELECT 
                            ef.id as field_id,
                            ef.document_id,
                            ef."Name",
                            ef."DOB",
                            ef."Gender",
                            ef."Address",
                            ad.file_path,
                            ad.extraction_timestamp,
                            ad.extraction_confidence,
                            ad.created_at
                        FROM extracted_fields ef
                        JOIN aadhaar_documents ad ON ef.document_id = ad.id
                        WHERE ef."Aadhaar Number" = ?
                        ORDER BY ad.created_at ASC
                    ''', (aadhaar_number,))
                    
                    records = cursor.fetchall()
                    
                    # Analyze the duplicates
                    duplicate_info = {
                        'aadhaar_number': aadhaar_number,
                        'normalized_aadhaar': self.normalize_aadhaar(aadhaar_number),
                        'duplicate_count': count,
                        'records': [],
                        'analysis': {
                            'same_name': True,
                            'same_dob': True,
                            'same_gender': True,
                            'confidence_scores': [],
                            'file_paths': [],
                            'date_range': {'earliest': None, 'latest': None}
                        }
                    }
                    
                    names = set()
                    dobs = set()
                    genders = set()
                    
                    for record in records:
                        record_info = {
                            'field_id': record[0],
                            'document_id': record[1],
                            'name': record[2],
                            'dob': record[3],
                            'gender': record[4],
                            'address': record[5],
                            'file_path': record[6],
                            'extraction_timestamp': record[7],
                            'extraction_confidence': record[8],
                            'created_at': record[9]
                        }
                        
                        duplicate_info['records'].append(record_info)
                        
                        # Collect data for analysis
                        if record[2]:  # name
                            names.add(record[2].strip().upper())
                        if record[3]:  # dob
                            dobs.add(record[3])
                        if record[4]:  # gender
                            genders.add(record[4].upper())
                        
                        duplicate_info['analysis']['confidence_scores'].append(record[8] or 0)
                        duplicate_info['analysis']['file_paths'].append(record[6])
                        
                        # Track date range
                        created_at = record[9]
                        if not duplicate_info['analysis']['date_range']['earliest'] or created_at < duplicate_info['analysis']['date_range']['earliest']:
                            duplicate_info['analysis']['date_range']['earliest'] = created_at
                        if not duplicate_info['analysis']['date_range']['latest'] or created_at > duplicate_info['analysis']['date_range']['latest']:
                            duplicate_info['analysis']['date_range']['latest'] = created_at
                    
                    # Update analysis
                    duplicate_info['analysis']['same_name'] = len(names) <= 1
                    duplicate_info['analysis']['same_dob'] = len(dobs) <= 1
                    duplicate_info['analysis']['same_gender'] = len(genders) <= 1
                    duplicate_info['analysis']['unique_names'] = list(names)
                    duplicate_info['analysis']['unique_dobs'] = list(dobs)
                    duplicate_info['analysis']['unique_genders'] = list(genders)
                    duplicate_info['analysis']['avg_confidence'] = sum(duplicate_info['analysis']['confidence_scores']) / len(duplicate_info['analysis']['confidence_scores'])
                    
                    duplicates.append(duplicate_info)
                
        except Exception as e:
            self.logger.error(f"Error scanning Aadhaar duplicates: {e}")
        
        return duplicates
    
    def scan_pan_duplicates(self) -> List[Dict]:
        """Scan for duplicate PAN numbers"""
        duplicates = []
        
        if not self.check_database_exists(self.pan_db_path):
            return duplicates
        
        self.logger.info("Scanning for PAN duplicates...")
        
        try:
            with sqlite3.connect(self.pan_db_path) as conn:
                cursor = conn.cursor()
                
                # Find PAN numbers with multiple entries
                cursor.execute('''
                    SELECT "PAN Number", COUNT(*) as count
                    FROM extracted_fields
                    WHERE "PAN Number" IS NOT NULL 
                    AND "PAN Number" != ''
                    AND LENGTH(TRIM("PAN Number")) > 0
                    GROUP BY "PAN Number"
                    HAVING COUNT(*) > 1
                    ORDER BY count DESC, "PAN Number"
                ''')
                
                duplicate_groups = cursor.fetchall()
                self.logger.info(f"Found {len(duplicate_groups)} PAN duplicate groups")
                
                for pan_number, count in duplicate_groups:
                    # Get detailed information for each duplicate
                    cursor.execute('''
                        SELECT 
                            ef.id as field_id,
                            ef.document_id,
                            ef."Name",
                            ef."Father's Name",
                            ef."DOB",
                            pd.file_path,
                            pd.extraction_timestamp,
                            pd.extraction_confidence,
                            pd.created_at
                        FROM extracted_fields ef
                        JOIN pan_documents pd ON ef.document_id = pd.id
                        WHERE ef."PAN Number" = ?
                        ORDER BY pd.created_at ASC
                    ''', (pan_number,))
                    
                    records = cursor.fetchall()
                    
                    # Analyze the duplicates
                    duplicate_info = {
                        'pan_number': pan_number,
                        'normalized_pan': self.normalize_pan(pan_number),
                        'duplicate_count': count,
                        'records': [],
                        'analysis': {
                            'same_name': True,
                            'same_father_name': True,
                            'same_dob': True,
                            'confidence_scores': [],
                            'file_paths': [],
                            'date_range': {'earliest': None, 'latest': None}
                        }
                    }
                    
                    names = set()
                    father_names = set()
                    dobs = set()
                    
                    for record in records:
                        record_info = {
                            'field_id': record[0],
                            'document_id': record[1],
                            'name': record[2],
                            'fathers_name': record[3],
                            'dob': record[4],
                            'file_path': record[5],
                            'extraction_timestamp': record[6],
                            'extraction_confidence': record[7],
                            'created_at': record[8]
                        }
                        
                        duplicate_info['records'].append(record_info)
                        
                        # Collect data for analysis
                        if record[2]:  # name
                            names.add(record[2].strip().upper())
                        if record[3]:  # father's name
                            father_names.add(record[3].strip().upper())
                        if record[4]:  # dob
                            dobs.add(record[4])
                        
                        duplicate_info['analysis']['confidence_scores'].append(record[7] or 0)
                        duplicate_info['analysis']['file_paths'].append(record[5])
                        
                        # Track date range
                        created_at = record[8]
                        if not duplicate_info['analysis']['date_range']['earliest'] or created_at < duplicate_info['analysis']['date_range']['earliest']:
                            duplicate_info['analysis']['date_range']['earliest'] = created_at
                        if not duplicate_info['analysis']['date_range']['latest'] or created_at > duplicate_info['analysis']['date_range']['latest']:
                            duplicate_info['analysis']['date_range']['latest'] = created_at
                    
                    # Update analysis
                    duplicate_info['analysis']['same_name'] = len(names) <= 1
                    duplicate_info['analysis']['same_father_name'] = len(father_names) <= 1
                    duplicate_info['analysis']['same_dob'] = len(dobs) <= 1
                    duplicate_info['analysis']['unique_names'] = list(names)
                    duplicate_info['analysis']['unique_father_names'] = list(father_names)
                    duplicate_info['analysis']['unique_dobs'] = list(dobs)
                    duplicate_info['analysis']['avg_confidence'] = sum(duplicate_info['analysis']['confidence_scores']) / len(duplicate_info['analysis']['confidence_scores'])
                    
                    duplicates.append(duplicate_info)
                
        except Exception as e:
            self.logger.error(f"Error scanning PAN duplicates: {e}")
        
        return duplicates
    
    def scan_data_quality_issues(self) -> List[Dict]:
        """Scan for data quality issues"""
        issues = []
        
        # Check Aadhaar data quality
        if self.check_database_exists(self.aadhaar_db_path):
            try:
                with sqlite3.connect(self.aadhaar_db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Invalid Aadhaar format
                    cursor.execute('''
                        SELECT COUNT(*) FROM extracted_fields
                        WHERE "Aadhaar Number" IS NOT NULL 
                        AND "Aadhaar Number" != ''
                        AND LENGTH(REPLACE(REPLACE("Aadhaar Number", ' ', ''), '-', '')) != 12
                    ''')
                    invalid_aadhaar_count = cursor.fetchone()[0]
                    
                    if invalid_aadhaar_count > 0:
                        issues.append({
                            'type': 'invalid_aadhaar_format',
                            'database': 'aadhaar',
                            'count': invalid_aadhaar_count,
                            'description': 'Aadhaar numbers with invalid format (not 12 digits)'
                        })
                    
                    # Missing names
                    cursor.execute('''
                        SELECT COUNT(*) FROM extracted_fields
                        WHERE "Name" IS NULL OR "Name" = '' OR LENGTH(TRIM("Name")) = 0
                    ''')
                    missing_names = cursor.fetchone()[0]
                    
                    if missing_names > 0:
                        issues.append({
                            'type': 'missing_names',
                            'database': 'aadhaar',
                            'count': missing_names,
                            'description': 'Records with missing or empty names'
                        })
                    
            except Exception as e:
                self.logger.error(f"Error checking Aadhaar data quality: {e}")
        
        # Check PAN data quality
        if self.check_database_exists(self.pan_db_path):
            try:
                with sqlite3.connect(self.pan_db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Invalid PAN format
                    cursor.execute('''
                        SELECT COUNT(*) FROM extracted_fields
                        WHERE "PAN Number" IS NOT NULL 
                        AND "PAN Number" != ''
                        AND (LENGTH("PAN Number") != 10 
                             OR "PAN Number" NOT GLOB '[A-Z][A-Z][A-Z][A-Z][A-Z][0-9][0-9][0-9][0-9][A-Z]')
                    ''')
                    invalid_pan_count = cursor.fetchone()[0]
                    
                    if invalid_pan_count > 0:
                        issues.append({
                            'type': 'invalid_pan_format',
                            'database': 'pan',
                            'count': invalid_pan_count,
                            'description': 'PAN numbers with invalid format'
                        })
                    
            except Exception as e:
                self.logger.error(f"Error checking PAN data quality: {e}")
        
        return issues
    
    def generate_summary_statistics(self) -> Dict:
        """Generate summary statistics for the scan"""
        summary = {
            'total_aadhaar_duplicate_groups': len(self.report_data['aadhaar_duplicates']),
            'total_pan_duplicate_groups': len(self.report_data['pan_duplicates']),
            'total_aadhaar_duplicate_records': sum(dup['duplicate_count'] for dup in self.report_data['aadhaar_duplicates']),
            'total_pan_duplicate_records': sum(dup['duplicate_count'] for dup in self.report_data['pan_duplicates']),
            'data_quality_issues': len(self.report_data['data_quality_issues']),
            'databases_scanned': len(self.report_data['databases_scanned'])
        }
        
        # Calculate severity levels
        if summary['total_aadhaar_duplicate_groups'] > 10 or summary['total_pan_duplicate_groups'] > 10:
            summary['severity'] = 'HIGH'
        elif summary['total_aadhaar_duplicate_groups'] > 5 or summary['total_pan_duplicate_groups'] > 5:
            summary['severity'] = 'MEDIUM'
        else:
            summary['severity'] = 'LOW'
        
        return summary
    
    def run_full_scan(self) -> Dict:
        """Run complete duplicate data scan"""
        self.logger.info("Starting full duplicate data scan...")
        
        # Record databases being scanned
        if self.check_database_exists(self.aadhaar_db_path):
            self.report_data['databases_scanned'].append(self.aadhaar_db_path)
        if self.check_database_exists(self.pan_db_path):
            self.report_data['databases_scanned'].append(self.pan_db_path)
        
        # Scan for duplicates
        self.report_data['aadhaar_duplicates'] = self.scan_aadhaar_duplicates()
        self.report_data['pan_duplicates'] = self.scan_pan_duplicates()
        
        # Scan for data quality issues
        self.report_data['data_quality_issues'] = self.scan_data_quality_issues()
        
        # Generate summary
        self.report_data['summary'] = self.generate_summary_statistics()
        
        self.logger.info(f"Scan completed. Found {self.report_data['summary']['total_aadhaar_duplicate_groups']} Aadhaar and {self.report_data['summary']['total_pan_duplicate_groups']} PAN duplicate groups")
        
        return self.report_data
    
    def save_json_report(self, filename: str = None) -> str:
        """Save detailed JSON report"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"duplicate_scan_report_{timestamp}.json"
        
        filepath = self.output_dir / filename
        
        try:
            with open(filepath, 'w') as f:
                json.dump(self.report_data, f, indent=2, default=str)
            
            self.logger.info(f"JSON report saved: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Error saving JSON report: {e}")
            return ""
    
    def save_csv_summary(self, filename: str = None) -> str:
        """Save CSV summary of duplicates"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"duplicate_summary_{timestamp}.csv"
        
        filepath = self.output_dir / filename
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow(['Type', 'Number', 'Duplicate_Count', 'Same_Name', 'Same_DOB', 'Avg_Confidence', 'Date_Range'])
                
                # Write Aadhaar duplicates
                for dup in self.report_data['aadhaar_duplicates']:
                    writer.writerow([
                        'AADHAAR',
                        dup['aadhaar_number'],
                        dup['duplicate_count'],
                        dup['analysis']['same_name'],
                        dup['analysis']['same_dob'],
                        f"{dup['analysis']['avg_confidence']:.2f}",
                        f"{dup['analysis']['date_range']['earliest']} to {dup['analysis']['date_range']['latest']}"
                    ])
                
                # Write PAN duplicates
                for dup in self.report_data['pan_duplicates']:
                    writer.writerow([
                        'PAN',
                        dup['pan_number'],
                        dup['duplicate_count'],
                        dup['analysis']['same_name'],
                        dup['analysis']['same_dob'],
                        f"{dup['analysis']['avg_confidence']:.2f}",
                        f"{dup['analysis']['date_range']['earliest']} to {dup['analysis']['date_range']['latest']}"
                    ])
            
            self.logger.info(f"CSV summary saved: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Error saving CSV summary: {e}")
            return ""
    
    def print_summary_report(self) -> None:
        """Print summary report to console"""
        print("\n" + "="*60)
        print("📊 DUPLICATE DATA SCAN SUMMARY")
        print("="*60)
        
        summary = self.report_data['summary']
        
        print(f"Scan Timestamp: {self.report_data['scan_timestamp']}")
        print(f"Databases Scanned: {', '.join(self.report_data['databases_scanned'])}")
        print(f"Severity Level: {summary['severity']}")
        print()
        
        print("🔍 DUPLICATE STATISTICS:")
        print(f"  Aadhaar Duplicate Groups: {summary['total_aadhaar_duplicate_groups']}")
        print(f"  Total Aadhaar Duplicate Records: {summary['total_aadhaar_duplicate_records']}")
        print(f"  PAN Duplicate Groups: {summary['total_pan_duplicate_groups']}")
        print(f"  Total PAN Duplicate Records: {summary['total_pan_duplicate_records']}")
        print(f"  Data Quality Issues: {summary['data_quality_issues']}")
        print()
        
        if self.report_data['aadhaar_duplicates']:
            print("📋 TOP AADHAAR DUPLICATES:")
            for i, dup in enumerate(self.report_data['aadhaar_duplicates'][:5]):
                print(f"  {i+1}. {dup['aadhaar_number']} ({dup['duplicate_count']} records)")
                print(f"     Same Name: {dup['analysis']['same_name']}, Same DOB: {dup['analysis']['same_dob']}")
        
        if self.report_data['pan_duplicates']:
            print("\n📋 TOP PAN DUPLICATES:")
            for i, dup in enumerate(self.report_data['pan_duplicates'][:5]):
                print(f"  {i+1}. {dup['pan_number']} ({dup['duplicate_count']} records)")
                print(f"     Same Name: {dup['analysis']['same_name']}, Same DOB: {dup['analysis']['same_dob']}")
        
        if self.report_data['data_quality_issues']:
            print("\n⚠️  DATA QUALITY ISSUES:")
            for issue in self.report_data['data_quality_issues']:
                print(f"  - {issue['description']}: {issue['count']} records")
        
        print("\n" + "="*60)

def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(description='Identify duplicate data in document databases')
    parser.add_argument('--aadhaar-db', default='aadhaar_documents.db', help='Path to Aadhaar database')
    parser.add_argument('--pan-db', default='pan_documents.db', help='Path to PAN database')
    parser.add_argument('--output-dir', default='duplicate_reports', help='Output directory for reports')
    parser.add_argument('--json-report', action='store_true', help='Save detailed JSON report')
    parser.add_argument('--csv-summary', action='store_true', help='Save CSV summary')
    parser.add_argument('--quiet', action='store_true', help='Suppress console output')
    
    args = parser.parse_args()
    
    # Create identifier
    identifier = DuplicateDataIdentifier(
        aadhaar_db_path=args.aadhaar_db,
        pan_db_path=args.pan_db,
        output_dir=args.output_dir
    )
    
    # Run scan
    report_data = identifier.run_full_scan()
    
    # Save reports
    if args.json_report:
        json_path = identifier.save_json_report()
        if not args.quiet:
            print(f"JSON report saved: {json_path}")
    
    if args.csv_summary:
        csv_path = identifier.save_csv_summary()
        if not args.quiet:
            print(f"CSV summary saved: {csv_path}")
    
    # Print summary
    if not args.quiet:
        identifier.print_summary_report()

if __name__ == "__main__":
    main()