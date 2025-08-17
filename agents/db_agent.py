

import sqlite3
import json
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from pathlib import Path
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import BaseTool
from config import Config
from utils.logging_config import setup_logging
import re

class DynamicDatabaseTool(BaseTool):
    """Tool for dynamic database operations with automatic table creation"""
    
    name: str = "Dynamic Database Operations"
    description: str = "Performs database operations with automatic table creation based on data structure"
    
    def __init__(self, db_path: str = "documents.db"):
        super().__init__()
        self.db_path = db_path
        self.logger = setup_logging()
        self._init_database()
    
    def _init_database(self):
        """Initialize database with core tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Core documents table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS documents (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        file_path TEXT NOT NULL,
                        document_type TEXT NOT NULL,
                        extraction_timestamp TEXT NOT NULL,
                        validation_status TEXT NOT NULL,
                        is_valid BOOLEAN NOT NULL,
                        quality_score REAL,
                        completeness_score REAL,
                        raw_data TEXT,
                        processed_data TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Processing logs table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS processing_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        document_id INTEGER,
                        agent_name TEXT NOT NULL,
                        action TEXT NOT NULL,
                        status TEXT NOT NULL,
                        details TEXT,
                        timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (document_id) REFERENCES documents (id)
                    )
                ''')
                
                # Table metadata for tracking dynamic tables
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS table_metadata (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        table_name TEXT UNIQUE NOT NULL,
                        columns TEXT NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        last_used TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                self.logger.info("Database initialized successfully")
                
        except Exception as e:
            self.logger.error(f"Database initialization error: {e}")
            raise
    
    def _run(self, operation: str) -> str:
        """Execute database operations"""
        try:
            if operation.startswith("STORE_VALIDATION:"):
                return self._store_validation_result(operation[17:])
            elif operation.startswith("GET_DOCUMENT:"):
                return self._get_document(operation[13:])
            elif operation.startswith("UPDATE_DOCUMENT:"):
                return self._update_document(operation[16:])
            elif operation.startswith("LOG_PROCESSING:"):
                return self._log_processing(operation[15:])
            elif operation.startswith("CREATE_DYNAMIC_TABLE:"):
                return self._create_dynamic_table(operation[21:])
            else:
                return f"Unknown operation: {operation}"
        except Exception as e:
            self.logger.error(f"Database operation error: {e}")
            return f"Database error: {str(e)}"
    
    def _create_dynamic_table(self, data_json: str) -> str:
        """Create a dynamic table based on JSON data structure"""
        try:
            data = json.loads(data_json)
            table_name = data.get('table_name', 'validation_results')
            columns_data = data.get('columns', {})
            
            # Generate table name if not provided
            if table_name == 'validation_results':
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                table_name = f"validation_results_{timestamp}"
            
            # Create column definitions
            columns = []
            columns.append("id INTEGER PRIMARY KEY AUTOINCREMENT")
            columns.append("document_id INTEGER")
            columns.append("validation_timestamp TEXT DEFAULT CURRENT_TIMESTAMP")
            
            # Add dynamic columns based on validation data
            for column_name, column_type in columns_data.items():
                # Sanitize column name
                safe_column_name = self._sanitize_column_name(column_name)
                
                # Determine SQL type based on data type
                sql_type = self._get_sql_type(column_type)
                columns.append(f"{safe_column_name} {sql_type}")
            
            # Create table
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                create_sql = f'''
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        {', '.join(columns)}
                    )
                '''
                
                cursor.execute(create_sql)
                
                # Store table metadata
                cursor.execute('''
                    INSERT OR REPLACE INTO table_metadata (table_name, columns, last_used)
                    VALUES (?, ?, ?)
                ''', (table_name, json.dumps(columns_data), datetime.now().isoformat()))
                
                conn.commit()
                
                return json.dumps({
                    "status": "success",
                    "table_name": table_name,
                    "message": f"Dynamic table {table_name} created successfully"
                })
                
        except Exception as e:
            self.logger.error(f"Error creating dynamic table: {e}")
            return json.dumps({
                "status": "error",
                "error": str(e)
            })
    
    def _store_validation_result(self, data_json: str) -> str:
        """Store validation result in dynamic table"""
        try:
            data = json.loads(data_json)
            
            # First, store in main documents table
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO documents (
                        file_path, document_type, extraction_timestamp, 
                        validation_status, is_valid, quality_score, completeness_score,
                        raw_data, processed_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data.get('file_path', ''),
                    data.get('document_type', 'UNKNOWN'),
                    data.get('extraction_timestamp', datetime.now().isoformat()),
                    data.get('validation_status', 'UNKNOWN'),
                    data.get('is_valid', False),
                    data.get('overall_score', 0.0),
                    data.get('completeness_score', 0.0),
                    json.dumps(data.get('extracted_data', {})),
                    json.dumps(data)
                ))
                
                document_id = cursor.lastrowid
                
                # Get or create dynamic table for validation details
                validation_details = data.get('validation_details', {})
                if validation_details:
                    table_name = self._get_or_create_validation_table(validation_details)
                    
                    # Prepare data for dynamic table
                    insert_data = {
                        'document_id': document_id,
                        'validation_timestamp': datetime.now().isoformat()
                    }
                    
                    # Add validation details
                    for field_name, field_data in validation_details.items():
                        safe_field_name = self._sanitize_column_name(field_name)
                        if isinstance(field_data, dict):
                            insert_data[safe_field_name] = json.dumps(field_data)
                        else:
                            insert_data[safe_field_name] = str(field_data)
                    
                    # Insert into dynamic table
                    columns = list(insert_data.keys())
                    placeholders = ', '.join(['?' for _ in columns])
                    values = list(insert_data.values())
                    
                    cursor.execute(f'''
                        INSERT INTO {table_name} ({', '.join(columns)})
                        VALUES ({placeholders})
                    ''', values)
                
                conn.commit()
                
                return json.dumps({
                    "status": "success",
                    "document_id": document_id,
                    "table_name": table_name if validation_details else None,
                    "message": "Validation result stored successfully"
                })
                
        except Exception as e:
            self.logger.error(f"Error storing validation result: {e}")
            return json.dumps({
                "status": "error",
                "error": str(e)
            })
    
    def _get_or_create_validation_table(self, validation_details: Dict[str, Any]) -> str:
        """Get existing validation table or create new one"""
        try:
            # Analyze validation details structure
            columns_data = {}
            for field_name, field_data in validation_details.items():
                if isinstance(field_data, dict):
                    columns_data[field_name] = 'TEXT'  # Store as JSON string
                else:
                    columns_data[field_name] = 'TEXT'
            
            # Check if suitable table exists
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT table_name FROM table_metadata 
                    WHERE columns = ? 
                    ORDER BY last_used DESC 
                    LIMIT 1
                ''', (json.dumps(columns_data),))
                
                result = cursor.fetchone()
                if result:
                    # Update last_used
                    cursor.execute('''
                        UPDATE table_metadata 
                        SET last_used = ? 
                        WHERE table_name = ?
                    ''', (datetime.now().isoformat(), result[0]))
                    conn.commit()
                    return result[0]
                
                # Create new table
                table_data = {
                    'table_name': 'validation_results',
                    'columns': columns_data
                }
                
                create_result = json.loads(self._create_dynamic_table(json.dumps(table_data)))
                if create_result['status'] == 'success':
                    return create_result['table_name']
                else:
                    raise Exception(f"Failed to create table: {create_result['error']}")
                
        except Exception as e:
            self.logger.error(f"Error getting or creating validation table: {e}")
            raise
    
    def _sanitize_column_name(self, column_name: str) -> str:
        """Sanitize column name for SQL"""
        # Remove special characters and replace spaces with underscores
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', column_name)
        # Ensure it doesn't start with a number
        if sanitized and sanitized[0].isdigit():
            sanitized = 'col_' + sanitized
        return sanitized.lower()
    
    def _get_sql_type(self, data_type: str) -> str:
        """Get SQL type based on data type"""
        type_mapping = {
            'TEXT': 'TEXT',
            'INTEGER': 'INTEGER',
            'REAL': 'REAL',
            'BOOLEAN': 'BOOLEAN',
            'JSON': 'TEXT'
        }
        return type_mapping.get(data_type.upper(), 'TEXT')
    
    def _get_document(self, document_id: str) -> str:
        """Retrieve document data from the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM documents WHERE id = ?
                ''', (document_id,))
                
                doc_record = cursor.fetchone()
                if not doc_record:
                    return json.dumps({"status": "error", "message": "Document not found"})
                
                document_data = {
                    "id": doc_record[0],
                    "file_path": doc_record[1],
                    "document_type": doc_record[2],
                    "extraction_timestamp": doc_record[3],
                    "validation_status": doc_record[4],
                    "is_valid": bool(doc_record[5]),
                    "quality_score": doc_record[6],
                    "completeness_score": doc_record[7],
                    "raw_data": json.loads(doc_record[8]) if doc_record[8] else "",
                    "processed_data": json.loads(doc_record[9]) if doc_record[9] else {}
                }
                
                return json.dumps(document_data, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error retrieving document: {e}")
            return json.dumps({"status": "error", "error": str(e)})
    
    def _update_document(self, data_json: str) -> str:
        """Update document data in the database"""
        try:
            data = json.loads(data_json)
            document_id = data.get('document_id')
            
            if not document_id:
                return json.dumps({"status": "error", "message": "Document ID required"})
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE documents SET 
                        validation_status = ?, 
                        is_valid = ?,
                        quality_score = ?, 
                        completeness_score = ?,
                        processed_data = ?
                    WHERE id = ?
                ''', (
                    data.get('validation_status'),
                    data.get('is_valid', False),
                    data.get('quality_score'),
                    data.get('completeness_score'),
                    json.dumps(data.get('processed_data', {})),
                    document_id
                ))
                
                conn.commit()
                
                return json.dumps({
                    "status": "success",
                    "message": "Document updated successfully"
                })
                
        except Exception as e:
            self.logger.error(f"Error updating document: {e}")
            return json.dumps({"status": "error", "error": str(e)})
    
    def _log_processing(self, data_json: str) -> str:
        """Log processing activities"""
        try:
            data = json.loads(data_json)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO processing_logs (
                        document_id, agent_name, action, status, details
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (
                    data.get('document_id'),
                    data.get('agent_name'),
                    data.get('action'),
                    data.get('status'),
                    json.dumps(data.get('details', {}))
                ))
                
                conn.commit()
                
                return json.dumps({
                    "status": "success",
                    "message": "Processing log stored successfully"
                })
                
        except Exception as e:
            self.logger.error(f"Error logging processing: {e}")
            return json.dumps({"status": "error", "error": str(e)})

class DatabaseAgent:
    """Enhanced agent responsible for database operations with dynamic table creation"""
    
    def __init__(self, db_path: str = "documents.db"):
        self.logger = setup_logging()
        self.db_path = db_path
        self.llm = ChatOpenAI(
            model=Config.OPENAI_MODEL,
            temperature=0.1,
            api_key=Config.OPENAI_API_KEY
        )
        self.tools = [DynamicDatabaseTool(db_path)]
        self.agent = self._create_agent()
    
    def _create_agent(self):
        """Create the database agent"""
        system_message = """You are a Database Management Agent with dynamic table creation capabilities. Your role is to:
        1. Store validation results in appropriate tables
        2. Automatically create tables based on validation data structure
        3. Retrieve document information when needed
        4. Update document records with validation results
        5. Log all processing activities
        6. Maintain data integrity and consistency
        
        Always ensure proper error handling and data validation. When storing validation results, analyze the data structure and create appropriate tables if needed."""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        agent = create_openai_functions_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=Config.AGENT_VERBOSE,
            handle_parsing_errors=True
        )
    
    def store_validation_result(self, validation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Store validation result in database with dynamic table creation"""
        try:
            self.logger.info("Database Agent: Storing validation result")
            
            # Prepare data for storage
            storage_data = {
                "file_path": validation_data.get("file_path", ""),
                "document_type": validation_data.get("document_type", "UNKNOWN"),
                "extraction_timestamp": validation_data.get("extraction_timestamp", datetime.now().isoformat()),
                "validation_status": validation_data.get("validation_status", "UNKNOWN"),
                "is_valid": validation_data.get("is_valid", False),
                "overall_score": validation_data.get("overall_score", 0.0),
                "completeness_score": validation_data.get("completeness_score", 0.0),
                "extracted_data": validation_data.get("extracted_data", {}),
                "validation_details": validation_data.get("validation_details", {})
            }
            
            operation = f"STORE_VALIDATION:{json.dumps(storage_data)}"
            result = self.agent.invoke({"input": f"Execute operation: {operation}"})
            
            self.logger.info("Database Agent: Validation result stored successfully")
            return json.loads(result["output"])
            
        except Exception as e:
            self.logger.error(f"Database Agent error: {e}")
            return {
                "status": "error",
                "error_message": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_document(self, document_id: int) -> Dict[str, Any]:
        """Retrieve document data from the database"""
        try:
            self.logger.info(f"Database Agent: Retrieving document {document_id}")
            
            operation = f"GET_DOCUMENT:{document_id}"
            result = self.agent.invoke({"input": f"Execute operation: {operation}"})
            
            return json.loads(result["output"])
            
        except Exception as e:
            self.logger.error(f"Database Agent error: {e}")
            return {
                "status": "error",
                "error_message": str(e)
            }
    
    def log_processing(self, document_id: int, agent_name: str, action: str, 
                      status: str, details: Dict[str, Any] = None) -> Dict[str, Any]:
        """Log processing activity"""
        try:
            log_data = {
                "document_id": document_id,
                "agent_name": agent_name,
                "action": action,
                "status": status,
                "details": details or {}
            }
            
            operation = f"LOG_PROCESSING:{json.dumps(log_data)}"
            result = self.agent.invoke({"input": f"Execute operation: {operation}"})
            
            return json.loads(result["output"])
            
        except Exception as e:
            self.logger.error(f"Database Agent logging error: {e}")
            return {
                "status": "error",
                "error_message": str(e)
            }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get total documents
                cursor.execute("SELECT COUNT(*) FROM documents")
                total_documents = cursor.fetchone()[0]
                
                # Get documents by validation status
                cursor.execute("SELECT validation_status, COUNT(*) FROM documents GROUP BY validation_status")
                documents_by_status = dict(cursor.fetchall())
                
                # Get valid vs invalid documents
                cursor.execute("SELECT is_valid, COUNT(*) FROM documents GROUP BY is_valid")
                validity_stats = dict(cursor.fetchall())
                
                # Get average scores
                cursor.execute("SELECT AVG(quality_score), AVG(completeness_score) FROM documents")
                avg_scores = cursor.fetchone()
                
                # Get dynamic tables
                cursor.execute("SELECT table_name, columns FROM table_metadata")
                dynamic_tables = cursor.fetchall()
                
                return {
                    "total_documents": total_documents,
                    "documents_by_status": documents_by_status,
                    "validity_stats": validity_stats,
                    "average_quality_score": avg_scores[0] or 0,
                    "average_completeness_score": avg_scores[1] or 0,
                    "dynamic_tables": [{"name": t[0], "columns": json.loads(t[1])} for t in dynamic_tables]
                }
                
        except Exception as e:
            self.logger.error(f"Error getting statistics: {e}")
            return {"error": str(e)}