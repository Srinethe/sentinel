import openai
import anthropic
from typing import BinaryIO
import json
from app.config import get_settings


class SpeechService:
    """Handles speech-to-text and clinical entity extraction"""
    
    def __init__(self):
        settings = get_settings()
        self.openai_client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        self.anthropic_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    
    async def transcribe_audio(self, audio_file: BinaryIO, filename: str = "audio.wav") -> str:
        """Transcribe audio using OpenAI Whisper"""
        transcript = await self.openai_client.audio.transcriptions.create(
            model="whisper-1",
            file=(filename, audio_file),
            response_format="text"
        )
        return transcript
    
    async def extract_clinical_entities(self, transcript: str) -> dict:
        """Extract clinical entities from transcript using Claude"""
        
        extraction_prompt = f"""You are a medical documentation specialist. Analyze this physician dictation/conversation 
and extract structured clinical information.

TRANSCRIPT:
{transcript}

Extract and return ONLY valid JSON in this exact format:
{{
    "patient_info": {{
        "name": "string or null",
        "age": "string or null",
        "gender": "string or null"
    }},
    "chief_complaint": "string",
    "clinical_entities": [
        {{
            "type": "symptom|lab_value|vital_sign|medication|diagnosis|procedure",
            "name": "string",
            "value": "string or null",
            "unit": "string or null",
            "status": "current|historical|planned"
        }}
    ],
    "soap_note": {{
        "subjective": "Patient's reported symptoms and history",
        "objective": "Exam findings, vitals, lab values",
        "assessment": "Diagnosis/clinical impression",
        "plan": "Treatment plan"
    }},
    "proposed_treatments": ["list of treatments mentioned"],
    "urgency_indicators": ["any urgent findings mentioned"]
}}

Be thorough - extract ALL lab values with their numeric values and units (e.g., K+ 5.3 mmol/L).
Look for vital signs, medications, symptoms, and diagnoses."""

        response = await self.anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": extraction_prompt}]
        )
        
        return self._parse_json_response(response.content[0].text)
    
    def _parse_json_response(self, text: str) -> dict:
        """Parse JSON from response, handling markdown code blocks"""
        try:
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            return json.loads(text.strip())
        except:
            return {"error": "Failed to parse clinical entities"}
