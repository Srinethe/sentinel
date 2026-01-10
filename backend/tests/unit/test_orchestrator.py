import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.agents.orchestrator import SentinelOrchestrator, SentinelState
from app.services.vector_db import PolicyVectorStore


class TestSentinelOrchestrator:
    """Unit tests for SentinelOrchestrator"""
    
    @pytest.fixture
    def mock_vector_store(self):
        """Mock PolicyVectorStore"""
        return Mock(spec=PolicyVectorStore)
    
    @pytest.fixture
    def orchestrator(self, mock_vector_store):
        """Create orchestrator with mocked dependencies"""
        with patch('app.agents.orchestrator.ScribeAgent') as mock_scribe_class, \
             patch('app.agents.orchestrator.CoderAgent') as mock_coder_class, \
             patch('app.agents.orchestrator.IntakeAgent') as mock_intake_class, \
             patch('app.agents.orchestrator.RebuttalAgent') as mock_rebuttal_class:
            
            mock_scribe = Mock()
            mock_scribe.process_text = AsyncMock(return_value={
                "raw_transcript": "Test dictation",
                "soap_note": {"assessment": "Hyperkalemia"},
                "clinical_entities": [{"type": "lab_value", "name": "K+", "value": "5.3"}],
                "proposed_treatments": [],
                "chief_complaint": "Weakness"
            })
            mock_scribe_class.return_value = mock_scribe
            
            mock_coder = Mock()
            mock_coder.process = AsyncMock(return_value={
                "icd_codes": [{"code": "E87.5"}],
                "policy_gaps": [],
                "preemptive_alerts": [],
                "medical_necessity_score": 0.7,
                "denial_risk": "medium"
            })
            mock_coder_class.return_value = mock_coder
            
            mock_intake = Mock()
            mock_intake.process = AsyncMock(return_value={
                "is_denial": True,
                "denial_reason": "K+ below threshold",
                "peer_to_peer_deadline": "2026-01-10T12:00:00",
                "extraction": {}
            })
            mock_intake_class.return_value = mock_intake
            
            mock_rebuttal = Mock()
            mock_rebuttal.process = AsyncMock(return_value={
                "letter": "Appeal letter content",
                "talking_points": ["Point 1", "Point 2", "Point 3"],
                "confidence_score": 0.85
            })
            mock_rebuttal_class.return_value = mock_rebuttal
            
            orch = SentinelOrchestrator(mock_vector_store)
            orch.scribe = mock_scribe
            orch.coder = mock_coder
            orch.intake = mock_intake
            orch.rebuttal = mock_rebuttal
            return orch
    
    @pytest.mark.asyncio
    async def test_process_dictation(self, orchestrator):
        """Test dictation workflow"""
        result = await orchestrator.process_dictation(
            case_id="test-123",
            patient_name="John Doe",
            dictation_text="Patient with hyperkalemia"
        )
        
        assert "raw_transcript" in result
        assert "soap_note" in result
        assert "icd_codes" in result
        assert orchestrator.scribe.process_text.called
        assert orchestrator.coder.process.called
    
    @pytest.mark.asyncio
    async def test_process_denial(self, orchestrator):
        """Test denial workflow"""
        pdf_bytes = b"fake pdf content"
        result = await orchestrator.process_denial(
            case_id="test-456",
            patient_name="Jane Doe",
            pdf_bytes=pdf_bytes
        )
        
        assert "denial_detected" in result
        assert result["denial_detected"] is True
        assert "rebuttal_letter" in result
        assert orchestrator.intake.process.called
        assert orchestrator.rebuttal.process.called
    
    @pytest.mark.asyncio
    async def test_process_full_case(self, orchestrator):
        """Test full workflow"""
        result = await orchestrator.process_full_case(
            case_id="test-789",
            patient_name="Test Patient",
            dictation_text="Test dictation",
            pdf_bytes=b"fake pdf"
        )
        
        assert "raw_transcript" in result
        assert "denial_detected" in result
        assert "rebuttal_letter" in result
        assert orchestrator.scribe.process_text.called
        assert orchestrator.coder.process.called
        assert orchestrator.intake.process.called
        assert orchestrator.rebuttal.process.called
    
    def test_route_after_coder_with_pdf(self, orchestrator):
        """Test routing after coder when PDF is present"""
        state: SentinelState = {
            "case_id": "test",
            "patient_name": "Test",
            "pdf_bytes": b"fake pdf",
            "workflow_type": "full",
            "raw_transcript": "",
            "soap_note": {},
            "clinical_entities": [],
            "proposed_treatments": [],
            "chief_complaint": "",
            "icd_codes": [],
            "policy_gaps": [],
            "preemptive_alerts": [],
            "medical_necessity_score": 0.0,
            "denial_risk": "",
            "denial_detected": False,
            "denial_reason": "",
            "peer_to_peer_deadline": "",
            "denial_extraction": {},
            "rebuttal_letter": "",
            "talking_points": [],
            "current_agent": "",
            "agent_logs": [],
            "error": ""
        }
        
        route = orchestrator._route_after_coder(state)
        assert route == "process_denial"
    
    def test_route_after_coder_without_pdf(self, orchestrator):
        """Test routing after coder when no PDF"""
        state: SentinelState = {
            "case_id": "test",
            "patient_name": "Test",
            "pdf_bytes": None,
            "workflow_type": "dictation",
            "raw_transcript": "",
            "soap_note": {},
            "clinical_entities": [],
            "proposed_treatments": [],
            "chief_complaint": "",
            "icd_codes": [],
            "policy_gaps": [],
            "preemptive_alerts": [],
            "medical_necessity_score": 0.0,
            "denial_risk": "",
            "denial_detected": False,
            "denial_reason": "",
            "peer_to_peer_deadline": "",
            "denial_extraction": {},
            "rebuttal_letter": "",
            "talking_points": [],
            "current_agent": "",
            "agent_logs": [],
            "error": ""
        }
        
        route = orchestrator._route_after_coder(state)
        assert route == "end"
    
    def test_route_after_intake_with_denial(self, orchestrator):
        """Test routing after intake when denial detected"""
        state: SentinelState = {
            "case_id": "test",
            "patient_name": "Test",
            "pdf_bytes": None,
            "workflow_type": "denial",
            "raw_transcript": "",
            "soap_note": {},
            "clinical_entities": [],
            "proposed_treatments": [],
            "chief_complaint": "",
            "icd_codes": [],
            "policy_gaps": [],
            "preemptive_alerts": [],
            "medical_necessity_score": 0.0,
            "denial_risk": "",
            "denial_detected": True,
            "denial_reason": "Test denial",
            "peer_to_peer_deadline": "",
            "denial_extraction": {},
            "rebuttal_letter": "",
            "talking_points": [],
            "current_agent": "",
            "agent_logs": [],
            "error": ""
        }
        
        route = orchestrator._route_after_intake(state)
        assert route == "generate_rebuttal"
    
    def test_route_after_intake_without_denial(self, orchestrator):
        """Test routing after intake when no denial"""
        state: SentinelState = {
            "case_id": "test",
            "patient_name": "Test",
            "pdf_bytes": None,
            "workflow_type": "denial",
            "raw_transcript": "",
            "soap_note": {},
            "clinical_entities": [],
            "proposed_treatments": [],
            "chief_complaint": "",
            "icd_codes": [],
            "policy_gaps": [],
            "preemptive_alerts": [],
            "medical_necessity_score": 0.0,
            "denial_risk": "",
            "denial_detected": False,
            "denial_reason": "",
            "peer_to_peer_deadline": "",
            "denial_extraction": {},
            "rebuttal_letter": "",
            "talking_points": [],
            "current_agent": "",
            "agent_logs": [],
            "error": ""
        }
        
        route = orchestrator._route_after_intake(state)
        assert route == "end"
    
    def test_subscribe_unsubscribe(self, orchestrator):
        """Test WebSocket subscription"""
        case_id = "test-case"
        
        queue = orchestrator.subscribe(case_id)
        assert case_id in orchestrator.active_streams
        assert orchestrator.active_streams[case_id] == queue
        
        orchestrator.unsubscribe(case_id)
        assert case_id not in orchestrator.active_streams
    
    def test_format_entities(self, orchestrator):
        """Test entity formatting"""
        entities = [
            {"name": "K+", "value": "5.3", "unit": "mmol/L"},
            {"name": "Creatinine", "value": "2.8", "unit": "mg/dL"}
        ]
        
        formatted = orchestrator._format_entities(entities)
        assert "K+" in formatted
        assert "5.3" in formatted
        assert "mmol/L" in formatted
    
    def test_format_entities_empty(self, orchestrator):
        """Test formatting empty entities"""
        formatted = orchestrator._format_entities([])
        assert formatted == "None extracted"
