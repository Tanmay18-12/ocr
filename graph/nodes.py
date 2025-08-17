from typing import Dict, Any
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from graph.state import DocumentState
from agents.extractor_agent import ExtractorAgent
from agents.validator_agent import ValidatorAgent
from config import Config
import logging

logger = logging.getLogger(__name__)

def create_extraction_node():
    """Create the extraction node for the graph"""
    
    def extraction_node(state: DocumentState) -> DocumentState:
        """Extract information from document"""
        state.add_log("Starting document extraction")
        
        try:
            # Initialize extractor agent
            extractor = ExtractorAgent()
            
            # Perform extraction
            extraction_result = extractor.run(state.file_path)
            
            # Update state with extraction results
            state.update_extraction_results(extraction_result)
            state.add_log(f"Extraction completed with status: {state.extraction_status}")
            
            if state.extraction_status == "error":
                state.add_log(f"Extraction error: {state.extraction_error}")
            else:
                state.add_log(f"Document type detected: {state.document_type}")
                state.add_log(f"Extraction confidence: {state.extraction_confidence:.2%}")
            
        except Exception as e:
            state.extraction_status = "error"
            state.extraction_error = str(e)
            state.add_log(f"Extraction failed with exception: {str(e)}")
            logger.error(f"Extraction error for {state.file_path}: {e}")
        
        return state
    
    return extraction_node

def create_validation_node():
    """Create the validation node for the graph"""
    
    def validation_node(state: DocumentState) -> DocumentState:
        """Validate extracted information"""
        state.add_log("Starting document validation")
        
        try:
            # Skip validation if extraction failed
            if state.extraction_status == "error":
                state.validation_status = "failed"
                state.errors.append("Cannot validate due to extraction failure")
                state.add_log("Validation skipped due to extraction failure")
                return state
            
            # Initialize validator agent
            validator = ValidatorAgent()
            
            # Prepare extraction result for validation
            extraction_result = {
                "status": state.extraction_status,
                "extracted_data": state.extracted_data,
                "extraction_confidence": state.extraction_confidence
            }
            
            # Perform validation
            validation_result = validator.validate(extraction_result)
            
            # Update state with validation results
            state.update_validation_results(validation_result)
            state.add_log(f"Validation completed with status: {state.validation_status}")
            
            if state.validation_status == "error":
                state.add_log(f"Validation error: {state.validation_error}")
            else:
                state.add_log(f"Overall validation score: {state.overall_score:.2%}")
                state.add_log(f"Found {len(state.errors)} errors and {len(state.warnings)} warnings")
            
        except Exception as e:
            state.validation_status = "error"
            state.validation_error = str(e)
            state.add_log(f"Validation failed with exception: {str(e)}")
            logger.error(f"Validation error for {state.file_path}: {e}")
        
        return state
    
    return validation_node

def create_analysis_node():
    """Create the analysis node for the graph"""
    
    def analysis_node(state: DocumentState) -> DocumentState:
        """Analyze and provide insights on the processing results"""
        state.add_log("Starting analysis and insights generation")
        
        try:
            # Initialize LLM for analysis
            llm = ChatOpenAI(
                model=Config.OPENAI_MODEL,
                temperature=0.1,
                api_key=Config.OPENAI_API_KEY
            )
            
            # Prepare analysis prompt
            analysis_prompt = f"""
            Analyze the document processing results and provide insights:
            
            Document: {state.file_path}
            Document Type: {state.document_type}
            Extraction Status: {state.extraction_status}
            Extraction Confidence: {state.extraction_confidence:.2%}
            Validation Status: {state.validation_status}
            Overall Score: {state.overall_score:.2%}
            
            Extracted Data: {state.extracted_data}
            Errors: {state.errors}
            Warnings: {state.warnings}
            
            Provide a brief analysis of:
            1. Quality of extraction
            2. Validation results
            3. Any notable issues or concerns
            4. Recommendations for improvement
            """
            
            # Get analysis
            messages = [
                SystemMessage(content="You are a document processing analyst. Provide concise, professional analysis."),
                HumanMessage(content=analysis_prompt)
            ]
            
            response = llm.invoke(messages)
            analysis = response.content
            
            state.add_log("Analysis completed")
            state.add_log(f"Analysis insights: {analysis[:100]}...")
            
        except Exception as e:
            state.add_log(f"Analysis failed: {str(e)}")
            logger.warning(f"Analysis error for {state.file_path}: {e}")
        
        return state
    
    return analysis_node

def create_finalize_node():
    """Create the finalization node for the graph"""
    
    def finalize_node(state: DocumentState) -> DocumentState:
        """Finalize the processing and prepare final results"""
        state.add_log("Finalizing document processing")
        
        # Determine final status
        if state.extraction_status == "error":
            state.final_status = "failed"
        elif state.validation_status == "error":
            state.final_status = "failed"
        elif state.validation_status == "passed":
            state.final_status = "success"
        else:
            state.final_status = "failed"
        
        state.add_log(f"Processing completed with final status: {state.final_status}")
        
        return state
    
    return finalize_node 