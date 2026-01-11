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
        # Use the correct model identifier - try standard name first
        self.model = "claude-3-5-sonnet-20240620"  # Stable model version
    
    async def process(self, pdf_bytes: bytes = None) -> dict:
        """Process a denial PDF and extract key information"""
        
        if not pdf_bytes:
            return {
                "is_denial": False,
                "extraction": None,
                "error": "No PDF provided"
            }
        
        # Validate PDF size (max 10MB for API)
        pdf_size_mb = len(pdf_bytes) / (1024 * 1024)
        if pdf_size_mb > 10:
            return {
                "is_denial": False,
                "extraction": None,
                "error": f"PDF too large ({pdf_size_mb:.2f}MB). Maximum size is 10MB."
            }
        
        print(f"📄 Processing PDF: {pdf_size_mb:.2f}MB")
        
        try:
            pdf_b64 = base64.standard_b64encode(pdf_bytes).decode("utf-8")
        except Exception as e:
            return {
                "is_denial": False,
                "extraction": None,
                "error": f"Failed to encode PDF: {str(e)}"
            }
        
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
            # Anthropic API: Try document type first (Claude 3.5+ supports PDFs directly)
            # If model not found, try alternative models
            response = None
            last_error = None
            models_to_try = [
                "claude-3-5-sonnet-20240620",  # Most stable
                "claude-3-5-sonnet",  # Without version
                "claude-3-opus-20240229",  # Alternative
                "claude-3-5-haiku-20241022"  # Fastest
            ]
            
            import asyncio
            
            for model_name in models_to_try:
                try:
                    print(f"🔄 Trying model: {model_name}...")
                    # Add timeout to prevent hanging (60 seconds)
                    # Wrap the API call in asyncio.wait_for to add timeout
                    response = await asyncio.wait_for(
                        self.client.messages.create(
                            model=model_name,
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
                        ),
                        timeout=60.0  # 60 second timeout
                    )
                    print(f"✅ Successfully used model: {model_name}")
                    self.model = model_name  # Update to working model
                    break
                except asyncio.TimeoutError:
                    last_error = Exception(f"Timeout waiting for {model_name}")
                    print(f"⏱️  Model {model_name} timed out after 65 seconds")
                    continue  # Try next model
                except Exception as model_err:
                    error_str = str(model_err).lower()
                    # Check if it's a model not found error
                    if any(keyword in error_str for keyword in ["not_found", "404", "model", "invalid"]):
                        last_error = model_err
                        print(f"⚠️  Model {model_name} not available: {str(model_err)[:100]}")
                        continue  # Try next model
                    else:
                        # If it's an authentication, quota, or other error, don't try other models
                        print(f"❌ Non-model error with {model_name}: {str(model_err)[:100]}")
                        raise
            
            if not response:
                error_msg = f"Could not find a working Claude model. Tried: {models_to_try}. Last error: {str(last_error)[:200] if last_error else 'Unknown'}"
                print(f"❌ {error_msg}")
                # Return error instead of raising to allow workflow to continue
                return {
                    "is_denial": False,
                    "error": error_msg,
                    "extraction": None
                }
            
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
