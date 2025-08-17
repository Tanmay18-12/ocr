#!/usr/bin/env python3
"""
Reader Agent - Reads and analyzes validated document data
"""

import json
import logging
from typing import Dict, Any, List
from datetime import datetime
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import SystemMessage, HumanMessage
from langchain.tools import BaseTool
from config import Config
from utils.logging_config import setup_logging

class DataReaderTool(BaseTool):
    name: str = "Data Reader"
    description: str = "Reads and analyzes validated document data for quality assessment and insights"
    
    def __init__(self):
        super().__init__()
        self.logger = setup_logging()
    
    def _run(self, data: str) -> str:
        """Read and analyze the provided data"""
        try:
            if isinstance(data, str):
                data_dict = json.loads(data)
            else:
                data_dict = data
            
            analysis = self._analyze_data(data_dict)
            return json.dumps(analysis, indent=2)
        except Exception as e:
            self.logger.error(f"Error reading data: {e}")
            return f"Error reading data: {str(e)}"
    
    def _analyze_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the extracted data for quality and completeness"""
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "document_type": data.get("document_type", "UNKNOWN"),
            "quality_score": 0,
            "completeness_score": 0,
            "confidence_score": 0,
            "missing_fields": [],
            "quality_issues": [],
            "recommendations": []
        }
        
        # Calculate completeness score
        if data.get("document_type") == "AADHAAR":
            required_fields = ["Aadhaar Number", "Name", "DOB", "Gender"]
            optional_fields = ["Address"]
        elif data.get("document_type") == "PAN":
            required_fields = ["PAN Number", "Name"]
            optional_fields = ["Father's Name", "DOB"]
        else:
            required_fields = []
            optional_fields = []
        
        # Check required fields
        present_fields = []
        for field in required_fields:
            if field in data and data[field]:
                present_fields.append(field)
            else:
                analysis["missing_fields"].append(field)
        
        # Calculate completeness score
        if required_fields:
            analysis["completeness_score"] = len(present_fields) / len(required_fields) * 100
        
        # Check optional fields
        optional_present = []
        for field in optional_fields:
            if field in data and data[field]:
                optional_present.append(field)
        
        # Quality assessment
        quality_issues = []
        
        # Check for common OCR issues
        for field, value in data.items():
            if isinstance(value, str):
                # Check for gibberish (too many repeated characters)
                if len(set(value)) < len(value) * 0.3:
                    quality_issues.append(f"Potential OCR issue in {field}: {value}")
                
                # Check for very short values
                if len(value.strip()) < 2:
                    quality_issues.append(f"Very short value in {field}: {value}")
        
        analysis["quality_issues"] = quality_issues
        
        # Calculate overall quality score
        quality_score = 100
        quality_score -= len(analysis["missing_fields"]) * 20
        quality_score -= len(quality_issues) * 10
        analysis["quality_score"] = max(0, quality_score)
        
        # Generate recommendations
        recommendations = []
        if analysis["missing_fields"]:
            recommendations.append(f"Missing required fields: {', '.join(analysis['missing_fields'])}")
        
        if quality_issues:
            recommendations.append("OCR quality issues detected - consider manual review")
        
        if analysis["completeness_score"] < 80:
            recommendations.append("Document extraction incomplete - consider reprocessing")
        
        analysis["recommendations"] = recommendations
        
        return analysis

class ReaderAgent:
    """Agent responsible for reading and analyzing validated document data"""
    
    def __init__(self):
        self.logger = setup_logging()
        self.llm = ChatOpenAI(
            model=Config.OPENAI_MODEL,
            temperature=0.1,
            api_key=Config.OPENAI_API_KEY
        )
        self.tools = [DataReaderTool()]
        self.agent = self._create_agent()
    
    def _create_agent(self):
        """Create the reader agent"""
        system_message = """You are a Document Data Reader Agent. Your role is to:
        1. Read and analyze validated document data
        2. Assess data quality and completeness
        3. Identify potential issues or missing information
        4. Provide insights and recommendations for improvement
        5. Generate summary reports of the extracted data
        
        Always be thorough in your analysis and provide clear, actionable recommendations."""
        
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
    
    def read_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Read and analyze the provided data"""
        try:
            self.logger.info("Reader Agent: Starting data analysis")
            
            # Convert data to string for the tool
            data_str = json.dumps(data, indent=2)
            
            # Create analysis prompt
            prompt = f"""
            Please analyze the following validated document data:
            
            {data_str}
            
            Provide a comprehensive analysis including:
            1. Data quality assessment
            2. Completeness evaluation
            3. Identification of any issues
            4. Recommendations for improvement
            5. Summary of key findings
            """
            
            result = self.agent.invoke({"input": prompt})
            
            self.logger.info("Reader Agent: Data analysis completed")
            return {
                "status": "success",
                "analysis": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Reader Agent error: {e}")
            return {
                "status": "error",
                "error_message": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def generate_report(self, data: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """Generate a comprehensive report"""
        try:
            report = f"""
# Document Analysis Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Document Information
- Type: {data.get('document_type', 'Unknown')}
- Processing Status: {data.get('status', 'Unknown')}

## Extracted Data
"""
            
            # Add extracted fields
            for field, value in data.items():
                if field not in ['document_type', 'status', 'raw_text', 'error']:
                    report += f"- {field}: {value}\n"
            
            report += f"""
## Quality Analysis
- Completeness Score: {analysis.get('completeness_score', 0):.1f}%
- Quality Score: {analysis.get('quality_score', 0):.1f}%
- Missing Fields: {', '.join(analysis.get('missing_fields', []))}

## Issues Identified
"""
            
            for issue in analysis.get('quality_issues', []):
                report += f"- {issue}\n"
            
            report += f"""
## Recommendations
"""
            
            for rec in analysis.get('recommendations', []):
                report += f"- {rec}\n"
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating report: {e}")
            return f"Error generating report: {str(e)}" 