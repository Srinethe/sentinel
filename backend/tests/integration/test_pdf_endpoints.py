import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
from app.main import app, cases_store
from app.services.pdf_generator import PDFGenerator


@pytest.fixture
def mock_orchestrator():
    """Mock orchestrator"""
    with patch('app.main.SentinelOrchestrator') as mock_class:
        mock_orch = Mock()
        mock_orch.process_denial = AsyncMock(return_value={
            "denial_detected": True,
            "denial_reason": "Medical necessity criteria not met",
            "peer_to_peer_deadline": "2026-01-10T12:00:00",
            "rebuttal_letter": "# APPEAL LETTER\n\nTest appeal content",
            "talking_points": ["Point 1", "Point 2"],
            "denial_extraction": {}
        })
        mock_class.return_value = mock_orch
        yield mock_orch


@pytest.fixture
def client(mock_orchestrator):
    """Test client"""
    with patch('app.main.PolicyVectorStore') as mock_vector_class:
        mock_vector = Mock()
        mock_vector.load_policies = AsyncMock()
        mock_vector_class.return_value = mock_vector
        
        # Clear cases_store for clean tests
        from app.main import cases_store
        cases_store.clear()
        
        # Initialize app state if not already set
        if not hasattr(app.state, 'vector_store'):
            app.state.vector_store = mock_vector
        else:
            app.state.vector_store = mock_vector
            
        if not hasattr(app.state, 'orchestrator'):
            app.state.orchestrator = mock_orchestrator
        else:
            app.state.orchestrator = mock_orchestrator
            
        if not hasattr(app.state, 'pdf_generator'):
            app.state.pdf_generator = PDFGenerator()
        else:
            app.state.pdf_generator = PDFGenerator()
        
        yield TestClient(app)
        
        # Cleanup
        cases_store.clear()


class TestPDFEndpoints:
    """Integration tests for PDF download endpoints"""
    
    def test_audit_report_pdf_success(self, client):
        """Test successful audit report PDF download"""
        # Create a case in the store
        case_id = "test-audit-123"
        cases_store[case_id] = {
            'case_id': case_id,
            'patient_name': 'Test Patient',
            'soap_note': {'assessment': 'NSTEMI'},
            'icd_codes': [{'code': 'BA41.1', 'description': 'NSTEMI'}],
            'preemptive_alerts': [],
            'medical_necessity_score': 0.75,
            'denial_risk': 'medium'
        }
        
        response = client.get(f"/api/case/{case_id}/audit-report")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert len(response.content) > 0
        assert response.content.startswith(b'%PDF')
    
    def test_audit_report_pdf_case_not_found(self, client):
        """Test audit report PDF with non-existent case"""
        response = client.get("/api/case/nonexistent/audit-report")
        
        assert response.status_code == 404
    
    def test_rebuttal_pdf_success(self, client):
        """Test successful rebuttal PDF download"""
        case_id = "test-rebuttal-456"
        cases_store[case_id] = {
            'case_id': case_id,
            'patient_name': 'Test Patient',
            'denial_detected': True,
            'denial_reason': 'Medical necessity not met',
            'rebuttal_letter': '# APPEAL LETTER\n\nTest appeal content',
            'talking_points': ['Point 1', 'Point 2']
        }
        
        response = client.get(f"/api/case/{case_id}/rebuttal-pdf")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert len(response.content) > 0
        assert response.content.startswith(b'%PDF')
    
    def test_rebuttal_pdf_case_not_found(self, client):
        """Test rebuttal PDF with non-existent case"""
        response = client.get("/api/case/nonexistent/rebuttal-pdf")
        
        assert response.status_code == 404
    
    def test_rebuttal_pdf_generates_from_denial_reason(self, client):
        """Test that rebuttal PDF is generated from denial_reason if letter missing"""
        case_id = "test-rebuttal-gen-789"
        cases_store[case_id] = {
            'case_id': case_id,
            'patient_name': 'Test Patient',
            'denial_detected': True,
            'denial_reason': 'Medical necessity criteria not met for inpatient admission',
            'rebuttal_letter': '',  # Empty but denial_reason exists
            'talking_points': []
        }
        
        response = client.get(f"/api/case/{case_id}/rebuttal-pdf")
        
        # Should generate PDF from denial_reason
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert len(response.content) > 0
    
    def test_rebuttal_pdf_no_denial_reason(self, client):
        """Test rebuttal PDF when no denial_reason available"""
        case_id = "test-rebuttal-no-reason"
        cases_store[case_id] = {
            'case_id': case_id,
            'patient_name': 'Test Patient',
            'denial_detected': True,
            'rebuttal_letter': '',  # Empty
            'denial_reason': None  # No denial reason
        }
        
        response = client.get(f"/api/case/{case_id}/rebuttal-pdf")
        
        assert response.status_code == 400
    
    def test_rebuttal_pdf_partial_case_id_match(self, client):
        """Test rebuttal PDF with partial case ID match"""
        full_case_id = "abc12345"
        cases_store[full_case_id] = {
            'case_id': full_case_id,
            'patient_name': 'Test Patient',
            'rebuttal_letter': 'Test appeal',
            'talking_points': []
        }
        
        # Try with partial ID
        response = client.get(f"/api/case/abc123/rebuttal-pdf")
        
        # Should find by partial match
        assert response.status_code == 200
    
    def test_audit_report_pdf_with_all_fields(self, client):
        """Test audit report with all possible fields"""
        case_id = "test-complete-123"
        cases_store[case_id] = {
            'case_id': case_id,
            'patient_name': 'Complete Patient',
            'soap_note': {
                'subjective': 'Chest pain',
                'objective': 'BP 140/90',
                'assessment': 'NSTEMI',
                'plan': 'Admit'
            },
            'clinical_entities': [
                {'type': 'lab_value', 'name': 'Troponin', 'value': '0.14', 'unit': 'ng/mL'}
            ],
            'icd_codes': [
                {'code': 'BA41.1', 'description': 'NSTEMI', 'specificity': 'high'}
            ],
            'policy_gaps': [
                {'gap': 'Missing reference range', 'risk_level': 'medium'}
            ],
            'preemptive_alerts': [
                {'alert_type': 'MISSING_DATA', 'message': 'Add reference ranges', 'urgency': 'before_submission'}
            ],
            'medical_necessity_score': 0.85,
            'denial_risk': 'low'
        }
        
        response = client.get(f"/api/case/{case_id}/audit-report")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
