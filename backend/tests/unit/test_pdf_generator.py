import pytest
from app.services.pdf_generator import PDFGenerator


class TestPDFGenerator:
    """Unit tests for PDFGenerator"""
    
    @pytest.fixture
    def pdf_generator(self):
        """Create PDFGenerator instance"""
        return PDFGenerator()
    
    @pytest.fixture
    def sample_case_data(self):
        """Sample case data for testing"""
        return {
            'case_id': 'test-123',
            'patient_name': 'John Doe',
            'soap_note': {
                'subjective': 'Patient reports chest pain',
                'objective': 'BP 140/90, HR 88',
                'assessment': 'NSTEMI',
                'plan': 'Admit to telemetry'
            },
            'clinical_entities': [
                {'type': 'lab_value', 'name': 'Troponin I', 'value': '0.14', 'unit': 'ng/mL'}
            ],
            'icd_codes': [
                {'code': 'BA41.1', 'description': 'Acute non-ST elevation myocardial infarction', 'specificity': 'high'}
            ],
            'preemptive_alerts': [
                {
                    'alert_type': 'MISSING_DATA',
                    'message': 'Troponin reference range not documented',
                    'action_required': 'Add reference ranges',
                    'urgency': 'before_submission'
                }
            ],
            'medical_necessity_score': 0.75,
            'denial_risk': 'medium'
        }
    
    @pytest.fixture
    def sample_denial_case(self):
        """Sample denial case data"""
        return {
            'case_id': 'test-456',
            'patient_name': 'Jane Smith',
            'denial_detected': True,
            'denial_reason': 'Medical necessity criteria not met for inpatient admission',
            'rebuttal_letter': '''# APPEAL LETTER

**Date:** January 10, 2026
**RE:** Appeal of Denial - Medical Necessity
**Patient:** Jane Smith

Dear Medical Director,

I am writing to formally appeal the denial.

## Rebuttal

The patient meets all medical necessity criteria.

Respectfully,
[Attending Physician]''',
            'talking_points': [
                'Patient meets medical necessity criteria',
                'Clinical documentation supports inpatient care',
                'Request peer-to-peer review'
            ]
        }
    
    def test_generate_audit_report_basic(self, pdf_generator, sample_case_data):
        """Test generating basic audit report"""
        pdf_bytes = pdf_generator.generate_audit_report(sample_case_data)
        
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b'%PDF')  # PDF magic number
    
    def test_generate_audit_report_missing_fields(self, pdf_generator):
        """Test audit report generation with missing fields"""
        minimal_case = {
            'case_id': 'test-min',
            'patient_name': 'Test Patient'
        }
        
        pdf_bytes = pdf_generator.generate_audit_report(minimal_case)
        
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
    
    def test_generate_rebuttal_letter_basic(self, pdf_generator, sample_denial_case):
        """Test generating basic rebuttal letter"""
        pdf_bytes = pdf_generator.generate_rebuttal_letter(sample_denial_case)
        
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b'%PDF')
    
    def test_generate_rebuttal_letter_with_talking_points(self, pdf_generator, sample_denial_case):
        """Test rebuttal letter with talking points"""
        sample_denial_case['talking_points'] = [
            'Point 1: Patient meets criteria',
            'Point 2: Documentation supports care',
            'Point 3: Request review'
        ]
        
        pdf_bytes = pdf_generator.generate_rebuttal_letter(sample_denial_case)
        
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
    
    def test_generate_rebuttal_letter_missing_patient_name(self, pdf_generator):
        """Test rebuttal letter with missing patient name"""
        case = {
            'case_id': 'test-789',
            'rebuttal_letter': 'Test appeal letter',
            'talking_points': []
        }
        
        pdf_bytes = pdf_generator.generate_rebuttal_letter(case)
        
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
    
    def test_generate_rebuttal_letter_empty_letter(self, pdf_generator):
        """Test rebuttal letter with empty letter content"""
        case = {
            'case_id': 'test-empty',
            'patient_name': 'Test Patient',
            'rebuttal_letter': '',
            'talking_points': []
        }
        
        pdf_bytes = pdf_generator.generate_rebuttal_letter(case)
        
        # Should still generate PDF even with empty content
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
    
    def test_pdf_generator_multiple_calls(self, pdf_generator, sample_case_data):
        """Test that PDFGenerator can be called multiple times"""
        pdf1 = pdf_generator.generate_audit_report(sample_case_data)
        pdf2 = pdf_generator.generate_audit_report(sample_case_data)
        
        assert pdf1 is not None
        assert pdf2 is not None
        # Should generate similar but not identical PDFs (timestamps differ)
        assert len(pdf1) > 0
        assert len(pdf2) > 0
