import anthropic
import json
from app.services.vector_db import PolicyVectorStore
from app.config import get_settings


class RebuttalAgent:
    """Agent 4: The Negotiator - Generates appeals and P2P scripts"""
    
    def __init__(self, vector_store: PolicyVectorStore):
        settings = get_settings()
        self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.vector_store = vector_store
        self.model = "claude-sonnet-4-20250514"
    
    async def process(
        self,
        denial_reason: str,
        patient_name: str = "Patient",
        clinical_context: str = "",
        extraction: dict = None
    ) -> dict:
        """Generate rebuttal letter and P2P talking points"""
        
        # Step 1: RAG - Find relevant policy sections
        policy_context = await self.vector_store.query(
            f"medical necessity criteria {denial_reason}",
            top_k=5
        )
        
        # Step 2: Generate the rebuttal letter
        letter_prompt = f"""You are an expert healthcare appeals specialist with 20 years of experience 
winning insurance denials. Generate a formal, legally-defensible appeal letter.

DENIAL REASON FROM INSURANCE:
{denial_reason}

PATIENT: {patient_name}

ADDITIONAL CLINICAL CONTEXT:
{clinical_context if clinical_context else "Standard clinical documentation supports medical necessity."}

RELEVANT INSURANCE POLICY EXCERPTS:
{policy_context}

MISSING CRITERIA CITED BY INSURANCE:
{json.dumps(extraction.get('key_missing_criteria', []) if extraction else [], indent=2)}

Generate a professional appeal letter that:
1. Opens with formal header (Date, RE: Appeal, Patient info placeholder)
2. Directly rebuts each denial reason with specific counter-arguments
3. Cites the insurance company's OWN policy criteria to show how they were met
4. Uses assertive but professional language
5. Requests expedited review given patient care implications
6. Closes with clear call to action

Format the letter in clean markdown. Make it compelling and evidence-based."""

        letter_response = await self.client.messages.create(
            model=self.model,
            max_tokens=2500,
            messages=[{"role": "user", "content": letter_prompt}]
        )
        
        # Step 3: Generate P2P talking points
        p2p_prompt = f"""Based on this insurance denial, generate EXACTLY 3 bullet points for the physician 
to use in a Peer-to-Peer phone call with the insurance company's medical director.

DENIAL REASON: {denial_reason}

POLICY CONTEXT: {policy_context[:1000]}

Requirements for each bullet point:
- Must be 1-2 sentences maximum
- Must cite specific clinical criteria or evidence
- Must be assertive but professional
- Should anticipate and counter the insurance company's objections

Respond with ONLY a JSON array of 3 strings, no other text:
["First talking point...", "Second talking point...", "Third talking point..."]"""

        p2p_response = await self.client.messages.create(
            model=self.model,
            max_tokens=500,
            messages=[{"role": "user", "content": p2p_prompt}]
        )
        
        talking_points = self._parse_talking_points(p2p_response.content[0].text)
        
        return {
            "letter": letter_response.content[0].text,
            "talking_points": talking_points,
            "policy_references": policy_context[:500] + "...",
            "confidence_score": 0.85
        }
    
    def _parse_talking_points(self, response: str) -> list:
        """Parse talking points from JSON response"""
        try:
            # Clean up response
            text = response.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            return json.loads(text.strip())
        except:
            # Fallback: return as single item
            return [response.strip()]
