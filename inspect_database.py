#!/usr/bin/env python3
"""
Inspect the validator database to show structure and content
"""

import sqlite3
import json

def inspect_database(db_path="validator_demo.db"):
    """Inspect the database structure and content"""
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            print("="*80)
            print("🗄️ DATABASE INSPECTION")
            print("="*80)
            
            # Show all tables
            print("\n📋 DATABASE TABLES:")
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            for table in tables:
                print(f"  - {table[0]}")
            
            # Show documents table schema
            print("\n📊 DOCUMENTS TABLE SCHEMA:")
            cursor.execute("PRAGMA table_info(documents)")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  {col[1]} ({col[2]}) - {'PRIMARY KEY' if col[5] else 'NOT NULL' if col[3] else 'NULLABLE'}")
            
            # Show validation_results table schema
            print("\n📊 VALIDATION_RESULTS TABLE SCHEMA:")
            cursor.execute("PRAGMA table_info(validation_results)")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  {col[1]} ({col[2]}) - {'PRIMARY KEY' if col[5] else 'NOT NULL' if col[3] else 'NULLABLE'}")
            
            # Show documents table content
            print("\n📋 DOCUMENTS TABLE CONTENT:")
            cursor.execute("SELECT * FROM documents")
            docs = cursor.fetchall()
            
            if docs:
                print("  Columns: id | file_path | document_type | validation_status | is_valid | overall_score | extracted_data | created_at")
                print("  " + "-"*120)
                for doc in docs:
                    extracted_data = doc[6][:50] + "..." if len(str(doc[6])) > 50 else doc[6]
                    print(f"  {doc[0]} | {doc[1]} | {doc[2]} | {doc[3]} | {doc[4]} | {doc[5]} | {extracted_data} | {doc[7]}")
            else:
                print("  No documents found")
            
            # Show validation_results table content
            print("\n📊 VALIDATION_RESULTS TABLE CONTENT:")
            cursor.execute("SELECT * FROM validation_results")
            results = cursor.fetchall()
            
            if results:
                print("  Columns: id | doc_id | aadhaar_valid | aadhaar_reason | name_valid | name_reason | dob_valid | dob_reason | gender_valid | gender_reason | addr_valid | addr_reason | timestamp")
                print("  " + "-"*160)
                for result in results:
                    print(f"  {result[0]} | {result[1]} | {result[2]} | {result[3]} | {result[4]} | {result[5]} | {result[6]} | {result[7]} | {result[8]} | {result[9]} | {result[10]} | {result[11]} | {result[12]}")
            else:
                print("  No validation results found")
            
            # Show summary statistics
            print("\n📈 SUMMARY STATISTICS:")
            
            cursor.execute("SELECT COUNT(*) FROM documents")
            total_docs = cursor.fetchone()[0]
            print(f"  Total Documents: {total_docs}")
            
            cursor.execute("SELECT COUNT(*) FROM documents WHERE is_valid = 1")
            valid_docs = cursor.fetchone()[0]
            print(f"  Valid Documents: {valid_docs}")
            
            cursor.execute("SELECT COUNT(*) FROM documents WHERE is_valid = 0")
            invalid_docs = cursor.fetchone()[0]
            print(f"  Invalid Documents: {invalid_docs}")
            
            cursor.execute("SELECT AVG(overall_score) FROM documents")
            avg_score = cursor.fetchone()[0]
            print(f"  Average Validation Score: {avg_score:.2f}" if avg_score else "  Average Validation Score: N/A")
            
            # Show field-level validation stats
            print("\n📊 FIELD-LEVEL VALIDATION STATISTICS:")
            
            field_stats = [
                ("Aadhaar Number", "aadhaar_number_valid"),
                ("Name", "name_valid"),
                ("DOB", "dob_valid"),
                ("Gender", "gender_valid"),
                ("Address", "address_valid")
            ]
            
            for field_name, column_name in field_stats:
                cursor.execute(f"SELECT COUNT(*) FROM validation_results WHERE {column_name} = 1")
                valid_count = cursor.fetchone()[0]
                
                cursor.execute(f"SELECT COUNT(*) FROM validation_results WHERE {column_name} = 0")
                invalid_count = cursor.fetchone()[0]
                
                total_field = valid_count + invalid_count
                valid_percentage = (valid_count / total_field * 100) if total_field > 0 else 0
                
                print(f"  {field_name}: {valid_count}/{total_field} valid ({valid_percentage:.1f}%)")
            
            print("\n✅ Database inspection completed")
            
    except Exception as e:
        print(f"❌ Error inspecting database: {e}")

if __name__ == "__main__":
    inspect_database()