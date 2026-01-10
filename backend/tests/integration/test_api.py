import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
from app.main import app
from app.agents.orchestrator import SentinelOrchestrator
from app.services.vector_db import PolicyVectorStore


@pytest.fixture
def mock_orchestrator():
    """Mock orchestrator for testing"""
    with patch('app.main.SentinelOrchestrator') as mock_class:
        mock_orch = Mock(spec=SentinelOrchestrator)
        mock_orch.process_dictation = AsyncMock(return_value={
            "raw_transcript": "Test transcript",
            "soap_note": {"assessment": "Hyperkalemia"},
            "clinical_entities": [{"type": "lab_value", "name": "K+", "value": "5.3"}],
            "icd_codes": [{"code": "E87.5"}],
            "policy_gaps": [],
            "preemptive_alerts": [],
            "denial_risk": "medium",
            "medical_necessity_score": 0.7
        })
        mock_orch.process_denial = AsyncMock(return_value={
            "denial_detected": True,
            "denial_reason": "K+ below threshold",
            "peer_to_peer_deadline": "2026-01-10T12:00:00",
            "rebuttal_letter": "Appeal letter",
            "talking_points": ["Point 1", "Point 2", "Point 3"],
            "denial_extraction": {}
        })
        mock_orch.process_full_case = AsyncMock(return_value={
            "raw_transcript": "Test",
            "denial_detected": True,
            "rebuttal_letter": "Appeal"
        })
        mock_orch.subscribe = Mock(return_value=Mock())
        mock_orch.unsubscribe = Mock()
        mock_class.return_value = mock_orch
        yield mock_orch


@pytest.fixture
def client(mock_orchestrator):
    """Test client with mocked dependencies"""
    with patch('app.main.PolicyVectorStore') as mock_vector_class:
        mock_vector = Mock(spec=PolicyVectorStore)
        mock_vector.load_policies = AsyncMock()
        mock_vector_class.return_value = mock_vector
        
        # Override app state
        app.state.vector_store = mock_vector
        app.state.orchestrator = mock_orchestrator
        
        yield TestClient(app)


class TestHealthEndpoints:
    """Test health and info endpoints"""
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "agents" in data
    
    def test_health_endpoint(self, client):
        """Test health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestDictationEndpoints:
    """Test dictation workflow endpoints"""
    
    def test_process_text_dictation(self, client, mock_orchestrator):
        """Test text dictation endpoint"""
        response = client.post(
            "/api/dictation/text",
            data={"dictation": "Test dictation", "patient_name": "Test Patient"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "case_id" in data
        assert data["workflow"] == "dictation"
        assert "transcript" in data
        assert "soap_note" in data
        mock_orchestrator.process_dictation.assert_called_once()
    
    def test_process_audio_dictation(self, client, mock_orchestrator):
        """Test audio dictation endpoint"""
        audio_content = b"fake audio data"
        response = client.post(
            "/api/dictation/audio",
            files={"audio": ("test.wav", audio_content, "audio/wav")},
            data={"patient_name": "Test Patient"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "case_id" in data
        assert data["workflow"] == "dictation"


class TestDenialEndpoints:
    """Test denial workflow endpoints"""
    
    def test_process_denial_pdf(self, client, mock_orchestrator):
        """Test denial PDF processing"""
        pdf_content = b"fake pdf content"
        response = client.post(
            "/api/denial/process",
            files={"file": ("denial.pdf", pdf_content, "application/pdf")},
            data={"patient_name": "Test Patient"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "case_id" in data
        assert data["workflow"] == "denial"
        assert "denial_detected" in data
        mock_orchestrator.process_denial.assert_called_once()
    
    def test_process_denial_invalid_file(self, client):
        """Test denial endpoint with invalid file type"""
        response = client.post(
            "/api/denial/process",
            files={"file": ("test.txt", b"content", "text/plain")},
            data={"patient_name": "Test Patient"}
        )
        assert response.status_code == 400


class TestCaseEndpoints:
    """Test case retrieval endpoints"""
    
    def test_get_case_not_found(self, client):
        """Test getting non-existent case"""
        response = client.get("/api/cases/nonexistent")
        assert response.status_code == 404
    
    def test_get_case_found(self, client):
        """Test getting existing case"""
        # First create a case
        from app.main import cases_store
        cases_store["test-case"] = {"case_id": "test-case", "patient_name": "Test"}
        
        response = client.get("/api/cases/test-case")
        assert response.status_code == 200
        data = response.json()
        assert data["case_id"] == "test-case"


class TestDemoEndpoints:
    """Test demo endpoints"""
    
    def test_demo_dictation(self, client, mock_orchestrator):
        """Test dictation demo endpoint"""
        response = client.post("/api/demo/dictation")
        assert response.status_code == 200
        data = response.json()
        assert "case_id" in data
        assert data["workflow"] == "dictation_demo"
        mock_orchestrator.process_dictation.assert_called_once()
    
    def test_demo_full(self, client, mock_orchestrator):
        """Test full demo endpoint"""
        response = client.post("/api/demo/full")
        assert response.status_code == 200
        data = response.json()
        assert "case_id" in data
        assert data["workflow"] == "full_demo"
        mock_orchestrator.process_dictation.assert_called_once()
