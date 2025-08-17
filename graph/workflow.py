from langgraph.graph import StateGraph, END
from graph.state import DocumentState
from graph.nodes import (
    create_extraction_node,
    create_validation_node,
    create_analysis_node,
    create_finalize_node
)
from agents.document_classifier_agent import classify_document
from config import Config
import logging
import json

logger = logging.getLogger(__name__)

def create_document_processing_graph():
    """Create the document processing workflow graph with classification and routing"""
    
    # Create the graph
    workflow = StateGraph(DocumentState)
    
    # Add nodes
    workflow.add_node("extract", create_extraction_node())
    workflow.add_node("classify", classify_document_node)
    workflow.add_node("validate", create_validation_node())
    workflow.add_node("analyze", create_analysis_node())
    workflow.add_node("finalize", create_finalize_node())
    workflow.add_node("manual_review", manual_review_node)
    
    # Define the workflow edges with conditional routing
    workflow.set_entry_point("extract")
    workflow.add_edge("extract", "classify")
    
    # Conditional routing based on document type
    workflow.add_conditional_edges(
        "classify",
        route_by_document_type,
        {
            "AADHAAR": "aadhar_extractor_agent_with_sql",
            "PAN": "pan_extractor_agent_with_sql", 
            "UNKNOWN": "manual_review"
        }
    )
    
    # Add edges for different document types
    workflow.add_edge("aadhar_extractor_agent_with_sql", "validate")
    workflow.add_edge("pan_extractor_agent_with_sql", "validate")
    workflow.add_edge("manual_review", END)
    
    workflow.add_edge("validate", "analyze")
    workflow.add_edge("analyze", "finalize")
    workflow.add_edge("finalize", END)
    
    # Compile the graph
    app = workflow.compile()
    
    return app

def classify_document_node(state: DocumentState) -> DocumentState:
    """Node to classify the document type using regex patterns"""
    
    logger.info("Classifying document type...")
    
    try:
        # Get extracted text from state
        extracted_text = state.extracted_text or ""
        
        # Classify document
        classification_result = classify_document(extracted_text)
        classification_data = json.loads(classification_result)
        
        # Update state with document type
        state.document_type = classification_data.get("document_type", "UNKNOWN")
        
        logger.info(f"Document classified as: {state.document_type}")
        
        return state
        
    except Exception as e:
        logger.error(f"Error in document classification: {e}")
        state.document_type = "UNKNOWN"
        return state

def route_by_document_type(state: DocumentState) -> str:
    """Route to appropriate agent based on document type"""
    
    document_type = state.document_type or "UNKNOWN"
    
    logger.info(f"Routing document type: {document_type}")
    
    if document_type == "AADHAAR":
        return "aadhar_extractor_agent_with_sql"
    elif document_type == "PAN":
        return "pan_extractor_agent_with_sql"
    else:
        return "manual_review"

def manual_review_node(state: DocumentState) -> DocumentState:
    """Node for documents that couldn't be classified automatically"""
    
    logger.info("Document sent to manual review")
    
    # Mark for manual review
    state.validation_status = "manual_review_required"
    state.processing_log.append("Document sent to manual review - classification failed")
    
    return state

def process_document_with_graph(file_path: str) -> dict:
    """Process a single document using the LangGraph workflow"""
    
    logger.info(f"Starting LangGraph processing for: {file_path}")
    
    try:
        # Create initial state
        initial_state = DocumentState(
            file_path=file_path,
            processing_timestamp=None
        )
        
        # Create and run the graph
        app = create_document_processing_graph()
        
        # Execute the workflow
        final_state = app.invoke(initial_state)
        
        # Convert to final result format
        result = final_state.to_final_result()
        
        logger.info(f"LangGraph processing completed for: {file_path}")
        return result
        
    except Exception as e:
        logger.error(f"Error in LangGraph processing for {file_path}: {e}")
        
        # Return error result
        return {
            "processing_timestamp": None,
            "file_path": file_path,
            "document_type": "UNKNOWN",
            "validation_status": "failed",
            "extraction_confidence": 0.0,
            "overall_score": 0.0,
            "errors": [f"LangGraph processing error: {str(e)}"],
            "warnings": [],
            "extracted_data": {},
            "validation_details": {},
            "processing_log": [f"Error: {str(e)}"]
        }

def process_batch_with_graph(file_paths: list) -> list:
    """Process multiple documents using the LangGraph workflow"""
    
    logger.info(f"Starting batch processing with LangGraph for {len(file_paths)} files")
    
    results = []
    
    for file_path in file_paths:
        try:
            result = process_document_with_graph(file_path)
            results.append(result)
            
            # Log progress
            success_count = len([r for r in results if r.get('validation_status') == 'passed'])
            logger.info(f"Processed {len(results)}/{len(file_paths)} files. Success: {success_count}")
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            error_result = {
                "processing_timestamp": None,
                "file_path": file_path,
                "document_type": "UNKNOWN",
                "validation_status": "failed",
                "extraction_confidence": 0.0,
                "overall_score": 0.0,
                "errors": [f"Processing error: {str(e)}"],
                "warnings": [],
                "extracted_data": {},
                "validation_details": {},
                "processing_log": [f"Error: {str(e)}"]
            }
            results.append(error_result)
    
    logger.info(f"Batch processing completed. Processed {len(results)} files")
    return results 