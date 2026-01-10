import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from io import BytesIO
from app.services.speech_service import SpeechService
from app.services.vector_db import PolicyVectorStore


@pytest.fixture
def mock_settings():
    """Mock settings for testing"""
    with patch('app.services.speech_service.get_settings') as mock_get:
        mock_settings = Mock()
        mock_settings.openai_api_key = "test-openai-key"
        mock_settings.anthropic_api_key = "test-anthropic-key"
        mock_get.return_value = mock_settings
        yield mock_settings


@pytest.fixture
def mock_vector_settings():
    """Mock settings for vector store"""
    with patch('app.services.vector_db.get_settings') as mock_get:
        mock_settings = Mock()
        mock_settings.openai_api_key = "test-openai-key"
        mock_get.return_value = mock_settings
        yield mock_settings


class TestSpeechService:
    """Unit tests for SpeechService"""
    
    @pytest.mark.asyncio
    async def test_transcribe_audio(self, mock_settings):
        """Test audio transcription"""
        service = SpeechService()
        
        # Mock OpenAI client
        mock_transcript = "Patient is a 67-year-old male with hyperkalemia."
        service.openai_client.audio.transcriptions.create = AsyncMock(return_value=mock_transcript)
        
        audio_file = BytesIO(b"fake audio data")
        result = await service.transcribe_audio(audio_file, "test.wav")
        
        assert result == mock_transcript
        service.openai_client.audio.transcriptions.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_extract_clinical_entities(self, mock_settings):
        """Test clinical entity extraction"""
        service = SpeechService()
        
        # Mock Anthropic response
        mock_response = Mock()
        mock_text = Mock()
        mock_text.text = '{"patient_info": {"name": "John"}, "clinical_entities": []}'
        mock_response.content = [mock_text]
        
        service.anthropic_client.messages.create = AsyncMock(return_value=mock_response)
        
        transcript = "Patient is a 67-year-old male with hyperkalemia."
        result = await service.extract_clinical_entities(transcript)
        
        assert "patient_info" in result
        assert "clinical_entities" in result
        service.anthropic_client.messages.create.assert_called_once()
    
    def test_parse_json_response_with_markdown(self, mock_settings):
        """Test JSON parsing with markdown code blocks"""
        service = SpeechService()
        
        text_with_markdown = '```json\n{"test": "value"}\n```'
        result = service._parse_json_response(text_with_markdown)
        
        assert result == {"test": "value"}
    
    def test_parse_json_response_without_markdown(self, mock_settings):
        """Test JSON parsing without markdown"""
        service = SpeechService()
        
        text = '{"test": "value"}'
        result = service._parse_json_response(text)
        
        assert result == {"test": "value"}
    
    def test_parse_json_response_error_handling(self, mock_settings):
        """Test JSON parsing error handling"""
        service = SpeechService()
        
        invalid_json = "not valid json"
        result = service._parse_json_response(invalid_json)
        
        assert "error" in result


class TestPolicyVectorStore:
    """Unit tests for PolicyVectorStore"""
    
    def test_init(self, mock_vector_settings):
        """Test vector store initialization"""
        with patch('app.services.vector_db.chromadb.Client') as mock_client:
            with patch('app.services.vector_db.embedding_functions.OpenAIEmbeddingFunction') as mock_embed:
                store = PolicyVectorStore()
                
                assert store._loaded is False
                mock_client.assert_called_once()
                mock_embed.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_load_policies(self, mock_vector_settings, tmp_path):
        """Test loading policies from directory"""
        # Create test policy file
        policy_file = tmp_path / "test_payer.txt"
        policy_file.write_text("Test policy content for hyperkalemia management.")
        
        with patch('app.services.vector_db.chromadb.Client') as mock_client:
            mock_collection = Mock()
            mock_client_instance = Mock()
            mock_client_instance.create_collection.return_value = mock_collection
            mock_client.return_value = mock_client_instance
            
            with patch('app.services.vector_db.embedding_functions.OpenAIEmbeddingFunction'):
                store = PolicyVectorStore()
                store.collection = mock_collection
                
                await store.load_policies(str(tmp_path))
                
                assert store._loaded is True
                # Verify add was called (collection.add should be called with documents)
                # The exact call depends on chunking, but we can verify it was called
                assert mock_collection.add.called
    
    @pytest.mark.asyncio
    async def test_query_no_results(self, mock_vector_settings):
        """Test query with no results"""
        with patch('app.services.vector_db.chromadb.Client') as mock_client:
            mock_collection = Mock()
            mock_collection.query.return_value = {"documents": [[]], "metadatas": [[]]}
            mock_client_instance = Mock()
            mock_client_instance.create_collection.return_value = mock_collection
            mock_client.return_value = mock_client_instance
            
            with patch('app.services.vector_db.embedding_functions.OpenAIEmbeddingFunction'):
                store = PolicyVectorStore()
                store.collection = mock_collection
                
                result = await store.query("test query")
                
                assert result == "No relevant policy sections found."
    
    @pytest.mark.asyncio
    async def test_query_with_results(self, mock_vector_settings):
        """Test query with results"""
        with patch('app.services.vector_db.chromadb.Client') as mock_client:
            mock_collection = Mock()
            mock_collection.query.return_value = {
                "documents": [["Policy text 1", "Policy text 2"]],
                "metadatas": [[{"payer": "test_payer", "chunk_id": 0}, {"payer": "test_payer", "chunk_id": 1}]]
            }
            mock_client_instance = Mock()
            mock_client_instance.create_collection.return_value = mock_collection
            mock_client.return_value = mock_client_instance
            
            with patch('app.services.vector_db.embedding_functions.OpenAIEmbeddingFunction'):
                store = PolicyVectorStore()
                store.collection = mock_collection
                
                result = await store.query("test query", top_k=2)
                
                assert "test_payer" in result
                assert "Policy text 1" in result
                assert "Policy text 2" in result
    
    @pytest.mark.asyncio
    async def test_query_with_payer_filter(self, mock_vector_settings):
        """Test query with payer filter"""
        with patch('app.services.vector_db.chromadb.Client') as mock_client:
            mock_collection = Mock()
            mock_collection.query.return_value = {
                "documents": [["Policy text"]],
                "metadatas": [[{"payer": "united_healthcare", "chunk_id": 0}]]
            }
            mock_client_instance = Mock()
            mock_client_instance.create_collection.return_value = mock_collection
            mock_client.return_value = mock_client_instance
            
            with patch('app.services.vector_db.embedding_functions.OpenAIEmbeddingFunction'):
                store = PolicyVectorStore()
                store.collection = mock_collection
                
                await store.query("test query", payer="united_healthcare")
                
                # Verify query was called with where filter
                call_args = mock_collection.query.call_args
                assert call_args[1]["where"] == {"payer": "united_healthcare"}
