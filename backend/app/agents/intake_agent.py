import anthropic
import base64
from datetime import datetime, timedelta
from app.models.schemas import Urgency
from app.config import get_settings


class IntakeAgent:
    """Agent 3: The Sorter - Reads denial PDFs using Vision"""
    
    def __init__(self):
        settings = get_settings()
        self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        # Claude 3.5 Sonnet supports PDF documents directly
        self.model = "claude-3-5-sonnet-20241022"
    
    async def process(self, pdf_bytes: bytes = None) -> dict:
        """Process a denial PDF and extract key information"""
        
        if not pdf_bytes:
            return {
                "is_denial": False,
                "extraction": None,
                "error": "No PDF provided"
            }
        
        pdf_b64 = base64.standard_b64encode(pdf_bytes).decode("utf-8")
        
        extraction_prompt = """Analyze this insurance document and extract information.

Respond ONLY with valid JSON in this exact format (no markdown, no extra text):
{
    "document_type": "APPROVAL" or "DENIAL" or "REQUEST_FOR_INFO" or "OTHER",
    "patient_name": "string or null",
    "account_number": "string or null",
    "denial_reason": "string or null - extract the EXACT quoted reason if this is a denial",
    "denial_code": "string or null",
    "appeal_deadline_days": number or null,
    "peer_to_peer_available": true or false,
    "key_missing_criteria": ["list", "of", "what insurance says is missing"],
    "urgency": "P0_CRITICAL" or "P1_HIGH" or "P2_MEDIUM" or "P3_LOW"
}

Rules:
- If it's a DENIAL, urgency should be P0_CRITICAL or P1_HIGH
- Extract the specific denial reason word-for-word
- Look for appeal deadlines (often 48-72 hours for peer-to-peer)
- Be thorough - denial reasons are often buried in dense paragraphs"""

        try:
            # Anthropic API: PDFs need to be sent as document type (Claude 3.5+ supports PDFs directly)
            # For older models, we'd need to convert to images, but 3.5 Sonnet supports PDF
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": "application/pdf",
                                "data": pdf_b64
                            }
                        },
                        {"type": "text", "text": extraction_prompt}
                    ]
                }]
            )
            
            result = self._parse_response(response.content[0].text)
            
            # Calculate deadline datetime
            deadline = None
            if result.get("appeal_deadline_days"):
                deadline = datetime.now() + timedelta(days=result["appeal_deadline_days"])
            
            return {
                "is_denial": result.get("document_type") == "DENIAL",
                "denial_reason": result.get("denial_reason"),
                "peer_to_peer_deadline": deadline.isoformat() if deadline else None,
                "extraction": result,
                "urgency": result.get("urgency", "P2_MEDIUM")
            }
            
        except Exception as e:
            import traceback
            error_details = f"{type(e).__name__}: {str(e)}"
            # Log full traceback for debugging (remove in production)
            print(f"❌ IntakeAgent error: {error_details}")
            print(f"Traceback: {traceback.format_exc()}")
            return {
                "is_denial": False,
                "error": error_details,
                "extraction": None
            }
    
    def _parse_response(self, text: str) -> dict:
        """Parse JSON from Claude's response"""
        import json
        try:
            # Handle potential markdown code blocks
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            return json.loads(text.strip())
        except json.JSONDecodeError:
            return {"document_type": "OTHER", "parse_error": True}
