import anthropic
import json
from app.services.vector_db import PolicyVectorStore
from app.config import get_settings


class CoderAgent:
    """
    Agent 2: The Brain - Predictive Coder & Policy Auditor
    
    Analyzes clinical documentation against insurance policy requirements,
    identifies gaps BEFORE submission, and suggests preemptive fixes.
    """
    
    def __init__(self, vector_store: PolicyVectorStore):
        settings = get_settings()
        self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.vector_store = vector_store
        self.model = "claude-sonnet-4-20250514"
    
    async def process(
        self, 
        soap_note: dict, 
        clinical_entities: list,
        proposed_treatments: list = None,
        payer: str = None
    ) -> dict:
        """
        Audit clinical documentation against payer policies.
        
        Returns ICD codes, policy gaps, and preemptive alerts.
        """
        
        # Step 1: Query relevant policy sections based on diagnoses
        diagnoses = self._extract_diagnoses(soap_note, clinical_entities)
        policy_context = await self.vector_store.query(
            f"medical necessity criteria admission {' '.join(diagnoses)}",
            top_k=8,
            payer=payer
        )
        
        # Step 2: Generate ICD codes and audit against policy
        audit_prompt = f"""You are an expert medical coder and insurance policy auditor. 
Analyze this clinical documentation and identify potential issues BEFORE claim submission.

CLINICAL DOCUMENTATION:
Subjective: {soap_note.get('subjective', 'N/A')}
Objective: {soap_note.get('objective', 'N/A')}
Assessment: {soap_note.get('assessment', 'N/A')}
Plan: {soap_note.get('plan', 'N/A')}

CLINICAL ENTITIES EXTRACTED:
{json.dumps(clinical_entities, indent=2)}

PROPOSED TREATMENTS:
{json.dumps(proposed_treatments or [], indent=2)}

RELEVANT INSURANCE POLICY REQUIREMENTS:
{policy_context}

Perform the following analysis and return ONLY valid JSON:

{{
    "icd_codes": [
        {{
            "code": "ICD-11 code",
            "description": "Description",
            "specificity": "high|medium|low",
            "supporting_evidence": "What in the documentation supports this code"
        }}
    ],
    "policy_gaps": [
        {{
            "gap": "What's missing or insufficient",
            "required_by_policy": "What the insurance policy requires",
            "risk_level": "high|medium|low",
            "suggested_fix": "How to address this gap"
        }}
    ],
    "preemptive_alerts": [
        {{
            "alert_type": "MISSING_DATA|THRESHOLD_NOT_MET|DOCUMENTATION_WEAK|AUTHORIZATION_NEEDED",
            "message": "Clear alert message for the physician",
            "action_required": "Specific action to take",
            "urgency": "immediate|before_submission|optional"
        }}
    ],
    "medical_necessity_score": 0.0 to 1.0,
    "denial_risk": "high|medium|low",
    "recommendations": ["List of recommendations to strengthen the case"]
}}

IMPORTANT: 
- Flag if any lab values are below insurance thresholds (e.g., K+ below 5.5 mmol/L for hyperkalemia)
- Flag if required tests are missing (e.g., EKG for cardiac conditions)
- Suggest the most specific ICD codes possible
- Be proactive - catch issues before they become denials"""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=2500,
            messages=[{"role": "user", "content": audit_prompt}]
        )
        
        result = self._parse_json_response(response.content[0].text)
        
        return {
            "icd_codes": result.get("icd_codes", []),
            "policy_gaps": result.get("policy_gaps", []),
            "preemptive_alerts": result.get("preemptive_alerts", []),
            "medical_necessity_score": result.get("medical_necessity_score", 0.5),
            "denial_risk": result.get("denial_risk", "medium"),
            "recommendations": result.get("recommendations", []),
            "policy_context_used": policy_context[:500] + "..."
        }
    
    def _extract_diagnoses(self, soap_note: dict, entities: list) -> list:
        """Extract diagnosis keywords for policy lookup"""
        diagnoses = []
        
        # From SOAP assessment
        if soap_note.get("assessment"):
            diagnoses.append(soap_note["assessment"])
        
        # From entities
        for entity in entities:
            if entity.get("type") in ["diagnosis", "symptom"]:
                diagnoses.append(entity.get("name", ""))
        
        return [d for d in diagnoses if d][:5]  # Limit to top 5
    
    def _parse_json_response(self, text: str) -> dict:
        """Parse JSON from response"""
        try:
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            return json.loads(text.strip())
        except:
            return {"error": "Failed to parse audit results"}
