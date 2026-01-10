import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from io import BytesIO
from app.agents.scribe_agent import ScribeAgent
from app.agents.coder_agent import CoderAgent
from app.agents.intake_agent import IntakeAgent
from app.agents.rebuttal_agent import RebuttalAgent
from app.services.vector_db import PolicyVectorStore


class TestScribeAgent:
    """Unit tests for ScribeAgent"""
    
    @pytest.fixture
    def mock_speech_service(self):
        """Mock SpeechService"""
        with patch('app.agents.scribe_agent.SpeechService') as mock_service_class:
            mock_service = Mock()
            mock_service.transcribe_audio = AsyncMock(return_value="Test transcript")
            mock_service.extract_clinical_entities = AsyncMock(return_value={
                "soap_note": {"subjective": "Test", "objective": "Test", "assessment": "Test", "plan": "Test"},
                "clinical_entities": [{"type": "lab_value", "name": "K+", "value": "5.3", "unit": "mmol/L"}],
                "patient_info": {"name": "John Doe", "age": "67"},
                "proposed_treatments": ["Admit to telemetry"],
                "urgency_indicators": [],
                "chief_complaint": "Weakness"
            })
            mock_service_class.return_value = mock_service
            yield mock_service
    
    @pytest.mark.asyncio
    async def test_process_audio(self, mock_speech_service):
        """Test processing audio file"""
        agent = ScribeAgent()
        audio_file = BytesIO(b"fake audio data")
        
        result = await agent.process_audio(audio_file, "test.wav")
        
        assert "raw_transcript" in result
        assert "soap_note" in result
        assert "clinical_entities" in result
        assert result["raw_transcript"] == "Test transcript"
        mock_speech_service.transcribe_audio.assert_called_once()
        mock_speech_service.extract_clinical_entities.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_text(self, mock_speech_service):
        """Test processing text dictation"""
        agent = ScribeAgent()
        dictation = "Patient is a 67-year-old male with hyperkalemia."
        
        result = await agent.process_text(dictation)
        
        assert "raw_transcript" in result
        assert result["raw_transcript"] == dictation
        assert "soap_note" in result
        assert "clinical_entities" in result
        assert len(result["clinical_entities"]) > 0
        mock_speech_service.extract_clinical_entities.assert_called_once_with(dictation)
    
    @pytest.mark.asyncio
    async def test_process_text_handles_missing_fields(self, mock_speech_service):
        """Test that missing fields are handled gracefully"""
        mock_speech_service.extract_clinical_entities.return_value = {}
        agent = ScribeAgent()
        
        result = await agent.process_text("Test dictation")
        
        assert result["soap_note"] == {}
        assert result["clinical_entities"] == []
        assert result["proposed_treatments"] == []


class TestCoderAgent:
    """Unit tests for CoderAgent"""
    
    @pytest.fixture
    def mock_vector_store(self):
        """Mock PolicyVectorStore"""
        mock_store = Mock(spec=PolicyVectorStore)
        mock_store.query = AsyncMock(return_value="Policy context: Hyperkalemia requires K+ >= 5.5 mmol/L")
        return mock_store
    
    @pytest.fixture
    def mock_anthropic_client(self):
        """Mock Anthropic client"""
        with patch('app.agents.coder_agent.anthropic.AsyncAnthropic') as mock_client_class:
            mock_client = Mock()
            mock_response = Mock()
            mock_text = Mock()
            mock_text.text = '''{
                "icd_codes": [{"code": "E87.5", "description": "Hyperkalemia", "specificity": "high", "supporting_evidence": "K+ 5.3 mmol/L"}],
                "policy_gaps": [{"gap": "K+ below threshold", "required_by_policy": "K+ >= 5.5", "risk_level": "high", "suggested_fix": "Document EKG changes"}],
                "preemptive_alerts": [{"alert_type": "THRESHOLD_NOT_MET", "message": "K+ 5.3 below threshold", "action_required": "Document EKG changes", "urgency": "immediate"}],
                "medical_necessity_score": 0.6,
                "denial_risk": "medium",
                "recommendations": ["Document EKG changes"]
            }'''
            mock_response.content = [mock_text]
            mock_client.messages.create = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            yield mock_client
    
    @pytest.mark.asyncio
    async def test_process_audit(self, mock_vector_store, mock_anthropic_client):
        """Test processing clinical documentation audit"""
        with patch('app.agents.coder_agent.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.anthropic_api_key = "test-key"
            mock_get_settings.return_value = mock_settings
            
            agent = CoderAgent(mock_vector_store)
            
            soap_note = {
                "subjective": "Patient with weakness",
                "objective": "K+ 5.3 mmol/L, EKG shows peaked T waves",
                "assessment": "Hyperkalemia",
                "plan": "Admit to telemetry"
            }
            clinical_entities = [
                {"type": "lab_value", "name": "K+", "value": "5.3", "unit": "mmol/L"}
            ]
            
            result = await agent.process(soap_note, clinical_entities)
            
            assert "icd_codes" in result
            assert "policy_gaps" in result
            assert "preemptive_alerts" in result
            assert "medical_necessity_score" in result
            assert "denial_risk" in result
            assert len(result["icd_codes"]) > 0
            mock_vector_store.query.assert_called_once()
            mock_anthropic_client.messages.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_with_payer_filter(self, mock_vector_store, mock_anthropic_client):
        """Test processing with payer filter"""
        with patch('app.agents.coder_agent.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.anthropic_api_key = "test-key"
            mock_get_settings.return_value = mock_settings
            
            agent = CoderAgent(mock_vector_store)
            
            result = await agent.process(
                {"assessment": "Hyperkalemia"},
                [],
                payer="united_healthcare"
            )
            
            # Verify query was called with payer filter
            call_args = mock_vector_store.query.call_args
            assert call_args[1]["payer"] == "united_healthcare"
    
    def test_extract_diagnoses_from_soap(self):
        """Test extracting diagnoses from SOAP note"""
        with patch('app.agents.coder_agent.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.anthropic_api_key = "test-key"
            mock_get_settings.return_value = mock_settings
            
            agent = CoderAgent(Mock())
            
            soap_note = {"assessment": "Hyperkalemia with EKG changes"}
            entities = []
            
            diagnoses = agent._extract_diagnoses(soap_note, entities)
            
            assert "Hyperkalemia with EKG changes" in diagnoses
    
    def test_extract_diagnoses_from_entities(self):
        """Test extracting diagnoses from clinical entities"""
        with patch('app.agents.coder_agent.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.anthropic_api_key = "test-key"
            mock_get_settings.return_value = mock_settings
            
            agent = CoderAgent(Mock())
            
            soap_note = {}
            entities = [
                {"type": "diagnosis", "name": "Hyperkalemia"},
                {"type": "symptom", "name": "Weakness"},
                {"type": "lab_value", "name": "K+"}
            ]
            
            diagnoses = agent._extract_diagnoses(soap_note, entities)
            
            assert "Hyperkalemia" in diagnoses
            assert "Weakness" in diagnoses
            assert "K+" not in diagnoses  # lab_value should not be included
    
    def test_parse_json_response_with_markdown(self):
        """Test parsing JSON response with markdown"""
        with patch('app.agents.coder_agent.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.anthropic_api_key = "test-key"
            mock_get_settings.return_value = mock_settings
            
            agent = CoderAgent(Mock())
            
            text = '```json\n{"test": "value"}\n```'
            result = agent._parse_json_response(text)
            
            assert result == {"test": "value"}
    
    def test_parse_json_response_error_handling(self):
        """Test JSON parsing error handling"""
        with patch('app.agents.coder_agent.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.anthropic_api_key = "test-key"
            mock_get_settings.return_value = mock_settings
            
            agent = CoderAgent(Mock())
            
            invalid_json = "not valid json"
            result = agent._parse_json_response(invalid_json)
            
            assert "error" in result


class TestIntakeAgent:
    """Unit tests for IntakeAgent"""
    
    @pytest.fixture
    def mock_anthropic_client(self):
        """Mock Anthropic client"""
        with patch('app.agents.intake_agent.anthropic.AsyncAnthropic') as mock_client_class:
            mock_client = Mock()
            mock_response = Mock()
            mock_text = Mock()
            mock_text.text = '''{
                "document_type": "DENIAL",
                "patient_name": "John Smith",
                "account_number": "8847291",
                "denial_reason": "Patient's potassium level of 5.3 mmol/L does not meet threshold of ≥5.5 mmol/L",
                "denial_code": "E87.5",
                "appeal_deadline_days": 2,
                "peer_to_peer_available": true,
                "key_missing_criteria": ["K+ threshold not met"],
                "urgency": "P0_CRITICAL"
            }'''
            mock_response.content = [mock_text]
            mock_client.messages.create = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            yield mock_client
    
    @pytest.mark.asyncio
    async def test_process_pdf_denial(self, mock_anthropic_client):
        """Test processing denial PDF"""
        with patch('app.agents.intake_agent.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.anthropic_api_key = "test-key"
            mock_get_settings.return_value = mock_settings
            
            agent = IntakeAgent()
            pdf_bytes = b"fake pdf content"
            
            result = await agent.process(pdf_bytes)
            
            assert result["is_denial"] is True
            assert "denial_reason" in result
            assert result["denial_reason"] is not None
            assert "peer_to_peer_deadline" in result
            assert result["urgency"] == "P0_CRITICAL"
            mock_anthropic_client.messages.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_no_pdf(self, mock_anthropic_client):
        """Test processing with no PDF"""
        with patch('app.agents.intake_agent.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.anthropic_api_key = "test-key"
            mock_get_settings.return_value = mock_settings
            
            agent = IntakeAgent()
            
            result = await agent.process(None)
            
            assert result["is_denial"] is False
            assert "error" in result
            assert result["extraction"] is None
    
    @pytest.mark.asyncio
    async def test_process_approval(self, mock_anthropic_client):
        """Test processing approval document"""
        with patch('app.agents.intake_agent.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.anthropic_api_key = "test-key"
            mock_get_settings.return_value = mock_settings
            
            mock_text = Mock()
            mock_text.text = '{"document_type": "APPROVAL", "patient_name": "John"}'
            mock_response = Mock()
            mock_response.content = [mock_text]
            mock_anthropic_client.messages.create = AsyncMock(return_value=mock_response)
            
            agent = IntakeAgent()
            pdf_bytes = b"fake pdf"
            
            result = await agent.process(pdf_bytes)
            
            assert result["is_denial"] is False
    
    def test_parse_response_with_markdown(self):
        """Test parsing response with markdown"""
        with patch('app.agents.intake_agent.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.anthropic_api_key = "test-key"
            mock_get_settings.return_value = mock_settings
            
            agent = IntakeAgent()
            
            text = '```json\n{"document_type": "DENIAL"}\n```'
            result = agent._parse_response(text)
            
            assert result["document_type"] == "DENIAL"
    
    def test_parse_response_error_handling(self):
        """Test JSON parsing error handling"""
        with patch('app.agents.intake_agent.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.anthropic_api_key = "test-key"
            mock_get_settings.return_value = mock_settings
            
            agent = IntakeAgent()
            
            invalid_json = "not valid json"
            result = agent._parse_response(invalid_json)
            
            assert result["document_type"] == "OTHER"
            assert result["parse_error"] is True


class TestRebuttalAgent:
    """Unit tests for RebuttalAgent"""
    
    @pytest.fixture
    def mock_vector_store(self):
        """Mock PolicyVectorStore"""
        mock_store = Mock(spec=PolicyVectorStore)
        mock_store.query = AsyncMock(return_value="Policy: Hyperkalemia requires K+ >= 5.5 or EKG changes")
        return mock_store
    
    @pytest.fixture
    def mock_anthropic_client(self):
        """Mock Anthropic client"""
        with patch('app.agents.rebuttal_agent.anthropic.AsyncAnthropic') as mock_client_class:
            mock_client = Mock()
            
            # Mock letter response
            mock_letter_text = Mock()
            mock_letter_text.text = "# Appeal Letter\n\nFormal appeal content..."
            mock_letter_response = Mock()
            mock_letter_response.content = [mock_letter_text]
            
            # Mock P2P response
            mock_p2p_text = Mock()
            mock_p2p_text.text = '["Point 1", "Point 2", "Point 3"]'
            mock_p2p_response = Mock()
            mock_p2p_response.content = [mock_p2p_text]
            
            # Setup side_effect to return different responses
            mock_client.messages.create = AsyncMock(side_effect=[mock_letter_response, mock_p2p_response])
            mock_client_class.return_value = mock_client
            yield mock_client
    
    @pytest.mark.asyncio
    async def test_process_generate_rebuttal(self, mock_vector_store, mock_anthropic_client):
        """Test generating rebuttal letter and talking points"""
        with patch('app.agents.rebuttal_agent.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.anthropic_api_key = "test-key"
            mock_get_settings.return_value = mock_settings
            
            agent = RebuttalAgent(mock_vector_store)
            
            result = await agent.process(
                denial_reason="K+ 5.3 below threshold",
                patient_name="John Doe",
                clinical_context="EKG shows peaked T waves"
            )
            
            assert "letter" in result
            assert "talking_points" in result
            assert len(result["talking_points"]) == 3
            assert "confidence_score" in result
            assert result["confidence_score"] == 0.85
            assert mock_vector_store.query.called
            assert mock_anthropic_client.messages.create.call_count == 2
    
    @pytest.mark.asyncio
    async def test_process_with_extraction(self, mock_vector_store, mock_anthropic_client):
        """Test processing with extraction data"""
        with patch('app.agents.rebuttal_agent.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.anthropic_api_key = "test-key"
            mock_get_settings.return_value = mock_settings
            
            agent = RebuttalAgent(mock_vector_store)
            
            extraction = {
                "key_missing_criteria": ["K+ threshold not met", "EKG changes not documented"]
            }
            
            result = await agent.process(
                denial_reason="Test denial",
                extraction=extraction
            )
            
            assert "letter" in result
            assert "talking_points" in result
    
    def test_parse_talking_points_with_markdown(self):
        """Test parsing talking points with markdown"""
        with patch('app.agents.rebuttal_agent.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.anthropic_api_key = "test-key"
            mock_get_settings.return_value = mock_settings
            
            agent = RebuttalAgent(Mock())
            
            text = '```json\n["Point 1", "Point 2"]\n```'
            result = agent._parse_talking_points(text)
            
            assert result == ["Point 1", "Point 2"]
    
    def test_parse_talking_points_error_handling(self):
        """Test talking points parsing error handling"""
        with patch('app.agents.rebuttal_agent.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.anthropic_api_key = "test-key"
            mock_get_settings.return_value = mock_settings
            
            agent = RebuttalAgent(Mock())
            
            invalid_json = "not valid json"
            result = agent._parse_talking_points(invalid_json)
            
            # Should return as single item list
            assert isinstance(result, list)
            assert len(result) == 1
