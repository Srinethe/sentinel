import anthropic
import json
from datetime import datetime
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
        # Add timestamp to prompt to ensure fresh analysis
        timestamp = datetime.now().isoformat()
        
        # Check if policy context is relevant to the diagnosis
        diagnoses_str = ' '.join(diagnoses).lower()
        policy_relevant = any(keyword in policy_context.lower() for keyword in [
            diagnoses_str.split()[0] if diagnoses_str else '',
            'cardiac', 'heart', 'myocardial', 'infarction', 'nstemi', 'stemi', 'troponin',
            'chest pain', 'coronary', 'angina'
        ]) if 'nstemi' in diagnoses_str.lower() or 'myocardial' in diagnoses_str.lower() else True
        
        # ICD-11 coding guidance for common conditions
        icd11_guidance = ""
        if 'nstemi' in diagnoses_str or 'non-st elevation' in diagnoses_str or 'myocardial infarction' in diagnoses_str:
            icd11_guidance = """
ICD-11 CODING FOR NSTEMI:
- Primary Code: BA41.1 (Acute non-ST elevation myocardial infarction)
- Post-coordination: Can add codes for specific location (anterior, inferior), underlying coronary atherosclerosis, or complications
- Medical Necessity: NSTEMI requires elevated troponin, ischemic symptoms (chest pain, dyspnea), and ECG findings (ST depression/T-wave inversion, but NOT ST elevation)
- Documentation Requirements: Must show troponin elevation above reference range, ischemic symptoms, and ECG changes or imaging confirmation
- Justification: NSTEMI indicates heart muscle damage from partial artery blockage, requiring urgent care to prevent severe outcomes
- Type 2 MI: If troponin rise is due to oxygen supply/demand imbalance (sepsis, respiratory failure), code underlying cause first but still bill as NSTEMI if symptoms fit
"""
        
        audit_prompt = f"""You are an expert medical coder and insurance policy auditor specializing in ICD-11 coding. 
Analyze this clinical documentation and identify potential issues BEFORE claim submission.

ANALYSIS TIMESTAMP: {timestamp}

CLINICAL DOCUMENTATION:
Subjective: {soap_note.get('subjective', 'N/A')}
Objective: {soap_note.get('objective', 'N/A')}
Assessment: {soap_note.get('assessment', 'N/A')}
Plan: {soap_note.get('plan', 'N/A')}

CLINICAL ENTITIES EXTRACTED:
{json.dumps(clinical_entities, indent=2)}

PROPOSED TREATMENTS:
{json.dumps(proposed_treatments or [], indent=2)}

DIAGNOSES IDENTIFIED: {', '.join(diagnoses) if diagnoses else 'None specified'}

{icd11_guidance}

INSURANCE POLICY REQUIREMENTS:
{policy_context}

⚠️ IMPORTANT: If the policy context above does not match the diagnosis (e.g., shows hyperkalemia policies for an NSTEMI case), 
you should:
1. Note this as a "MISSING_DATA" alert indicating relevant policies are not available
2. Apply GENERAL medical necessity principles for the actual diagnosis
3. Use ICD-11 coding standards (like BA41.1 for NSTEMI) regardless of available policies
4. Focus on documentation gaps specific to the ACTUAL diagnosis, not the mismatched policies

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

CRITICAL INSTRUCTIONS: 
- Use ICD-11 codes (e.g., BA41.1 for NSTEMI, not ICD-10)
- Flag if any lab values are below insurance thresholds FOR THE ACTUAL DIAGNOSIS (e.g., troponin elevation for NSTEMI, not K+ for hyperkalemia)
- Flag if required tests are missing FOR THE ACTUAL DIAGNOSIS (e.g., serial troponins, ECG, cardiac enzymes for NSTEMI)
- If policies don't match the diagnosis, create a "MISSING_DATA" alert stating: "Insurance policies provided are for [policy topic], not relevant to [actual diagnosis] admission. Obtain and review [diagnosis]-specific admission criteria policies."
- Suggest the most specific ICD-11 codes possible based on the ACTUAL diagnosis
- Focus on documentation gaps specific to the ACTUAL diagnosis presented
- Be proactive - catch issues before they become denials
- For NSTEMI: Ensure troponin values include reference ranges, peak values are documented, ECG findings are clear, and cardiac catheterization authorization is verified if mentioned"""

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
        
        # From SOAP assessment - extract key terms
        if soap_note.get("assessment"):
            assessment = soap_note["assessment"]
            diagnoses.append(assessment)
            # Extract key diagnosis terms (NSTEMI, STEMI, MI, etc.)
            assessment_lower = assessment.lower()
            if 'nstemi' in assessment_lower or 'non-st elevation' in assessment_lower:
                diagnoses.append("NSTEMI")
                diagnoses.append("myocardial infarction")
                diagnoses.append("acute coronary syndrome")
            if 'stemi' in assessment_lower or 'st elevation' in assessment_lower:
                diagnoses.append("STEMI")
                diagnoses.append("myocardial infarction")
            if 'myocardial' in assessment_lower or 'infarction' in assessment_lower:
                diagnoses.append("cardiac")
                diagnoses.append("coronary")
        
        # From entities
        for entity in entities:
            if entity.get("type") in ["diagnosis", "symptom"]:
                name = entity.get("name", "")
                if name:
                    diagnoses.append(name)
                    # Add related terms for cardiac conditions
                    name_lower = name.lower()
                    if any(term in name_lower for term in ['chest', 'cardiac', 'heart', 'troponin', 'coronary']):
                        diagnoses.append("cardiac")
        
        # Remove duplicates and limit
        unique_diagnoses = []
        seen = set()
        for d in diagnoses:
            d_lower = d.lower()
            if d_lower not in seen and d.strip():
                unique_diagnoses.append(d)
                seen.add(d_lower)
        
        return unique_diagnoses[:8]  # Increased limit to capture more relevant terms
    
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
