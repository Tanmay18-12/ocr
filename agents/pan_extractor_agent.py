from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import re
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from config import Config
import logging

class PANExtractorAgent:
    """PAN Card extraction agent with enhanced pattern recognition"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=Config.OPENAI_MODEL,
            temperature=0.1,
            api_key=Config.OPENAI_API_KEY
        )
        
        self.system_prompt = """You are a specialized PAN card information extraction expert. 
        Your role is to accurately extract key information from PAN card documents including:
        
        Required Fields:
        1. Name - Card holder's full name
        2. Father's Name - Guardian's name (Father/Mother/Spouse)
        3. DOB - Date of Birth in DD/MM/YYYY format
        4. PAN Number - 10-character alphanumeric code (5 letters + 4 digits + 1 letter)
        
        You must:
        - Use precise pattern matching for PAN numbers (format: ABCDE1234F)
        - Extract names accurately, handling various formats
        - Parse dates in multiple formats and standardize to DD/MM/YYYY
        - Handle OCR artifacts and clean extracted text
        - Provide confidence scores for each extracted field
        - Return results in structured JSON format"""
    
    def extract_pan_fields(self, raw_text: str) -> Dict[str, Any]:
        """Extract PAN card fields from raw text using pattern matching and LLM"""
        
        try:
            # First, use pattern matching for critical fields
            pattern_results = self._extract_with_patterns(raw_text)
            
            # Then use LLM for validation and enhancement
            llm_results = self._extract_with_llm(raw_text, pattern_results)
            
            # Combine and validate results
            final_results = self._combine_results(pattern_results, llm_results)
            
            # Calculate confidence scores
            confidence_scores = self._calculate_field_confidence(final_results, raw_text)
            
            return {
                "status": "success",
                "extracted_data": final_results,
                "confidence_scores": confidence_scores,
                "overall_confidence": self._calculate_overall_confidence(confidence_scores),
                "extraction_method": "pattern_matching_and_llm",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"PAN extraction error: {e}")
            return {
                "status": "error",
                "error_message": str(e),
                "extracted_data": {},
                "timestamp": datetime.now().isoformat()
            }
    
    def _extract_with_patterns(self, text: str) -> Dict[str, Any]:
        """Extract fields using regex patterns"""
        results = {
            "Name": None,
            "Father's Name": None,
            "DOB": None,
            "PAN Number": None
        }
        
        # PAN Number patterns (10 characters: 5 letters + 4 digits + 1 letter)
        pan_patterns = [
            r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b',  # Standard PAN format
            r'\b[A-Z]{5}\s*[0-9]{4}\s*[A-Z]{1}\b',  # PAN with spaces
            r'PAN[:\s]*([A-Z]{5}[0-9]{4}[A-Z]{1})',  # PAN with label
            r'Permanent Account Number[:\s]*([A-Z]{5}[0-9]{4}[A-Z]{1})'  # Full label
        ]
        
        for pattern in pan_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                pan = match.group(1) if len(match.groups()) > 0 else match.group(0)
                pan = pan.replace(" ", "").upper()
                if len(pan) == 10 and re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]$', pan):
                    results['PAN Number'] = pan
                    break
        
        # Date of Birth patterns
        dob_patterns = [
            r'(DOB|Date of Birth)[\s:]*([\d]{1,2}[-/][\d]{1,2}[-/][\d]{2,4})',
            r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'(\d{2}[-/]\d{2}[-/]\d{4})',  # DD/MM/YYYY format
            r'(\d{4}[-/]\d{2}[-/]\d{2})'   # YYYY/MM/DD format
        ]
        
        for pattern in dob_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                dob = match.group(2) if len(match.groups()) > 1 else match.group(1)
                results['DOB'] = self._standardize_date(dob)
                break
        
        # Name patterns
        name_patterns = [
            r'(Name|NAME)[:\s]*([A-Z][a-zA-Z\s]{2,})',
            r'Card Holder Name[:\s]*([A-Z][a-zA-Z\s]{2,})',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)',  # Two words like "John Doe"
            r'([A-Z][a-zA-Z\s]{2,})'  # General name pattern
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(2) if len(match.groups()) > 1 else match.group(1)
                if self._is_valid_name(name):
                    results['Name'] = name.strip()
                    break
        
        # Father's Name patterns
        father_name_patterns = [
            r'(Father\'s Name|Father Name|FATHER\'S NAME)[:\s]*([A-Z][a-zA-Z\s]{2,})',
            r'(S/O|Son of)[:\s]*([A-Z][a-zA-Z\s]{2,})',
            r'(D/O|Daughter of)[:\s]*([A-Z][a-zA-Z\s]{2,})',
            r'(W/O|Wife of)[:\s]*([A-Z][a-zA-Z\s]{2,})',
            r'Guardian[:\s]*([A-Z][a-zA-Z\s]{2,})'
        ]
        
        for pattern in father_name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                father_name = match.group(2) if len(match.groups()) > 1 else match.group(1)
                if self._is_valid_name(father_name):
                    results['Father\'s Name'] = father_name.strip()
                    break
        
        return results
    
    def _extract_with_llm(self, text: str, pattern_results: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to enhance and validate extracted fields"""
        try:
            prompt = f"""
            Analyze the following text from a PAN card document and extract the required information.
            If you find any information that conflicts with the pattern-matching results, provide the correct information.
            
            Raw Text:
            {text[:2000]}  # Limit text length for LLM
            
            Pattern Matching Results:
            {json.dumps(pattern_results, indent=2)}
            
            Please extract and return ONLY the following fields in JSON format:
            {{
                "Name": "Full name of the card holder",
                "Father's Name": "Guardian's name (Father/Mother/Spouse)",
                "DOB": "Date of Birth in DD/MM/YYYY format",
                "PAN Number": "10-character PAN number (5 letters + 4 digits + 1 letter)"
            }}
            
            Rules:
            1. PAN Number must be exactly 10 characters: 5 letters + 4 digits + 1 letter
            2. Names should be properly capitalized
            3. Date should be in DD/MM/YYYY format
            4. If a field is not found, use null
            5. Clean any OCR artifacts from the text
            """
            
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            
            # Parse LLM response
            try:
                llm_data = json.loads(response.content)
                return {
                    "Name": llm_data.get("Name"),
                    "Father's Name": llm_data.get("Father's Name"),
                    "DOB": llm_data.get("DOB"),
                    "PAN Number": llm_data.get("PAN Number")
                }
            except json.JSONDecodeError:
                # Fallback to pattern matching if LLM response is invalid
                return pattern_results
                
        except Exception as e:
            logging.error(f"LLM extraction error: {e}")
            return pattern_results
    
    def _combine_results(self, pattern_results: Dict[str, Any], llm_results: Dict[str, Any]) -> Dict[str, Any]:
        """Combine pattern matching and LLM results intelligently"""
        combined = {}
        
        for field in ["Name", "Father's Name", "DOB", "PAN Number"]:
            # Prefer pattern matching for PAN Number (more reliable)
            if field == "PAN Number":
                combined[field] = pattern_results.get(field) or llm_results.get(field)
            # Prefer LLM for names (better at handling variations)
            elif field in ["Name", "Father's Name"]:
                combined[field] = llm_results.get(field) or pattern_results.get(field)
            # For DOB, use whichever is more complete
            elif field == "DOB":
                pattern_dob = pattern_results.get(field)
                llm_dob = llm_results.get(field)
                
                if pattern_dob and llm_dob:
                    # If both exist, prefer the one that looks more complete
                    if len(pattern_dob) >= len(llm_dob):
                        combined[field] = pattern_dob
                    else:
                        combined[field] = llm_dob
                else:
                    combined[field] = pattern_dob or llm_dob
            else:
                combined[field] = pattern_results.get(field) or llm_results.get(field)
        
        return combined
    
    def _calculate_field_confidence(self, results: Dict[str, Any], raw_text: str) -> Dict[str, float]:
        """Calculate confidence scores for each field"""
        confidence_scores = {}
        
        # PAN Number confidence
        pan = results.get("PAN Number")
        if pan:
            if re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]$', pan):
                confidence_scores["PAN Number"] = 0.95
            else:
                confidence_scores["PAN Number"] = 0.3
        else:
            confidence_scores["PAN Number"] = 0.0
        
        # Name confidence
        name = results.get("Name")
        if name:
            if len(name) >= 3 and self._is_valid_name(name):
                confidence_scores["Name"] = 0.85
            else:
                confidence_scores["Name"] = 0.4
        else:
            confidence_scores["Name"] = 0.0
        
        # Father's Name confidence
        father_name = results.get("Father's Name")
        if father_name:
            if len(father_name) >= 3 and self._is_valid_name(father_name):
                confidence_scores["Father's Name"] = 0.8
            else:
                confidence_scores["Father's Name"] = 0.3
        else:
            confidence_scores["Father's Name"] = 0.0
        
        # DOB confidence
        dob = results.get("DOB")
        if dob:
            if self._is_valid_date(dob):
                confidence_scores["DOB"] = 0.9
            else:
                confidence_scores["DOB"] = 0.4
        else:
            confidence_scores["DOB"] = 0.0
        
        return confidence_scores
    
    def _calculate_overall_confidence(self, confidence_scores: Dict[str, float]) -> float:
        """Calculate overall confidence score"""
        if not confidence_scores:
            return 0.0
        
        # Weight different fields
        weights = {
            "PAN Number": 0.4,
            "Name": 0.3,
            "Father's Name": 0.2,
            "DOB": 0.1
        }
        
        total_score = 0.0
        for field, weight in weights.items():
            score = confidence_scores.get(field, 0.0)
            total_score += score * weight
        
        return round(total_score, 2)
    
    def _is_valid_name(self, name: str) -> bool:
        """Validate if string looks like a real name"""
        if not name or len(name) < 2 or len(name) > 50:
            return False
        
        # Skip common non-name words
        skip_words = {'DOB', 'PAN', 'GOVT', 'INDIA', 'DEPARTMENT', 'AUTHORITY', 'UNIQUE', 'PERMANENT', 'ACCOUNT', 'NUMBER', 'CARD'}
        if name.upper() in skip_words:
            return False
        
        # Check if mostly alphabetic
        alpha_ratio = sum(1 for c in name if c.isalpha()) / len(name)
        return alpha_ratio > 0.6
    
    def _is_valid_date(self, date_str: str) -> bool:
        """Validate date format"""
        if not date_str:
            return False
        
        # Check if it matches DD/MM/YYYY or DD-MM-YYYY
        if re.match(r'^\d{1,2}[-/]\d{1,2}[-/]\d{4}$', date_str):
            return True
        
        return False
    
    def _standardize_date(self, date_str: str) -> str:
        """Standardize date to DD/MM/YYYY format"""
        if not date_str:
            return None
        
        # Handle different separators
        date_str = date_str.replace('-', '/')
        
        # Parse and standardize
        try:
            parts = date_str.split('/')
            if len(parts) == 3:
                day, month, year = parts
                
                # Handle 2-digit years
                if len(year) == 2:
                    year = '20' + year if int(year) < 50 else '19' + year
                
                # Ensure proper formatting
                day = day.zfill(2)
                month = month.zfill(2)
                
                return f"{day}/{month}/{year}"
        except:
            pass
        
        return date_str
    
    def validate_pan_number(self, pan: str) -> Dict[str, Any]:
        """Validate PAN number format and structure"""
        if not pan:
            return {"valid": False, "reason": "empty", "type": "invalid"}
        
        clean_pan = pan.replace(" ", "").upper()
        
        # Check basic format
        if not re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]$', clean_pan):
            return {"valid": False, "reason": "invalid_format", "type": "invalid"}
        
        # Check for suspicious patterns
        if self._is_sequential(clean_pan):
            return {"valid": False, "reason": "sequential_pattern", "type": "invalid"}
        
        if self._has_repeated_pattern(clean_pan):
            return {"valid": False, "reason": "repeated_pattern", "type": "invalid"}
        
        return {
            "valid": True,
            "type": "valid",
            "format": clean_pan,
            "length": len(clean_pan)
        }
    
    def _is_sequential(self, text: str) -> bool:
        """Check if text contains sequential patterns"""
        if len(text) < 3:
            return False
        
        # Check for sequential numbers
        for i in range(len(text) - 2):
            if text[i:i+3].isdigit():
                nums = [int(c) for c in text[i:i+3]]
                if nums == list(range(nums[0], nums[0] + 3)):
                    return True
        
        return False
    
    def _has_repeated_pattern(self, text: str) -> bool:
        """Check if text has repeated patterns"""
        if len(text) < 4:
            return False
        
        # Check for repeated 2-char patterns
        for i in range(len(text) - 3):
            pattern = text[i:i+2]
            if text.count(pattern) > 2:
                return True
        
        return False
    
    def generate_extraction_report(self, extraction_result: Dict[str, Any]) -> str:
        """Generate a detailed extraction report"""
        try:
            prompt = f"""
            Generate a detailed PAN card extraction report for the following results:
            
            Extraction Status: {extraction_result.get('status', 'Unknown')}
            Overall Confidence: {extraction_result.get('overall_confidence', 0):.2%}
            
            Extracted Data: {json.dumps(extraction_result.get('extracted_data', {}), indent=2)}
            Confidence Scores: {json.dumps(extraction_result.get('confidence_scores', {}), indent=2)}
            
            Provide a professional report including:
            1. Summary of extraction results
            2. Field-by-field analysis with confidence scores
            3. Quality assessment of extracted data
            4. Recommendations for improvement
            5. Validation status for each field
            """
            
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            return response.content
            
        except Exception as e:
            logging.error(f"Error generating extraction report: {e}")
            return f"Error generating report: {str(e)}"



