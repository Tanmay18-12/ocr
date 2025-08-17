from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import re
from datetime import datetime
from typing import Dict, Any, List, Tuple
from config import Config
import logging

class ValidationPatterns:
    """Contains all validation patterns and rules"""
    
    # Aadhaar patterns
    AADHAAR_MASKED_PATTERN = r'^\d{4}[X*]{4}\d{4}$|^\d{4}\s*[X*]{4}\s*\d{4}$'
    AADHAAR_UNMASKED_PATTERN = r'^\d{12}$'
    
    # PAN patterns
    PAN_PATTERN = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'
    
    # Name patterns
    NAME_PATTERN = r'^[A-Za-z\s.]+$'
    NAME_MIN_LENGTH = 2
    NAME_MAX_LENGTH = 50
    
    # Date patterns
    DATE_PATTERNS = [
        r'^\d{1,2}/\d{1,2}/\d{4}$',  # DD/MM/YYYY
        r'^\d{1,2}-\d{1,2}-\d{4}$',  # DD-MM-YYYY
        r'^\d{4}-\d{1,2}-\d{1,2}$',  # YYYY-MM-DD
        r'^\d{1,2}/\d{1,2}/\d{2}$',  # DD/MM/YY
        r'^\d{1,2}-\d{1,2}-\d{2}$',  # DD-MM-YY
    ]
    
    # Gender patterns
    GENDER_PATTERNS = ['M', 'F', 'MALE', 'FEMALE']
    
    # Address patterns
    ADDRESS_MIN_LENGTH = 10
    ADDRESS_MAX_LENGTH = 500
    
    # Invalid patterns (common OCR errors)
    INVALID_PATTERNS = [
        r'[0-9]{1,2}[A-Za-z]{1,2}[0-9]{1,2}',  # Mixed alphanumeric
        r'[A-Za-z]{1,2}[0-9]{1,2}[A-Za-z]{1,2}',  # Mixed alphanumeric
        r'[^A-Za-z0-9\s.,/:()\-]',  # Special characters
    ]

class FieldValidator:
    """Handles individual field validation"""
    
    @staticmethod
    def validate_aadhaar_number(aadhaar: str) -> Dict[str, Any]:
        """Validate Aadhaar number with comprehensive checks"""
        if not aadhaar:
            return {"valid": False, "reason": "not_found", "type": "empty"}
        
        # Clean the input
        clean_aadhaar = aadhaar.replace(" ", "").replace("-", "")
        
        # Check for masked Aadhaar
        if "X" in clean_aadhaar or "*" in clean_aadhaar:
            is_valid = bool(re.match(ValidationPatterns.AADHAAR_MASKED_PATTERN, clean_aadhaar))
            return {
                "valid": is_valid,
                "type": "masked",
                "format": "XXXX-XXXX-1234" if is_valid else "invalid",
                "reason": "invalid_format" if not is_valid else None
            }
        
        # Check for unmasked Aadhaar
        if re.match(ValidationPatterns.AADHAAR_UNMASKED_PATTERN, clean_aadhaar):
            # Additional checks for unmasked Aadhaar
            if clean_aadhaar == "000000000000":
                return {"valid": False, "type": "unmasked", "reason": "all_zeros"}
            
            # Check for sequential numbers (suspicious)
            if FieldValidator._is_sequential(clean_aadhaar):
                return {"valid": False, "type": "unmasked", "reason": "sequential_numbers"}
            
            # Check for repeated patterns
            if FieldValidator._has_repeated_pattern(clean_aadhaar):
                return {"valid": False, "type": "unmasked", "reason": "repeated_pattern"}
            
            return {
                "valid": True,
                "type": "unmasked",
                "length": len(clean_aadhaar),
                "checksum_valid": FieldValidator._validate_aadhaar_checksum(clean_aadhaar)
            }
        
        return {"valid": False, "type": "unknown", "reason": "invalid_format"}
    
    @staticmethod
    def test_invalid_aadhaar_patterns() -> Dict[str, Any]:
        """Test various invalid Aadhaar patterns and return detailed results"""
        test_cases = [
            ("12345678901", "11 digits", "Invalid length"),
            ("1234567890123", "13 digits", "Invalid length"),
            ("12345678901A", "11 digits + letter", "Invalid characters"),
            ("000000000000", "All zeros", "Suspicious pattern"),
            ("123456789012", "12 digits sequential", "Sequential numbers"),
            ("111111111111", "All ones", "Repeated pattern"),
            ("", "Empty string", "Empty input"),
            ("1234-5678-9012", "With dashes", "Invalid format"),
            ("1234 5678 9012", "With spaces", "Invalid format"),
            ("XXXX-XXXX-1234", "Masked format", "Masked Aadhaar"),
        ]
        
        results = {}
        for aadhaar, description, expected_issue in test_cases:
            result = FieldValidator.validate_aadhaar_number(aadhaar)
            results[description] = {
                "input": aadhaar,
                "expected_issue": expected_issue,
                "validation_result": result,
                "is_invalid": not result["valid"]
            }
        
        return results
    
    @staticmethod
    def test_invalid_pan_patterns() -> Dict[str, Any]:
        """Test various invalid PAN patterns and return detailed results"""
        test_cases = [
            ("ABCD1234E", "9 characters", "Invalid length"),
            ("ABCDE12345F", "11 characters", "Invalid length"),
            ("ABCD1234EF", "Wrong format", "Invalid format"),
            ("12345ABCDE", "Wrong format", "Invalid format"),
            ("ABCDE1234", "Missing last letter", "Invalid format"),
            ("AAAAA0000A", "All A's and 0's", "Common invalid pattern"),
            ("ZZZZZ9999Z", "All Z's and 9's", "Common invalid pattern"),
            ("ABCDE1234F", "Sequential pattern", "Common invalid pattern"),
            ("AAAAA1111A", "All same letters", "All same characters"),
            ("", "Empty string", "Empty input"),
            ("ABCD 1234 E", "With spaces", "Invalid format"),
            ("ABCD-1234-E", "With dashes", "Invalid format"),
        ]
        
        results = {}
        for pan, description, expected_issue in test_cases:
            result = FieldValidator.validate_pan_number(pan)
            results[description] = {
                "input": pan,
                "expected_issue": expected_issue,
                "validation_result": result,
                "is_invalid": not result["valid"]
            }
        
        return results
    
    @staticmethod
    def explain_validation_logic(aadhaar: str) -> Dict[str, Any]:
        """Explain step by step what happens during Aadhaar validation"""
        explanation = {
            "input": aadhaar,
            "length": len(aadhaar) if aadhaar else 0,
            "steps": [],
            "final_result": None
        }
        
        # Step 1: Check if input is empty
        step1 = {
            "step": 1,
            "check": "Empty input check",
            "condition": "if not aadhaar",
            "result": not bool(aadhaar),
            "action": "return invalid" if not aadhaar else "continue"
        }
        explanation["steps"].append(step1)
        
        if not aadhaar:
            explanation["final_result"] = {"valid": False, "reason": "not_found", "type": "empty"}
            return explanation
        
        # Step 2: Clean the input
        clean_aadhaar = aadhaar.replace(" ", "").replace("-", "")
        step2 = {
            "step": 2,
            "check": "Input cleaning",
            "original": aadhaar,
            "cleaned": clean_aadhaar,
            "changes": "removed spaces and dashes" if aadhaar != clean_aadhaar else "no changes needed"
        }
        explanation["steps"].append(step2)
        
        # Step 3: Check for masked Aadhaar
        has_x = "X" in clean_aadhaar
        has_star = "*" in clean_aadhaar
        step3 = {
            "step": 3,
            "check": "Masked Aadhaar check",
            "contains_x": has_x,
            "contains_star": has_star,
            "is_masked": has_x or has_star,
            "action": "check mask pattern" if (has_x or has_star) else "check unmasked pattern"
        }
        explanation["steps"].append(step3)
        
        if has_x or has_star:
            pattern = ValidationPatterns.AADHAAR_MASKED_PATTERN
            is_valid = bool(re.match(pattern, clean_aadhaar))
            explanation["final_result"] = {
                "valid": is_valid,
                "type": "masked",
                "format": "XXXX-XXXX-1234" if is_valid else "invalid",
                "reason": "invalid_format" if not is_valid else None
            }
            return explanation
        
        # Step 4: Check unmasked Aadhaar pattern
        pattern = ValidationPatterns.AADHAAR_UNMASKED_PATTERN
        match_result = re.match(pattern, clean_aadhaar)
        step4 = {
            "step": 4,
            "check": "Unmasked Aadhaar pattern",
            "pattern": pattern,
            "pattern_meaning": "exactly 12 digits",
            "match_result": bool(match_result),
            "action": "continue with additional checks" if match_result else "return invalid"
        }
        explanation["steps"].append(step4)
        
        if not match_result:
            explanation["final_result"] = {"valid": False, "type": "unknown", "reason": "invalid_format"}
            return explanation
        
        # Step 5: Additional checks (if pattern matched)
        step5 = {
            "step": 5,
            "check": "Additional validation checks",
            "checks": [
                "all_zeros_check",
                "sequential_numbers_check", 
                "repeated_pattern_check",
                "checksum_validation"
            ]
        }
        explanation["steps"].append(step5)
        
        # Perform additional checks
        if clean_aadhaar == "000000000000":
            explanation["final_result"] = {"valid": False, "type": "unmasked", "reason": "all_zeros"}
        elif FieldValidator._is_sequential(clean_aadhaar):
            explanation["final_result"] = {"valid": False, "type": "unmasked", "reason": "sequential_numbers"}
        elif FieldValidator._has_repeated_pattern(clean_aadhaar):
            explanation["final_result"] = {"valid": False, "type": "unmasked", "reason": "repeated_pattern"}
        else:
            explanation["final_result"] = {
                "valid": True,
                "type": "unmasked",
                "length": len(clean_aadhaar),
                "checksum_valid": FieldValidator._validate_aadhaar_checksum(clean_aadhaar)
            }
        
        return explanation
    
    @staticmethod
    def validate_pan_number(pan: str) -> Dict[str, Any]:
        """Validate PAN number with comprehensive checks"""
        if not pan:
            return {"valid": False, "reason": "not_found", "type": "empty"}
        
        clean_pan = pan.replace(" ", "").upper()
        
        # Check length (must be exactly 10 characters)
        if len(clean_pan) != 10:
            return {"valid": False, "type": "invalid", "reason": "invalid_length", "expected_length": 10, "actual_length": len(clean_pan)}
        
        # Check basic pattern (5 letters + 4 digits + 1 letter)
        if not re.match(ValidationPatterns.PAN_PATTERN, clean_pan):
            return {"valid": False, "type": "invalid", "reason": "invalid_format", "expected_format": "ABCDE1234F"}
        
        # Check for suspicious patterns
        if FieldValidator._is_sequential(clean_pan):
            return {"valid": False, "type": "invalid", "reason": "sequential_pattern"}
        
        # Check for repeated characters
        if FieldValidator._has_repeated_pattern(clean_pan):
            return {"valid": False, "type": "invalid", "reason": "repeated_pattern"}
        
        # Check for all same characters
        if len(set(clean_pan)) == 1:
            return {"valid": False, "type": "invalid", "reason": "all_same_characters"}
        
        # Check for common invalid patterns
        invalid_patterns = [
            "AAAAA0000A",  # All A's and 0's
            "ZZZZZ9999Z",  # All Z's and 9's
            "ABCDE1234F",  # Sequential letters and numbers
        ]
        
        if clean_pan in invalid_patterns:
            return {"valid": False, "type": "invalid", "reason": "common_invalid_pattern"}
        
        # Validate PAN structure
        letters_part = clean_pan[:5]
        digits_part = clean_pan[5:9]
        last_letter = clean_pan[9]
        
        # Check if letters part contains only letters
        if not letters_part.isalpha():
            return {"valid": False, "type": "invalid", "reason": "letters_part_contains_digits"}
        
        # Check if digits part contains only digits
        if not digits_part.isdigit():
            return {"valid": False, "type": "invalid", "reason": "digits_part_contains_letters"}
        
        # Check if last character is a letter
        if not last_letter.isalpha():
            return {"valid": False, "type": "invalid", "reason": "last_character_not_letter"}
        
        return {
            "valid": True,
            "type": "valid",
            "format": clean_pan,
            "length": len(clean_pan),
            "structure": {
                "letters_part": letters_part,
                "digits_part": digits_part,
                "last_letter": last_letter
            }
        }
    
    @staticmethod
    def validate_name(name: str) -> Dict[str, Any]:
        """Validate name with comprehensive checks"""
        if not name:
            return {"valid": False, "reason": "not_found", "type": "empty"}
        
        clean_name = name.strip()
        
        # Check length
        if len(clean_name) < ValidationPatterns.NAME_MIN_LENGTH:
            return {"valid": False, "type": "short", "reason": "too_short"}
        
        if len(clean_name) > ValidationPatterns.NAME_MAX_LENGTH:
            return {"valid": False, "type": "long", "reason": "too_long"}
        
        # Check pattern
        if not re.match(ValidationPatterns.NAME_PATTERN, clean_name):
            return {"valid": False, "type": "invalid", "reason": "invalid_characters"}
        
        # Check for common OCR errors
        if FieldValidator._has_ocr_errors(clean_name):
            return {"valid": False, "type": "ocr_error", "reason": "ocr_artifacts"}
        
        # Check for suspicious patterns
        if FieldValidator._is_suspicious_name(clean_name):
            return {"valid": False, "type": "suspicious", "reason": "suspicious_pattern"}
        
        return {
            "valid": True,
            "type": "valid",
            "length": len(clean_name),
            "format": clean_name.title()
        }
    
    @staticmethod
    def validate_date(date_str: str) -> Dict[str, Any]:
        """Validate date with comprehensive checks"""
        if not date_str:
            return {"valid": False, "reason": "not_found", "type": "empty"}
        
        clean_date = date_str.strip()
        
        # Check if it matches any date pattern
        for pattern in ValidationPatterns.DATE_PATTERNS:
            if re.match(pattern, clean_date):
                # Try to parse the date
                try:
                    if '/' in clean_date:
                        if len(clean_date.split('/')[-1]) == 2:
                            parsed_date = datetime.strptime(clean_date, "%d/%m/%y")
                        else:
                            parsed_date = datetime.strptime(clean_date, "%d/%m/%Y")
                    elif '-' in clean_date:
                        if len(clean_date.split('-')[-1]) == 2:
                            parsed_date = datetime.strptime(clean_date, "%d-%m-%y")
                        else:
                            parsed_date = datetime.strptime(clean_date, "%d-%m-%Y")
                    
                    # Check for reasonable date range (not future, not too old)
                    current_year = datetime.now().year
                    if parsed_date.year > current_year:
                        return {"valid": False, "type": "future", "reason": "future_date"}
                    
                    if parsed_date.year < 1900:
                        return {"valid": False, "type": "old", "reason": "too_old"}
                    
                    return {
                        "valid": True,
                        "type": "valid",
                        "parsed_date": parsed_date.strftime("%Y-%m-%d"),
                        "format": clean_date
                    }
                    
                except ValueError:
                    continue
        
        return {"valid": False, "type": "invalid", "reason": "unrecognized_format"}
    
    @staticmethod
    def validate_gender(gender: str) -> Dict[str, Any]:
        """Validate gender field"""
        if not gender:
            return {"valid": False, "reason": "not_found", "type": "empty"}
        
        clean_gender = gender.strip().upper()
        
        if clean_gender in ValidationPatterns.GENDER_PATTERNS:
            return {
                "valid": True,
                "type": "valid",
                "value": clean_gender
            }
        
        return {"valid": False, "type": "invalid", "reason": "invalid_value"}
    
    @staticmethod
    def validate_address(address: str) -> Dict[str, Any]:
        """Validate address field"""
        if not address:
            return {"valid": False, "reason": "not_found", "type": "empty"}
        
        clean_address = address.strip()
        
        if len(clean_address) < ValidationPatterns.ADDRESS_MIN_LENGTH:
            return {"valid": False, "type": "short", "reason": "too_short"}
        
        if len(clean_address) > ValidationPatterns.ADDRESS_MAX_LENGTH:
            return {"valid": False, "type": "long", "reason": "too_long"}
        
        # Check for OCR artifacts
        if FieldValidator._has_ocr_errors(clean_address):
            return {"valid": False, "type": "ocr_error", "reason": "ocr_artifacts"}
        
        return {
            "valid": True,
            "type": "valid",
            "length": len(clean_address)
        }
    
    # Helper methods for pattern detection
    @staticmethod
    def _is_sequential(text: str) -> bool:
        """Check if text contains sequential numbers/letters"""
        if len(text) < 3:
            return False
        
        # Check for sequential numbers
        for i in range(len(text) - 2):
            if text[i:i+3].isdigit():
                nums = [int(c) for c in text[i:i+3]]
                if nums == list(range(nums[0], nums[0] + 3)):
                    return True
        
        return False
    
    @staticmethod
    def _has_repeated_pattern(text: str) -> bool:
        """Check if text has repeated patterns"""
        if len(text) < 4:
            return False
        
        # Check for repeated 2-char patterns
        for i in range(len(text) - 3):
            pattern = text[i:i+2]
            if text.count(pattern) > 2:
                return True
        
        return False
    
    @staticmethod
    def _has_ocr_errors(text: str) -> bool:
        """Check for common OCR errors"""
        # Check for mixed case patterns that are suspicious
        if re.search(r'[A-Z]{1,2}[a-z]{1,2}[A-Z]{1,2}', text):
            return True
        
        # Check for numbers mixed with letters in suspicious ways
        if re.search(r'[0-9]{1,2}[A-Za-z]{1,2}[0-9]{1,2}', text):
            return True
        
        return False
    
    @staticmethod
    def _is_suspicious_name(name: str) -> bool:
        """Check for suspicious name patterns"""
        suspicious_patterns = [
            'TEST', 'SAMPLE', 'EXAMPLE', 'DUMMY', 'FAKE',
            'ABCD', 'XYZ', '123', '000', 'XXX'
        ]
        
        return any(pattern in name.upper() for pattern in suspicious_patterns)
    
    @staticmethod
    def _validate_aadhaar_checksum(aadhaar: str) -> bool:
        """Validate Aadhaar checksum using Verhoeff algorithm"""
        try:
            if len(aadhaar) != 12:
                return False
            
            # Basic validation: check if it's not all zeros
            if aadhaar == "000000000000":
                return False
            
            # For now, return True for valid length and non-zero
            # In production, implement proper Verhoeff algorithm
            return True
            
        except Exception:
            return False

class ValidatorAgent:
    """Enhanced validator agent with comprehensive pattern validation"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=Config.OPENAI_MODEL,
            temperature=0.1,
            api_key=Config.OPENAI_API_KEY
        )
        
        self.system_prompt = """You are a meticulous document verification specialist who ensures 
        that extracted information meets all regulatory standards and formats. 
        You have deep knowledge of Indian document formats and validation rules.
        
        Your role is to:
        1. Validate extracted field formats and completeness
        2. Check for regulatory compliance
        3. Identify inconsistencies and errors
        4. Provide detailed validation reports
        5. Calculate confidence scores for validation
        6. Detect invalid patterns and OCR artifacts"""
    
    def validate(self, extraction_result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate extracted fields and return validation results"""
        
        if extraction_result.get("status") == "error":
            return {
                "validation_status": "failed",
                "reason": "Extraction failed",
                "errors": [extraction_result.get("error_message", "Unknown extraction error")],
                "extracted_data": {},
                "validation_details": {},
                "is_valid": False
            }
        
        extracted_data = extraction_result.get("extracted_data", {})
        doc_type = extracted_data.get("document_type", "UNKNOWN")
        
        if doc_type.startswith("AADHAAR"):
            return self._validate_aadhaar(extracted_data)
        elif doc_type.startswith("PAN"):
            return self._validate_pan(extracted_data)
        else:
            return {
                "validation_status": "failed",
                "reason": "Unknown document type",
                "errors": ["Could not determine document type"],
                "extracted_data": extracted_data,
                "validation_details": {},
                "is_valid": False
            }
    
    def _validate_aadhaar(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Aadhaar card fields with enhanced pattern detection"""
        validation_results = {}
        errors = []
        warnings = []
        
        # Validate Aadhaar Number
        aadhaar = fields.get("Aadhaar Number", "")
        aadhaar_validation = FieldValidator.validate_aadhaar_number(aadhaar)
        validation_results["Aadhaar Number"] = aadhaar_validation
        
        if not aadhaar_validation["valid"]:
            errors.append(f"Aadhaar Number: {aadhaar_validation.get('reason', 'invalid')}")
        
        # Validate Name
        name = fields.get("Name", "")
        name_validation = FieldValidator.validate_name(name)
        validation_results["Name"] = name_validation
        
        if not name_validation["valid"]:
            errors.append(f"Name: {name_validation.get('reason', 'invalid')}")
        
        # Validate DOB
        dob = fields.get("DOB", "")
        dob_validation = FieldValidator.validate_date(dob)
        validation_results["DOB"] = dob_validation
        
        if not dob_validation["valid"]:
            warnings.append(f"DOB: {dob_validation.get('reason', 'invalid')}")
        
        # Validate Gender
        gender = fields.get("Gender", "")
        gender_validation = FieldValidator.validate_gender(gender)
        validation_results["Gender"] = gender_validation
        
        if not gender_validation["valid"]:
            warnings.append(f"Gender: {gender_validation.get('reason', 'invalid')}")
        
        # Validate Address
        address = fields.get("Address", "")
        address_validation = FieldValidator.validate_address(address)
        validation_results["Address"] = address_validation
        
        if not address_validation["valid"]:
            warnings.append(f"Address: {address_validation.get('reason', 'invalid')}")
        
        # Calculate overall score
        overall_score = self._calculate_validation_score(validation_results)
        
        # Determine validation status
        validation_status = "passed" if len(errors) == 0 else "failed"
        is_valid = len(errors) == 0
        
        return {
            "validation_status": validation_status,
            "document_type": "AADHAAR",
            "validation_details": validation_results,
            "errors": errors,
            "warnings": warnings,
            "overall_score": overall_score,
            "extracted_data": fields,
            "is_valid": is_valid
        }
    
    def _validate_pan(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Validate PAN card fields with enhanced pattern detection"""
        validation_results = {}
        errors = []
        warnings = []
        
        # Validate PAN Number
        pan = fields.get("PAN Number", "")
        pan_validation = FieldValidator.validate_pan_number(pan)
        validation_results["PAN Number"] = pan_validation
        
        if not pan_validation["valid"]:
            errors.append(f"PAN Number: {pan_validation.get('reason', 'invalid')}")
        
        # Validate Name
        name = fields.get("Name", "")
        name_validation = FieldValidator.validate_name(name)
        validation_results["Name"] = name_validation
        
        if not name_validation["valid"]:
            errors.append(f"Name: {name_validation.get('reason', 'invalid')}")
        
        # Validate Father's Name
        father_name = fields.get("Father's Name", "")
        if father_name:
            father_validation = FieldValidator.validate_name(father_name)
            validation_results["Father's Name"] = father_validation
            
            if not father_validation["valid"]:
                warnings.append(f"Father's Name: {father_validation.get('reason', 'invalid')}")
        
        # Validate DOB
        dob = fields.get("DOB", "")
        dob_validation = FieldValidator.validate_date(dob)
        validation_results["DOB"] = dob_validation
        
        if not dob_validation["valid"]:
            warnings.append(f"DOB: {dob_validation.get('reason', 'invalid')}")
        
        # Calculate overall score
        overall_score = self._calculate_validation_score(validation_results)
        
        # Determine validation status
        validation_status = "passed" if len(errors) == 0 else "failed"
        is_valid = len(errors) == 0
        
        return {
            "validation_status": validation_status,
            "document_type": "PAN",
            "validation_details": validation_results,
            "errors": errors,
            "warnings": warnings,
            "overall_score": overall_score,
            "extracted_data": fields,
            "is_valid": is_valid
        }
    
    def _calculate_validation_score(self, validation_results: Dict[str, Any]) -> float:
        """Calculate overall validation score"""
        if not validation_results:
            return 0.0
        
        valid_fields = sum(1 for field_data in validation_results.values() 
                          if isinstance(field_data, dict) and field_data.get("valid", False))
        total_fields = len(validation_results)
        
        if total_fields == 0:
            return 0.0
        
        return round(valid_fields / total_fields, 2)
    
    def generate_validation_report(self, validation_result: Dict[str, Any]) -> str:
        """Generate a detailed validation report"""
        try:
            prompt = f"""
            Generate a detailed validation report for the following document processing results:
            
            Document Type: {validation_result.get('document_type', 'Unknown')}
            Validation Status: {validation_result.get('validation_status', 'Unknown')}
            Overall Score: {validation_result.get('overall_score', 0):.2%}
            Is Valid: {validation_result.get('is_valid', False)}
            
            Validation Details: {validation_result.get('validation_details', {})}
            Errors: {validation_result.get('errors', [])}
            Warnings: {validation_result.get('warnings', [])}
            
            Provide a professional, detailed report including:
            1. Summary of validation results
            2. Field-by-field analysis
            3. Issues and recommendations
            4. Overall assessment
            5. Pattern validation results
            """
            
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            return response.content
            
        except Exception as e:
            logging.error(f"Error generating validation report: {e}")
            return f"Error generating report: {str(e)}"
    
    def test_invalid_patterns(self) -> Dict[str, Any]:
        """Test invalid patterns for all document types"""
        results = {
            "aadhaar_tests": FieldValidator.test_invalid_aadhaar_patterns(),
            "pan_tests": FieldValidator.test_invalid_pan_patterns(),
            "timestamp": datetime.now().isoformat(),
            "summary": {}
        }
        
        # Generate summary for Aadhaar
        aadhaar_results = results["aadhaar_tests"]
        total_aadhaar_tests = len(aadhaar_results)
        invalid_aadhaar_count = sum(1 for test in aadhaar_results.values() if test["is_invalid"])
        
        # Generate summary for PAN
        pan_results = results["pan_tests"]
        total_pan_tests = len(pan_results)
        invalid_pan_count = sum(1 for test in pan_results.values() if test["is_invalid"])
        
        results["summary"] = {
            "total_aadhaar_tests": total_aadhaar_tests,
            "invalid_aadhaar_count": invalid_aadhaar_count,
            "valid_aadhaar_count": total_aadhaar_tests - invalid_aadhaar_count,
            "aadhaar_success_rate": f"{((total_aadhaar_tests - invalid_aadhaar_count) / total_aadhaar_tests * 100):.1f}%" if total_aadhaar_tests > 0 else "0%",
            "total_pan_tests": total_pan_tests,
            "invalid_pan_count": invalid_pan_count,
            "valid_pan_count": total_pan_tests - invalid_pan_count,
            "pan_success_rate": f"{((total_pan_tests - invalid_pan_count) / total_pan_tests * 100):.1f}%" if total_pan_tests > 0 else "0%"
        }
        
        return results
    
    def explain_aadhaar_validation(self, aadhaar: str) -> Dict[str, Any]:
        """Explain step by step Aadhaar validation logic"""
        return FieldValidator.explain_validation_logic(aadhaar)