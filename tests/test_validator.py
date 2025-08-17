import unittest
from agents.validator_agent import ValidatorAgent

class TestValidatorAgent(unittest.TestCase):
    def setUp(self):
        self.validator = ValidatorAgent()
    
    def test_validate_aadhaar_success(self):
        """Test successful Aadhaar validation"""
        fields = {
            'document_type': 'AADHAAR',
            'Aadhaar Number': '123456789012',
            'Name': 'John Doe',
            'DOB': '15/08/1990',
            'Gender': 'Male'
        }
        
        extraction_result = {
            'status': 'success',
            'extracted_data': fields
        }
        
        result = self.validator.validate(extraction_result)
        self.assertIn('validation_status', result)
        self.assertIn('validation_details', result)
    
    def test_validate_pan_success(self):
        """Test successful PAN validation"""
        fields = {
            'document_type': 'PAN',
            'PAN Number': 'ABCDE1234F',
            'Name': 'Jane Smith',
            'Father\'s Name': 'Robert Smith'
        }
        
        extraction_result = {
            'status': 'success',
            'extracted_data': fields
        }
        
        result = self.validator.validate(extraction_result)
        self.assertIn('validation_status', result)
        self.assertIn('validation_details', result)
    
    def test_validate_date(self):
        """Test date validation"""
        # Valid dates
        valid_dates = ['15/08/1990', '01-01-2000', '31/12/1985']
        for date in valid_dates:
            result = self.validator._validate_date(date)
            self.assertTrue(result['valid'], f"Date {date} should be valid")
        
        # Invalid dates
        invalid_dates = ['32/01/1990', '15/13/1990', 'invalid-date', '2025/01/01']
        for date in invalid_dates:
            result = self.validator._validate_date(date)
            self.assertFalse(result['valid'], f"Date {date} should be invalid")
    
    def test_validate_aadhaar_number_format(self):
        """Test Aadhaar number format validation"""
        # Valid formats
        valid_aadhaar = ['123456789012', '1234 5678 9012', '1234-5678-9012']
        for aadhaar in valid_aadhaar:
            fields = {'document_type': 'AADHAAR', 'Aadhaar Number': aadhaar}
            extraction_result = {'status': 'success', 'extracted_data': fields}
            result = self.validator.validate(extraction_result)
            # Should pass basic format validation
            self.assertIsNotNone(result['validation_details'].get('Aadhaar Number'))
        
        # Invalid formats
        invalid_aadhaar = ['12345678901', '1234567890123', 'abcd5678efgh']
        for aadhaar in invalid_aadhaar:
            fields = {'document_type': 'AADHAAR', 'Aadhaar Number': aadhaar}
            extraction_result = {'status': 'success', 'extracted_data': fields}
            result = self.validator.validate(extraction_result)
            self.assertEqual(result['validation_status'], 'failed')
    
    def test_validate_pan_format(self):
        """Test PAN format validation"""
        # Valid PAN
        valid_pan = ['ABCDE1234F', 'PQRST5678G']
        for pan in valid_pan:
            fields = {'document_type': 'PAN', 'PAN Number': pan, 'Name': 'Test Name'}
            extraction_result = {'status': 'success', 'extracted_data': fields}
            result = self.validator.validate(extraction_result)
            pan_validation = result['validation_details'].get('PAN Number', {})
            self.assertTrue(pan_validation.get('valid', False), f"PAN {pan} should be valid")
        
        # Invalid PAN
        invalid_pan = ['ABC123DEF', '12345ABCDE', 'ABCDE12345']
        for pan in invalid_pan:
            fields = {'document_type': 'PAN', 'PAN Number': pan, 'Name': 'Test Name'}
            extraction_result = {'status': 'success', 'extracted_data': fields}
            result = self.validator.validate(extraction_result)
            pan_validation = result['validation_details'].get('PAN Number', {})
            self.assertFalse(pan_validation.get('valid', True), f"PAN {pan} should be invalid")

if __name__ == '__main__':
    unittest.main()
