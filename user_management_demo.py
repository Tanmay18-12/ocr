#!/usr/bin/env python3
"""
Complete User Management System Demo
Demonstrates the full integration of unique user management with document extraction
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

# Add user_management to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'user_management'))

from user_management.database_schema_manager import DatabaseSchemaManager
from user_management.duplicate_data_identifier import DuplicateDataIdentifier
from user_management.data_cleanup_migrator import DataCleanupMigrator
from user_management.user_id_manager import UserIDManager
from user_management.duplicate_prevention_service import DuplicatePreventionService

# Import enhanced extraction tools
from aadhaar_extractor_with_sql import AadhaarExtractionTool
from pan_extractor_with_sql import PANExtractionTool

class UserManagementSystem:
    """Complete user management system orchestrator"""
    
    def __init__(self, aadhaar_db_path: str = "aadhaar_documents.db", 
                 pan_db_path: str = "pan_documents.db"):
        self.aadhaar_db_path = aadhaar_db_path
        self.pan_db_path = pan_db_path
        
        # Initialize components
        self.schema_manager = DatabaseSchemaManager(aadhaar_db_path, pan_db_path)
        self.user_manager = UserIDManager(aadhaar_db_path, pan_db_path)
        self.duplicate_service = DuplicatePreventionService(aadhaar_db_path, pan_db_path)
        self.identifier = DuplicateDataIdentifier(aadhaar_db_path, pan_db_path)
        self.migrator = DataCleanupMigrator(aadhaar_db_path, pan_db_path)
        
        # Initialize extraction tools
        self.aadhaar_extractor = AadhaarExtractionTool(aadhaar_db_path)
        self.pan_extractor = PANExtractionTool(pan_db_path, aadhaar_db_path)
    
    def setup_system(self, force_migration: bool = False) -> dict:
        """Set up the complete user management system"""
        print("🚀 Setting up User Management System...")
        print("=" * 60)
        
        setup_results = {
            'schema_migration': False,
            'data_cleanup': False,
            'constraint_application': False,
            'system_ready': False,
            'errors': []
        }
        
        try:
            # Step 1: Check if migration is needed
            print("📋 Step 1: Checking system status...")
            
            aadhaar_verification = self.schema_manager.verify_schema_changes(self.aadhaar_db_path)
            pan_verification = self.schema_manager.verify_schema_changes(self.pan_db_path)
            
            needs_migration = (
                not aadhaar_verification.get('users_table_exists', False) or
                not pan_verification.get('users_table_exists', False) or
                force_migration
            )
            
            if needs_migration:
                print("⚠️  System needs migration")
                
                # Step 2: Run schema migration
                print("\n📋 Step 2: Running schema migration...")
                if self.schema_manager.migrate_all_databases():
                    setup_results['schema_migration'] = True
                    print("✅ Schema migration completed")
                else:
                    setup_results['errors'].append("Schema migration failed")
                    print("❌ Schema migration failed")
                
                # Step 3: Clean up duplicates
                print("\n📋 Step 3: Cleaning up duplicate data...")
                try:
                    migration_result = self.migrator.run_complete_migration(dry_run=False)
                    if migration_result['final_status'] in ['completed_successfully', 'completed_with_warnings']:
                        setup_results['data_cleanup'] = True
                        print("✅ Data cleanup completed")
                    else:
                        setup_results['errors'].append("Data cleanup failed")
                        print("❌ Data cleanup failed")
                except Exception as e:
                    setup_results['errors'].append(f"Data cleanup error: {e}")
                    print(f"❌ Data cleanup error: {e}")
                
            else:
                print("✅ System already migrated")
                setup_results['schema_migration'] = True
                setup_results['data_cleanup'] = True
            
            # Step 4: Verify system is ready
            print("\n📋 Step 4: Verifying system readiness...")
            
            final_aadhaar_verification = self.schema_manager.verify_schema_changes(self.aadhaar_db_path)
            final_pan_verification = self.schema_manager.verify_schema_changes(self.pan_db_path)
            
            system_ready = (
                final_aadhaar_verification.get('users_table_exists', False) and
                final_pan_verification.get('users_table_exists', False)
            )
            
            setup_results['system_ready'] = system_ready
            
            if system_ready:
                print("✅ User Management System is ready!")
            else:
                print("❌ System setup incomplete")
                setup_results['errors'].append("System verification failed")
            
        except Exception as e:
            error_msg = f"System setup failed: {e}"
            setup_results['errors'].append(error_msg)
            print(f"❌ {error_msg}")
        
        print("\n" + "=" * 60)
        return setup_results
    
    def process_document(self, file_path: str, document_type: str = None) -> dict:
        """Process a document with full user management integration"""
        print(f"📄 Processing document: {file_path}")
        
        if not os.path.exists(file_path):
            return {
                'status': 'error',
                'error': f'File not found: {file_path}'
            }
        
        # Auto-detect document type if not specified
        if not document_type:
            if 'aadhaar' in file_path.lower() or 'aadhar' in file_path.lower():
                document_type = 'AADHAAR'
            elif 'pan' in file_path.lower():
                document_type = 'PAN'
            else:
                document_type = 'AADHAAR'  # Default
        
        try:
            if document_type.upper() == 'AADHAAR':
                result = self.aadhaar_extractor.extract_and_store(file_path)
            elif document_type.upper() == 'PAN':
                result = self.pan_extractor.extract_and_store(file_path)
            else:
                return {
                    'status': 'error',
                    'error': f'Unsupported document type: {document_type}'
                }
            
            return result
            
        except Exception as e:
            return {
                'status': 'error',
                'error': f'Processing failed: {e}'
            }
    
    def get_system_statistics(self) -> dict:
        """Get comprehensive system statistics"""
        print("📊 Generating system statistics...")
        
        stats = {
            'timestamp': datetime.now().isoformat(),
            'user_statistics': {},
            'data_quality_metrics': {},
            'duplicate_report': {},
            'database_info': {}
        }
        
        try:
            # User statistics
            stats['user_statistics'] = self.user_manager.get_user_statistics()
            
            # Data quality metrics
            stats['data_quality_metrics'] = self.duplicate_service.get_data_quality_metrics()
            
            # Duplicate report summary
            duplicate_report = self.identifier.run_full_scan()
            stats['duplicate_report'] = duplicate_report['summary']
            
            # Database verification
            stats['database_info'] = {
                'aadhaar_db': self.schema_manager.verify_schema_changes(self.aadhaar_db_path),
                'pan_db': self.schema_manager.verify_schema_changes(self.pan_db_path)
            }
            
        except Exception as e:
            stats['error'] = f"Failed to generate statistics: {e}"
        
        return stats
    
    def check_document_exists(self, document_number: str, document_type: str) -> dict:
        """Check if a document already exists in the system"""
        try:
            if document_type.upper() == 'AADHAAR':
                return self.aadhaar_extractor.check_aadhaar_exists(document_number)
            elif document_type.upper() == 'PAN':
                return self.pan_extractor.check_pan_exists(document_number)
            else:
                return {
                    'status': 'error',
                    'error': f'Unsupported document type: {document_type}'
                }
        except Exception as e:
            return {
                'status': 'error',
                'error': f'Check failed: {e}'
            }
    
    def get_user_documents(self, user_id: str) -> dict:
        """Get all documents for a user across both databases"""
        try:
            result = {
                'user_id': user_id,
                'aadhaar_documents': [],
                'pan_documents': [],
                'total_documents': 0
            }
            
            # Get Aadhaar documents
            aadhaar_docs = self.aadhaar_extractor.get_user_documents(user_id)
            if aadhaar_docs.get('status') == 'success':
                result['aadhaar_documents'] = aadhaar_docs.get('documents', [])
            
            # Get PAN documents
            pan_docs = self.pan_extractor.get_user_documents(user_id)
            if pan_docs.get('status') == 'success':
                result['pan_documents'] = pan_docs.get('documents', [])
            
            result['total_documents'] = len(result['aadhaar_documents']) + len(result['pan_documents'])
            
            return result
            
        except Exception as e:
            return {
                'status': 'error',
                'error': f'Failed to get user documents: {e}'
            }
    
    def run_data_quality_check(self) -> dict:
        """Run comprehensive data quality check"""
        print("🔍 Running data quality check...")
        
        try:
            # Generate duplicate report
            duplicate_report = self.identifier.run_full_scan()
            
            # Get data quality metrics
            quality_metrics = self.duplicate_service.get_data_quality_metrics()
            
            return {
                'status': 'success',
                'duplicate_report': duplicate_report,
                'quality_metrics': quality_metrics,
                'recommendations': self._generate_recommendations(duplicate_report, quality_metrics)
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': f'Data quality check failed: {e}'
            }
    
    def _generate_recommendations(self, duplicate_report: dict, quality_metrics: dict) -> list:
        """Generate recommendations based on data quality analysis"""
        recommendations = []
        
        # Check for duplicates
        aadhaar_duplicates = duplicate_report['summary'].get('aadhaar_duplicate_groups', 0)
        pan_duplicates = duplicate_report['summary'].get('pan_duplicate_groups', 0)
        
        if aadhaar_duplicates > 0:
            recommendations.append(f"Found {aadhaar_duplicates} Aadhaar duplicate groups. Consider running data cleanup.")
        
        if pan_duplicates > 0:
            recommendations.append(f"Found {pan_duplicates} PAN duplicate groups. Consider running data cleanup.")
        
        # Check data quality metrics
        aadhaar_metrics = quality_metrics.get('aadhaar_metrics', {})
        if aadhaar_metrics.get('duplicate_percentage', 0) > 5:
            recommendations.append("High Aadhaar duplicate percentage detected. Run duplicate cleanup.")
        
        pan_metrics = quality_metrics.get('pan_metrics', {})
        if pan_metrics.get('duplicate_percentage', 0) > 5:
            recommendations.append("High PAN duplicate percentage detected. Run duplicate cleanup.")
        
        if not recommendations:
            recommendations.append("Data quality looks good. No immediate action required.")
        
        return recommendations

def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(description='User Management System Demo')
    parser.add_argument('--setup', action='store_true', help='Set up the user management system')
    parser.add_argument('--force-migration', action='store_true', help='Force system migration')
    parser.add_argument('--process', help='Process a document file')
    parser.add_argument('--document-type', choices=['AADHAAR', 'PAN'], help='Document type')
    parser.add_argument('--check-exists', help='Check if document number exists')
    parser.add_argument('--stats', action='store_true', help='Show system statistics')
    parser.add_argument('--quality-check', action='store_true', help='Run data quality check')
    parser.add_argument('--user-docs', help='Get documents for user ID')
    parser.add_argument('--aadhaar-db', default='aadhaar_documents.db', help='Aadhaar database path')
    parser.add_argument('--pan-db', default='pan_documents.db', help='PAN database path')
    
    args = parser.parse_args()
    
    # Initialize system
    system = UserManagementSystem(args.aadhaar_db, args.pan_db)
    
    print("🎯 User Management System Demo")
    print("=" * 50)
    
    try:
        if args.setup:
            # Set up system
            setup_result = system.setup_system(args.force_migration)
            print(f"\nSetup Result: {json.dumps(setup_result, indent=2)}")
            
        elif args.process:
            # Process document
            result = system.process_document(args.process, args.document_type)
            print(f"\nProcessing Result:")
            print(json.dumps(result, indent=2))
            
        elif args.check_exists:
            # Check document existence
            doc_type = args.document_type or 'AADHAAR'
            result = system.check_document_exists(args.check_exists, doc_type)
            print(f"\nExistence Check Result:")
            print(json.dumps(result, indent=2))
            
        elif args.stats:
            # Show statistics
            stats = system.get_system_statistics()
            print(f"\nSystem Statistics:")
            print(json.dumps(stats, indent=2))
            
        elif args.quality_check:
            # Run quality check
            quality_result = system.run_data_quality_check()
            print(f"\nData Quality Check Result:")
            print(json.dumps(quality_result, indent=2))
            
        elif args.user_docs:
            # Get user documents
            docs = system.get_user_documents(args.user_docs)
            print(f"\nUser Documents:")
            print(json.dumps(docs, indent=2))
            
        else:
            # Interactive demo
            print("\n🎮 Interactive Demo Mode")
            print("Available commands:")
            print("1. Setup system")
            print("2. Check system statistics")
            print("3. Run data quality check")
            print("4. Process sample document (if available)")
            
            # Auto-setup if needed
            print("\n🔧 Auto-checking system setup...")
            setup_result = system.setup_system()
            
            if setup_result['system_ready']:
                print("✅ System is ready!")
                
                # Show statistics
                print("\n📊 Current System Statistics:")
                stats = system.get_system_statistics()
                
                user_stats = stats.get('user_statistics', {})
                print(f"  Total Users: {user_stats.get('total_users', 0)}")
                print(f"  Aadhaar DB Users: {user_stats.get('aadhaar_db_users', 0)}")
                print(f"  PAN DB Users: {user_stats.get('pan_db_users', 0)}")
                
                quality_metrics = stats.get('data_quality_metrics', {})
                aadhaar_metrics = quality_metrics.get('aadhaar_metrics', {})
                pan_metrics = quality_metrics.get('pan_metrics', {})
                
                if aadhaar_metrics:
                    print(f"  Aadhaar Records: {aadhaar_metrics.get('total_records', 0)} "
                          f"(Duplicates: {aadhaar_metrics.get('duplicate_percentage', 0):.1f}%)")
                
                if pan_metrics:
                    print(f"  PAN Records: {pan_metrics.get('total_records', 0)} "
                          f"(Duplicates: {pan_metrics.get('duplicate_percentage', 0):.1f}%)")
                
                # Run quality check
                print("\n🔍 Running data quality check...")
                quality_result = system.run_data_quality_check()
                
                if quality_result.get('status') == 'success':
                    recommendations = quality_result.get('recommendations', [])
                    print("📋 Recommendations:")
                    for rec in recommendations:
                        print(f"  • {rec}")
                
            else:
                print("❌ System setup failed!")
                print("Errors:", setup_result.get('errors', []))
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Demo completed!")

if __name__ == "__main__":
    main()