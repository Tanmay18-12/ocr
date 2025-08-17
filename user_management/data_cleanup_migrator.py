#!/usr/bin/env python3
"""
Data Cleanup and Migration Script for Unique User Management System
Handles duplicate record cleanup, data migration, and constraint application
"""

import sqlite3
import json
import shutil
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import logging
import argparse

from duplicate_data_identifier import DuplicateDataIdentifier
from database_schema_manager import DatabaseSchemaManager
from user_id_manager import UserIDManager
from exceptions import MigrationError, DataIntegrityError

class DataCleanupMigrator:
    """Handles data cleanup and migration operations"""
    
    def __init__(self, aadhaar_db_path: str = "aadhaar_documents.db", 
                 pan_db_path: str = "pan_documents.db",
                 backup_dir: str = "migration_backups"):
        self.aadhaar_db_path = aadhaar_db_path
        self.pan_db_path = pan_db_path
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        
        self.logger = self._setup_logging()
        self.identifier = DuplicateDataIdentifier(aadhaar_db_path, pan_db_path)
        self.schema_manager = DatabaseSchemaManager(aadhaar_db_path, pan_db_path)
        self.user_manager = UserIDManager(aadhaar_db_path, pan_db_path)
        
        # Migration tracking
        self.migration_log = {
            'start_time': datetime.now().isoformat(),
            'operations': [],
            'backups_created': [],
            'errors': [],
            'rollback_available': True
        }
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for migration operations"""
        logger = logging.getLogger('DataCleanupMigrator')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def create_migration_backup(self, db_path: str) -> str:
        """Create backup before migration"""
        if not Path(db_path).exists():
            self.logger.warning(f"Database {db_path} does not exist, skipping backup")
            return ""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        db_name = Path(db_path).stem
        backup_path = self.backup_dir / f"{db_name}_pre_migration_{timestamp}.db"
        
        try:
            shutil.copy2(db_path, backup_path)
            self.migration_log['backups_created'].append(str(backup_path))
            self.logger.info(f"Created migration backup: {backup_path}")
            return str(backup_path)
        except Exception as e:
            error_msg = f"Failed to create backup for {db_path}: {e}"
            self.logger.error(error_msg)
            self.migration_log['errors'].append(error_msg)
            raise MigrationError("backup_creation", db_path, original_error=str(e))
    
    def analyze_duplicates_for_cleanup(self, duplicates: List[Dict]) -> Dict:
        """Analyze duplicates to determine cleanup strategy"""
        cleanup_plan = {
            'total_groups': len(duplicates),
            'records_to_keep': [],
            'records_to_remove': [],
            'merge_candidates': [],
            'manual_review_needed': []
        }
        
        for dup_group in duplicates:
            records = dup_group['records']
            analysis = dup_group['analysis']
            
            if len(records) == 2 and analysis['same_name'] and analysis['same_dob']:
                # Simple case: 2 records with same name and DOB
                # Keep the one with higher confidence or more recent date
                sorted_records = sorted(records, key=lambda x: (x['extraction_confidence'] or 0, x['created_at']), reverse=True)
                cleanup_plan['records_to_keep'].append(sorted_records[0])
                cleanup_plan['records_to_remove'].extend(sorted_records[1:])
                
            elif analysis['same_name'] and analysis['same_dob']:
                # Multiple records with same name and DOB
                # Keep the most recent one with highest confidence
                sorted_records = sorted(records, key=lambda x: (x['extraction_confidence'] or 0, x['created_at']), reverse=True)
                cleanup_plan['records_to_keep'].append(sorted_records[0])
                cleanup_plan['records_to_remove'].extend(sorted_records[1:])
                
            elif len(analysis['unique_names']) == 1:
                # Same name but different other details - potential data entry variations
                # Keep the most complete record (highest confidence)
                best_record = max(records, key=lambda x: x['extraction_confidence'] or 0)
                cleanup_plan['records_to_keep'].append(best_record)
                cleanup_plan['records_to_remove'].extend([r for r in records if r != best_record])
                
            else:
                # Different names - needs manual review
                cleanup_plan['manual_review_needed'].append(dup_group)
        
        return cleanup_plan
    
    def remove_duplicate_record(self, db_path: str, document_table: str, fields_table: str, 
                               field_id: int, document_id: int) -> bool:
        """Remove a duplicate record from database"""
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Remove from extracted_fields table
                cursor.execute(f'DELETE FROM {fields_table} WHERE id = ?', (field_id,))
                
                # Check if this was the only field record for the document
                cursor.execute(f'SELECT COUNT(*) FROM {fields_table} WHERE document_id = ?', (document_id,))
                remaining_fields = cursor.fetchone()[0]
                
                if remaining_fields == 0:
                    # Remove the document record as well
                    cursor.execute(f'DELETE FROM {document_table} WHERE id = ?', (document_id,))
                    self.logger.info(f"Removed document {document_id} and its fields")
                else:
                    self.logger.info(f"Removed field record {field_id}")
                
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Error removing duplicate record: {e}")
            return False
    
    def cleanup_aadhaar_duplicates(self, dry_run: bool = False) -> Dict:
        """Clean up Aadhaar duplicate records"""
        self.logger.info("Starting Aadhaar duplicate cleanup...")
        
        # Get duplicates
        duplicates = self.identifier.scan_aadhaar_duplicates()
        if not duplicates:
            self.logger.info("No Aadhaar duplicates found")
            return {'status': 'success', 'removed_count': 0, 'kept_count': 0}
        
        # Analyze cleanup strategy
        cleanup_plan = self.analyze_duplicates_for_cleanup(duplicates)
        
        self.logger.info(f"Cleanup plan: {len(cleanup_plan['records_to_keep'])} to keep, "
                        f"{len(cleanup_plan['records_to_remove'])} to remove, "
                        f"{len(cleanup_plan['manual_review_needed'])} need manual review")
        
        if dry_run:
            return {
                'status': 'dry_run',
                'cleanup_plan': cleanup_plan,
                'would_remove': len(cleanup_plan['records_to_remove']),
                'would_keep': len(cleanup_plan['records_to_keep'])
            }
        
        # Perform cleanup
        removed_count = 0
        for record in cleanup_plan['records_to_remove']:
            if self.remove_duplicate_record(
                self.aadhaar_db_path, 'aadhaar_documents', 'extracted_fields',
                record['field_id'], record['document_id']
            ):
                removed_count += 1
        
        operation_log = {
            'operation': 'aadhaar_duplicate_cleanup',
            'timestamp': datetime.now().isoformat(),
            'removed_count': removed_count,
            'kept_count': len(cleanup_plan['records_to_keep']),
            'manual_review_count': len(cleanup_plan['manual_review_needed'])
        }
        self.migration_log['operations'].append(operation_log)
        
        return {
            'status': 'success',
            'removed_count': removed_count,
            'kept_count': len(cleanup_plan['records_to_keep']),
            'manual_review_needed': cleanup_plan['manual_review_needed']
        }
    
    def cleanup_pan_duplicates(self, dry_run: bool = False) -> Dict:
        """Clean up PAN duplicate records"""
        self.logger.info("Starting PAN duplicate cleanup...")
        
        # Get duplicates
        duplicates = self.identifier.scan_pan_duplicates()
        if not duplicates:
            self.logger.info("No PAN duplicates found")
            return {'status': 'success', 'removed_count': 0, 'kept_count': 0}
        
        # Analyze cleanup strategy
        cleanup_plan = self.analyze_duplicates_for_cleanup(duplicates)
        
        self.logger.info(f"Cleanup plan: {len(cleanup_plan['records_to_keep'])} to keep, "
                        f"{len(cleanup_plan['records_to_remove'])} to remove, "
                        f"{len(cleanup_plan['manual_review_needed'])} need manual review")
        
        if dry_run:
            return {
                'status': 'dry_run',
                'cleanup_plan': cleanup_plan,
                'would_remove': len(cleanup_plan['records_to_remove']),
                'would_keep': len(cleanup_plan['records_to_keep'])
            }
        
        # Perform cleanup
        removed_count = 0
        for record in cleanup_plan['records_to_remove']:
            if self.remove_duplicate_record(
                self.pan_db_path, 'pan_documents', 'extracted_fields',
                record['field_id'], record['document_id']
            ):
                removed_count += 1
        
        operation_log = {
            'operation': 'pan_duplicate_cleanup',
            'timestamp': datetime.now().isoformat(),
            'removed_count': removed_count,
            'kept_count': len(cleanup_plan['records_to_keep']),
            'manual_review_count': len(cleanup_plan['manual_review_needed'])
        }
        self.migration_log['operations'].append(operation_log)
        
        return {
            'status': 'success',
            'removed_count': removed_count,
            'kept_count': len(cleanup_plan['records_to_keep']),
            'manual_review_needed': cleanup_plan['manual_review_needed']
        }
    
    def migrate_existing_data_to_user_system(self) -> Dict:
        """Migrate existing data to use the new user management system"""
        self.logger.info("Starting data migration to user management system...")
        
        migration_results = {
            'aadhaar_users_created': 0,
            'pan_users_created': 0,
            'aadhaar_records_updated': 0,
            'pan_records_updated': 0,
            'errors': []
        }
        
        # Migrate Aadhaar records
        try:
            with sqlite3.connect(self.aadhaar_db_path) as conn:
                cursor = conn.cursor()
                
                # Get all unique Aadhaar records
                cursor.execute('''
                    SELECT DISTINCT ef."Aadhaar Number", ef."Name"
                    FROM extracted_fields ef
                    WHERE ef."Aadhaar Number" IS NOT NULL 
                    AND ef."Aadhaar Number" != ''
                    AND ef."Name" IS NOT NULL
                    AND ef."Name" != ''
                ''')
                
                unique_aadhaar_records = cursor.fetchall()
                
                for aadhaar_number, name in unique_aadhaar_records:
                    try:
                        # Create or get user ID
                        user_id = self.user_manager.get_or_create_user_id(
                            aadhaar_number, name, self.aadhaar_db_path
                        )
                        
                        # Update all records with this Aadhaar number
                        cursor.execute('''
                            UPDATE aadhaar_documents 
                            SET user_id = ?
                            WHERE id IN (
                                SELECT document_id FROM extracted_fields 
                                WHERE "Aadhaar Number" = ?
                            )
                        ''', (user_id, aadhaar_number))
                        
                        cursor.execute('''
                            UPDATE extracted_fields 
                            SET user_id = ?
                            WHERE "Aadhaar Number" = ?
                        ''', (user_id, aadhaar_number))
                        
                        updated_count = cursor.rowcount
                        migration_results['aadhaar_records_updated'] += updated_count
                        migration_results['aadhaar_users_created'] += 1
                        
                    except Exception as e:
                        error_msg = f"Error migrating Aadhaar {aadhaar_number}: {e}"
                        self.logger.error(error_msg)
                        migration_results['errors'].append(error_msg)
                
                conn.commit()
                
        except Exception as e:
            error_msg = f"Error during Aadhaar migration: {e}"
            self.logger.error(error_msg)
            migration_results['errors'].append(error_msg)
        
        # Migrate PAN records
        try:
            with sqlite3.connect(self.pan_db_path) as conn:
                cursor = conn.cursor()
                
                # Get all unique PAN records
                cursor.execute('''
                    SELECT DISTINCT ef."PAN Number", ef."Name"
                    FROM extracted_fields ef
                    WHERE ef."PAN Number" IS NOT NULL 
                    AND ef."PAN Number" != ''
                    AND ef."Name" IS NOT NULL
                    AND ef."Name" != ''
                ''')
                
                unique_pan_records = cursor.fetchall()
                
                for pan_number, name in unique_pan_records:
                    try:
                        # For PAN records, we need to check if user already exists with Aadhaar
                        # For now, create separate user IDs for PAN records
                        user_id = self.user_manager.generate_user_id()
                        
                        # Create user record in PAN database
                        cursor.execute('''
                            INSERT OR IGNORE INTO users (user_id, aadhaar_number, primary_name, document_count)
                            VALUES (?, ?, ?, 1)
                        ''', (user_id, '', name))  # Empty Aadhaar for PAN-only users
                        
                        # Update all records with this PAN number
                        cursor.execute('''
                            UPDATE pan_documents 
                            SET user_id = ?
                            WHERE id IN (
                                SELECT document_id FROM extracted_fields 
                                WHERE "PAN Number" = ?
                            )
                        ''', (user_id, pan_number))
                        
                        cursor.execute('''
                            UPDATE extracted_fields 
                            SET user_id = ?
                            WHERE "PAN Number" = ?
                        ''', (user_id, pan_number))
                        
                        updated_count = cursor.rowcount
                        migration_results['pan_records_updated'] += updated_count
                        migration_results['pan_users_created'] += 1
                        
                    except Exception as e:
                        error_msg = f"Error migrating PAN {pan_number}: {e}"
                        self.logger.error(error_msg)
                        migration_results['errors'].append(error_msg)
                
                conn.commit()
                
        except Exception as e:
            error_msg = f"Error during PAN migration: {e}"
            self.logger.error(error_msg)
            migration_results['errors'].append(error_msg)
        
        operation_log = {
            'operation': 'user_system_migration',
            'timestamp': datetime.now().isoformat(),
            'results': migration_results
        }
        self.migration_log['operations'].append(operation_log)
        
        return migration_results
    
    def apply_database_constraints(self) -> Dict:
        """Apply unique constraints after data cleanup"""
        self.logger.info("Applying database constraints...")
        
        constraint_results = {
            'aadhaar_constraints_applied': False,
            'pan_constraints_applied': False,
            'errors': []
        }
        
        try:
            # Apply Aadhaar constraints
            if self.schema_manager.add_unique_constraints(
                self.aadhaar_db_path, 'extracted_fields', 'Aadhaar Number'
            ):
                constraint_results['aadhaar_constraints_applied'] = True
                self.logger.info("Aadhaar unique constraints applied successfully")
            else:
                constraint_results['errors'].append("Failed to apply Aadhaar constraints")
            
            # Apply PAN constraints
            if self.schema_manager.add_unique_constraints(
                self.pan_db_path, 'extracted_fields', 'PAN Number'
            ):
                constraint_results['pan_constraints_applied'] = True
                self.logger.info("PAN unique constraints applied successfully")
            else:
                constraint_results['errors'].append("Failed to apply PAN constraints")
                
        except Exception as e:
            error_msg = f"Error applying constraints: {e}"
            self.logger.error(error_msg)
            constraint_results['errors'].append(error_msg)
        
        operation_log = {
            'operation': 'apply_constraints',
            'timestamp': datetime.now().isoformat(),
            'results': constraint_results
        }
        self.migration_log['operations'].append(operation_log)
        
        return constraint_results
    
    def verify_migration_integrity(self) -> Dict:
        """Verify data integrity after migration"""
        self.logger.info("Verifying migration integrity...")
        
        integrity_results = {
            'aadhaar_duplicates_remaining': 0,
            'pan_duplicates_remaining': 0,
            'orphaned_records': 0,
            'constraint_violations': 0,
            'user_id_coverage': {},
            'issues': []
        }
        
        try:
            # Check for remaining duplicates
            remaining_aadhaar_dups = self.identifier.scan_aadhaar_duplicates()
            remaining_pan_dups = self.identifier.scan_pan_duplicates()
            
            integrity_results['aadhaar_duplicates_remaining'] = len(remaining_aadhaar_dups)
            integrity_results['pan_duplicates_remaining'] = len(remaining_pan_dups)
            
            if remaining_aadhaar_dups:
                integrity_results['issues'].append(f"Found {len(remaining_aadhaar_dups)} remaining Aadhaar duplicate groups")
            
            if remaining_pan_dups:
                integrity_results['issues'].append(f"Found {len(remaining_pan_dups)} remaining PAN duplicate groups")
            
            # Check user ID coverage
            for db_path, db_name in [(self.aadhaar_db_path, 'aadhaar'), (self.pan_db_path, 'pan')]:
                try:
                    with sqlite3.connect(db_path) as conn:
                        cursor = conn.cursor()
                        
                        # Count total records
                        cursor.execute('SELECT COUNT(*) FROM extracted_fields')
                        total_records = cursor.fetchone()[0]
                        
                        # Count records with user_id
                        cursor.execute('SELECT COUNT(*) FROM extracted_fields WHERE user_id IS NOT NULL')
                        records_with_user_id = cursor.fetchone()[0]
                        
                        coverage_percentage = (records_with_user_id / total_records * 100) if total_records > 0 else 0
                        
                        integrity_results['user_id_coverage'][db_name] = {
                            'total_records': total_records,
                            'records_with_user_id': records_with_user_id,
                            'coverage_percentage': coverage_percentage
                        }
                        
                        if coverage_percentage < 100:
                            integrity_results['issues'].append(f"{db_name} database has {100-coverage_percentage:.1f}% records without user_id")
                
                except Exception as e:
                    integrity_results['issues'].append(f"Error checking {db_name} user ID coverage: {e}")
            
        except Exception as e:
            error_msg = f"Error during integrity verification: {e}"
            self.logger.error(error_msg)
            integrity_results['issues'].append(error_msg)
        
        operation_log = {
            'operation': 'verify_integrity',
            'timestamp': datetime.now().isoformat(),
            'results': integrity_results
        }
        self.migration_log['operations'].append(operation_log)
        
        return integrity_results
    
    def run_complete_migration(self, dry_run: bool = False) -> Dict:
        """Run complete migration process"""
        self.logger.info(f"Starting complete migration process (dry_run={dry_run})...")
        
        migration_results = {
            'start_time': self.migration_log['start_time'],
            'dry_run': dry_run,
            'steps_completed': [],
            'steps_failed': [],
            'backups_created': [],
            'final_status': 'in_progress'
        }
        
        try:
            # Step 1: Create backups
            if not dry_run:
                self.logger.info("Step 1: Creating backups...")
                aadhaar_backup = self.create_migration_backup(self.aadhaar_db_path)
                pan_backup = self.create_migration_backup(self.pan_db_path)
                migration_results['backups_created'] = [aadhaar_backup, pan_backup]
                migration_results['steps_completed'].append('create_backups')
            
            # Step 2: Schema updates
            if not dry_run:
                self.logger.info("Step 2: Updating database schemas...")
                if self.schema_manager.migrate_all_databases():
                    migration_results['steps_completed'].append('schema_updates')
                else:
                    migration_results['steps_failed'].append('schema_updates')
                    raise MigrationError("schema_updates", "multiple databases")
            
            # Step 3: Clean up duplicates
            self.logger.info("Step 3: Cleaning up duplicate records...")
            aadhaar_cleanup = self.cleanup_aadhaar_duplicates(dry_run)
            pan_cleanup = self.cleanup_pan_duplicates(dry_run)
            
            migration_results['aadhaar_cleanup'] = aadhaar_cleanup
            migration_results['pan_cleanup'] = pan_cleanup
            migration_results['steps_completed'].append('cleanup_duplicates')
            
            # Step 4: Migrate to user system
            if not dry_run:
                self.logger.info("Step 4: Migrating to user management system...")
                user_migration = self.migrate_existing_data_to_user_system()
                migration_results['user_migration'] = user_migration
                migration_results['steps_completed'].append('user_migration')
            
            # Step 5: Apply constraints
            if not dry_run:
                self.logger.info("Step 5: Applying database constraints...")
                constraint_results = self.apply_database_constraints()
                migration_results['constraint_application'] = constraint_results
                migration_results['steps_completed'].append('apply_constraints')
            
            # Step 6: Verify integrity
            self.logger.info("Step 6: Verifying migration integrity...")
            integrity_results = self.verify_migration_integrity()
            migration_results['integrity_verification'] = integrity_results
            migration_results['steps_completed'].append('verify_integrity')
            
            # Determine final status
            if len(migration_results['steps_failed']) == 0:
                if integrity_results.get('issues'):
                    migration_results['final_status'] = 'completed_with_warnings'
                else:
                    migration_results['final_status'] = 'completed_successfully'
            else:
                migration_results['final_status'] = 'completed_with_errors'
            
        except Exception as e:
            error_msg = f"Migration failed: {e}"
            self.logger.error(error_msg)
            migration_results['final_status'] = 'failed'
            migration_results['error'] = error_msg
            self.migration_log['errors'].append(error_msg)
        
        # Update migration log
        self.migration_log['end_time'] = datetime.now().isoformat()
        self.migration_log['final_results'] = migration_results
        
        return migration_results
    
    def save_migration_report(self, filename: str = None) -> str:
        """Save detailed migration report"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"migration_report_{timestamp}.json"
        
        filepath = self.backup_dir / filename
        
        try:
            with open(filepath, 'w') as f:
                json.dump(self.migration_log, f, indent=2, default=str)
            
            self.logger.info(f"Migration report saved: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Error saving migration report: {e}")
            return ""

def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(description='Clean up duplicate data and migrate to user management system')
    parser.add_argument('--aadhaar-db', default='aadhaar_documents.db', help='Path to Aadhaar database')
    parser.add_argument('--pan-db', default='pan_documents.db', help='Path to PAN database')
    parser.add_argument('--backup-dir', default='migration_backups', help='Backup directory')
    parser.add_argument('--dry-run', action='store_true', help='Perform dry run without making changes')
    parser.add_argument('--cleanup-only', action='store_true', help='Only clean up duplicates, skip migration')
    parser.add_argument('--save-report', action='store_true', help='Save detailed migration report')
    
    args = parser.parse_args()
    
    # Create migrator
    migrator = DataCleanupMigrator(
        aadhaar_db_path=args.aadhaar_db,
        pan_db_path=args.pan_db,
        backup_dir=args.backup_dir
    )
    
    if args.cleanup_only:
        # Only run cleanup
        print("🧹 Running duplicate cleanup only...")
        aadhaar_result = migrator.cleanup_aadhaar_duplicates(args.dry_run)
        pan_result = migrator.cleanup_pan_duplicates(args.dry_run)
        
        print(f"Aadhaar cleanup: {aadhaar_result}")
        print(f"PAN cleanup: {pan_result}")
    else:
        # Run complete migration
        print("🚀 Running complete migration process...")
        results = migrator.run_complete_migration(args.dry_run)
        
        print(f"\nMigration Status: {results['final_status']}")
        print(f"Steps Completed: {', '.join(results['steps_completed'])}")
        if results['steps_failed']:
            print(f"Steps Failed: {', '.join(results['steps_failed'])}")
        
        if args.save_report:
            report_path = migrator.save_migration_report()
            print(f"Migration report saved: {report_path}")

if __name__ == "__main__":
    main()