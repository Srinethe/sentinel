import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.agents.orchestrator import SentinelOrchestrator
from app.services.vector_db import PolicyVectorStore


class TestWorkflows:
    """Integration tests for complete workflows"""
    
    @pytest.fixture
    def mock_vector_store(self):
        """Mock vector store"""
        return Mock(spec=PolicyVectorStore)
    
    @pytest.fixture
    def orchestrator(self, mock_vector_store):
        """Create orchestrator with mocked agents"""
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
                "preemptive_alerts": [{"alert_type": "THRESHOLD_NOT_MET", "message": "K+ below threshold"}],
                "medical_necessity_score": 0.6,
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
                "letter": "Appeal letter",
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
    async def test_dictation_workflow_integration(self, orchestrator):
        """Test complete dictation workflow end-to-end"""
        result = await orchestrator.process_dictation(
            case_id="test-123",
            patient_name="Test Patient",
            dictation_text="Patient with hyperkalemia, K+ 5.3 mmol/L"
        )
        
        assert "raw_transcript" in result
        assert "soap_note" in result
        assert "icd_codes" in result
        assert "preemptive_alerts" in result
        assert orchestrator.scribe.process_text.called
        assert orchestrator.coder.process.called
    
    @pytest.mark.asyncio
    async def test_denial_workflow_integration(self, orchestrator):
        """Test complete denial workflow end-to-end"""
        pdf_bytes = b"fake pdf content"
        result = await orchestrator.process_denial(
            case_id="test-456",
            patient_name="Test Patient",
            pdf_bytes=pdf_bytes
        )
        
        assert "denial_detected" in result
        assert result["denial_detected"] is True
        assert "rebuttal_letter" in result
        assert "talking_points" in result
        assert orchestrator.intake.process.called
        assert orchestrator.rebuttal.process.called
    
    @pytest.mark.asyncio
    async def test_full_workflow_integration(self, orchestrator):
        """Test complete full workflow end-to-end"""
        result = await orchestrator.process_full_case(
            case_id="test-789",
            patient_name="Test Patient",
            dictation_text="Test dictation",
            pdf_bytes=b"fake pdf"
        )
        
        # Verify all agents were called
        assert orchestrator.scribe.process_text.called
        assert orchestrator.coder.process.called
        assert orchestrator.intake.process.called
        assert orchestrator.rebuttal.process.called
        
        # Verify result contains outputs from all agents
        assert "raw_transcript" in result
        assert "icd_codes" in result
        assert "denial_detected" in result
        assert "rebuttal_letter" in result
