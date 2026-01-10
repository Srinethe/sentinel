from app.services.speech_service import SpeechService
from typing import BinaryIO, Optional


class ScribeAgent:
    """
    Agent 1: The Ear - Ambient Scribe
    
    Listens to physician-patient encounters and dictations,
    transcribes speech to text, and extracts structured clinical data.
    """
    
    def __init__(self):
        self.speech_service = SpeechService()
    
    async def process_audio(self, audio_file: BinaryIO, filename: str = "dictation.wav") -> dict:
        """
        Process audio recording from physician dictation or patient encounter.
        
        Returns structured clinical data including SOAP note and entities.
        """
        # Step 1: Transcribe audio to text using Whisper
        transcript = await self.speech_service.transcribe_audio(audio_file, filename)
        
        # Step 2: Extract clinical entities and generate SOAP note
        extraction = await self.speech_service.extract_clinical_entities(transcript)
        
        return {
            "raw_transcript": transcript,
            "soap_note": extraction.get("soap_note", {}),
            "clinical_entities": extraction.get("clinical_entities", []),
            "patient_info": extraction.get("patient_info", {}),
            "proposed_treatments": extraction.get("proposed_treatments", []),
            "urgency_indicators": extraction.get("urgency_indicators", []),
            "chief_complaint": extraction.get("chief_complaint", "")
        }
    
    async def process_text(self, dictation_text: str) -> dict:
        """
        Process text dictation directly (for demo/testing without audio).
        """
        extraction = await self.speech_service.extract_clinical_entities(dictation_text)
        
        return {
            "raw_transcript": dictation_text,
            "soap_note": extraction.get("soap_note", {}),
            "clinical_entities": extraction.get("clinical_entities", []),
            "patient_info": extraction.get("patient_info", {}),
            "proposed_treatments": extraction.get("proposed_treatments", []),
            "urgency_indicators": extraction.get("urgency_indicators", []),
            "chief_complaint": extraction.get("chief_complaint", "")
        }
