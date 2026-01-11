from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uuid
import asyncio
from typing import Optional
from datetime import datetime

from app.agents.orchestrator import SentinelOrchestrator
from app.services.vector_db import PolicyVectorStore
from app.services.pdf_generator import PDFGenerator
from app.models.schemas import CaseResponse, AgentUpdate
from app.config import get_settings

# In-memory store for demo (use real DB in production)
cases_store: dict = {}
pdf_generator = PDFGenerator()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup"""
    settings = get_settings()
    
    # Initialize vector store with payer policies
    app.state.vector_store = PolicyVectorStore()
    
    # Try to load policies, but don't fail if API quota is exceeded
    try:
        await app.state.vector_store.load_policies("app/data/payer_policies/")
        print("✅ Vector store loaded successfully")
    except Exception as e:
        error_msg = str(e)
        if "quota" in error_msg.lower() or "429" in error_msg:
            print("⚠️  WARNING: OpenAI API quota exceeded. Vector store not loaded.")
            print("   The app will still work, but policy RAG features will be limited.")
            print("   To fix: Add billing/credits to your OpenAI account or use a different API key.")
        else:
            print(f"⚠️  WARNING: Failed to load vector store: {error_msg}")
            print("   The app will still work, but policy RAG features will be limited.")
    
    # Initialize the orchestrator with all 4 agents
    app.state.orchestrator = SentinelOrchestrator(app.state.vector_store)
    
    print("🏥 Project Sentinel initialized with all 4 agents!")
    print("   - Agent 1: The Ear (Scribe)")
    print("   - Agent 2: The Brain (Coder)")
    print("   - Agent 3: The Sorter (Intake)")
    print("   - Agent 4: The Negotiator (Rebuttal)")
    yield
    print("👋 Shutting down Project Sentinel...")

app = FastAPI(
    title="Project Sentinel API",
    description="Autonomous Revenue & Clinical Operations - Multi-Agent Healthcare AI",
    version="2.0.0",
    lifespan=lifespan
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== HEALTH & INFO ====================

@app.get("/")
async def root():
    return {
        "status": "healthy",
        "service": "Project Sentinel",
        "agents": ["scribe", "coder", "intake", "rebuttal"]
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}


# ==================== DICTATION WORKFLOW ====================
# Agent 1 (Ear) -> Agent 2 (Brain)

@app.post("/api/dictation/audio")
async def process_audio_dictation(
    audio: UploadFile = File(...),
    patient_name: str = Form("Demo Patient")
):
    """
    Process audio dictation through Scribe -> Coder workflow.
    
    Accepts audio file (WAV, MP3, etc.), transcribes it, extracts clinical entities,
    generates SOAP note, and audits against payer policies for preemptive alerts.
    """
    case_id = str(uuid.uuid4())[:8]
    audio_bytes = await audio.read()
    
    orchestrator: SentinelOrchestrator = app.state.orchestrator
    result = await orchestrator.process_dictation(
        case_id=case_id,
        patient_name=patient_name,
        audio_bytes=audio_bytes
    )
    
    cases_store[case_id] = result
    
    return {
        "case_id": case_id,
        "workflow": "dictation",
        "transcript": result.get("raw_transcript"),
        "soap_note": result.get("soap_note"),
        "clinical_entities": result.get("clinical_entities"),
        "icd_codes": result.get("icd_codes"),
        "policy_gaps": result.get("policy_gaps"),
        "preemptive_alerts": result.get("preemptive_alerts"),
        "denial_risk": result.get("denial_risk"),
        "medical_necessity_score": result.get("medical_necessity_score")
    }

@app.post("/api/dictation/text")
async def process_text_dictation(
    dictation: str = Form(...),
    patient_name: str = Form("Demo Patient")
):
    """
    Process text dictation through Scribe -> Coder workflow.
    
    For demos/testing without audio. Paste physician dictation text directly.
    """
    case_id = str(uuid.uuid4())[:8]
    
    print(f"🆕 NEW DICTATION REQUEST:")
    print(f"   Case ID: {case_id}")
    print(f"   Patient: {patient_name}")
    print(f"   Dictation length: {len(dictation)} chars")
    print(f"   Dictation preview: {dictation[:200]}...")
    
    orchestrator: SentinelOrchestrator = app.state.orchestrator
    result = await orchestrator.process_dictation(
        case_id=case_id,
        patient_name=patient_name,
        dictation_text=dictation
    )
    
    print(f"✅ Dictation processing complete for case {case_id}")
    print(f"   Result keys: {list(result.keys())}")
    print(f"   ICD codes: {len(result.get('icd_codes', []))}")
    print(f"   Alerts: {len(result.get('preemptive_alerts', []))}")
    
    # Ensure case_id and patient_name are in the stored result
    result['case_id'] = case_id
    result['patient_name'] = patient_name
    cases_store[case_id] = result
    
    return {
        "case_id": case_id,
        "workflow": "dictation",
        "transcript": result.get("raw_transcript"),
        "soap_note": result.get("soap_note"),
        "clinical_entities": result.get("clinical_entities"),
        "icd_codes": result.get("icd_codes"),
        "policy_gaps": result.get("policy_gaps"),
        "preemptive_alerts": result.get("preemptive_alerts"),
        "denial_risk": result.get("denial_risk"),
        "medical_necessity_score": result.get("medical_necessity_score"),
        "patient_name": patient_name
    }


# ==================== DENIAL WORKFLOW ====================
# Agent 3 (Sorter) -> Agent 4 (Negotiator)

@app.post("/api/denial/process")
async def process_denial_pdf(
    file: UploadFile = File(...),
    patient_name: str = Form("Demo Patient")
):
    """
    Process denial PDF through Intake -> Rebuttal workflow.
    
    Reads denial letter, extracts reason and deadline, generates appeal letter
    and P2P talking points.
    """
    if not file.filename or not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    case_id = str(uuid.uuid4())[:8]
    
    try:
        print(f"📥 Received PDF upload: {file.filename}, size: {file.size if hasattr(file, 'size') else 'unknown'}")
        pdf_bytes = await file.read()
        print(f"✅ Read PDF: {len(pdf_bytes)} bytes")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read PDF file: {str(e)}")
    
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="PDF file is empty")
    
    try:
        orchestrator: SentinelOrchestrator = app.state.orchestrator
        print(f"🚀 Starting denial processing for case: {case_id}")
        result = await orchestrator.process_denial(
            case_id=case_id,
            patient_name=patient_name,
            pdf_bytes=pdf_bytes
        )
        print(f"✅ Denial processing complete for case: {case_id}")
    except Exception as e:
        import traceback
        error_msg = f"Error processing denial: {str(e)}"
        print(f"❌ {error_msg}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_msg)
    
    # Store result with case_id and patient_name
    result['case_id'] = case_id
    result['patient_name'] = patient_name
    
    # Ensure rebuttal_letter exists if denial was detected
    if result.get('denial_detected') and not result.get('rebuttal_letter'):
        if result.get('denial_reason'):
            print(f"⚠️  Denial detected but no rebuttal_letter. Generating one...")
            result['rebuttal_letter'] = f"""# APPEAL LETTER

**Date:** {datetime.now().strftime('%B %d, %Y')}  
**RE:** Appeal of Denial - Medical Necessity  
**Patient:** {patient_name}  
**Claim:** {case_id}

---

Dear Medical Director,

I am writing to formally appeal the denial of medical necessity for our patient.

## Rebuttal of Denial Reason

{result.get('denial_reason', 'Denial reason not specified')}

## Request

We request immediate reversal of this denial and authorization for the requested services.

Please contact me for Peer-to-Peer review at your earliest convenience.

Respectfully,  
[Attending Physician]
"""
            if not result.get('talking_points'):
                result['talking_points'] = [
                    f"Patient meets medical necessity criteria despite the denial reason",
                    "Clinical documentation supports the requested level of care",
                    "Request immediate peer-to-peer review for expedited resolution"
                ]
    
    cases_store[case_id] = result
    print(f"💾 Stored case {case_id} in cases_store")
    print(f"   Has rebuttal_letter: {bool(result.get('rebuttal_letter'))}")
    print(f"   Has talking_points: {bool(result.get('talking_points'))}")
    print(f"   Denial detected: {result.get('denial_detected')}")
    
    return {
        "case_id": case_id,
        "workflow": "denial",
        "denial_detected": result.get("denial_detected"),
        "denial_reason": result.get("denial_reason"),
        "peer_to_peer_deadline": result.get("peer_to_peer_deadline"),
        "rebuttal_letter": result.get("rebuttal_letter"),
        "talking_points": result.get("talking_points"),
        "extraction": result.get("denial_extraction")
    }


# ==================== FULL WORKFLOW ====================
# Agent 1 -> Agent 2 -> Agent 3 -> Agent 4

@app.post("/api/case/full")
async def process_full_case(
    denial_pdf: UploadFile = File(...),
    dictation: Optional[str] = Form(None),
    audio: Optional[UploadFile] = File(None),
    patient_name: str = Form("Demo Patient")
):
    """
    Process FULL workflow with all 4 agents.
    
    1. Scribe (The Ear): Process dictation
    2. Coder (The Brain): Audit against policies
    3. Intake (The Sorter): Read denial PDF
    4. Rebuttal (The Negotiator): Generate appeal
    
    The clinical context from Scribe/Coder enhances the Rebuttal quality.
    """
    case_id = str(uuid.uuid4())[:8]
    
    # Read inputs
    pdf_bytes = await denial_pdf.read()
    audio_bytes = await audio.read() if audio else None
    
    orchestrator: SentinelOrchestrator = app.state.orchestrator
    result = await orchestrator.process_full_case(
        case_id=case_id,
        patient_name=patient_name,
        audio_bytes=audio_bytes,
        dictation_text=dictation,
        pdf_bytes=pdf_bytes
    )
    
    cases_store[case_id] = result
    
    return {
        "case_id": case_id,
        "workflow": "full",
        # Scribe outputs
        "transcript": result.get("raw_transcript"),
        "soap_note": result.get("soap_note"),
        "clinical_entities": result.get("clinical_entities"),
        # Coder outputs
        "icd_codes": result.get("icd_codes"),
        "policy_gaps": result.get("policy_gaps"),
        "preemptive_alerts": result.get("preemptive_alerts"),
        "denial_risk": result.get("denial_risk"),
        # Intake outputs
        "denial_detected": result.get("denial_detected"),
        "denial_reason": result.get("denial_reason"),
        "peer_to_peer_deadline": result.get("peer_to_peer_deadline"),
        # Rebuttal outputs
        "rebuttal_letter": result.get("rebuttal_letter"),
        "talking_points": result.get("talking_points")
    }


# ==================== CASE RETRIEVAL ====================

@app.get("/api/cases/{case_id}")
async def get_case(case_id: str):
    """Retrieve a processed case by ID"""
    if case_id not in cases_store:
        raise HTTPException(status_code=404, detail="Case not found")
    return cases_store[case_id]

@app.get("/api/case/{case_id}/audit-report")
async def get_audit_report_pdf(case_id: str):
    """Generate and return audit report PDF"""
    # Try to find case - check both exact match and partial match
    case = None
    if case_id in cases_store:
        case = cases_store[case_id]
    else:
        # Try to find by partial match (case IDs might be shortened)
        for stored_id, stored_case in cases_store.items():
            if case_id in stored_id or stored_id in case_id:
                case = stored_case
                break
    
    if not case:
        raise HTTPException(
            status_code=404, 
            detail=f"Case not found. Available cases: {list(cases_store.keys())[:5]}"
        )
    
    try:
        pdf_bytes = pdf_generator.generate_audit_report(case)
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=audit-report-{case_id}.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")

@app.get("/api/case/{case_id}/rebuttal-pdf")
async def get_rebuttal_pdf(case_id: str):
    """Generate and return rebuttal letter PDF"""
    print(f"📥 Request for rebuttal PDF: case_id={case_id}")
    print(f"📋 Available cases: {list(cases_store.keys())}")
    
    # Try to find case - check both exact match and partial match
    case = None
    matched_id = None
    
    if case_id in cases_store:
        case = cases_store[case_id]
        matched_id = case_id
        print(f"✅ Found exact match: {case_id}")
    else:
        # Try to find by partial match (case IDs might be shortened)
        for stored_id, stored_case in cases_store.items():
            if case_id in stored_id or stored_id in case_id:
                case = stored_case
                matched_id = stored_id
                print(f"✅ Found partial match: {case_id} -> {stored_id}")
                break
    
    if not case:
        available = list(cases_store.keys())[:10]
        error_msg = f"Case '{case_id}' not found. Available cases: {available}"
        print(f"❌ {error_msg}")
        raise HTTPException(status_code=404, detail=error_msg)
    
    # Check if case has rebuttal_letter (check for both None and empty string)
    rebuttal_letter = case.get('rebuttal_letter')
    if not rebuttal_letter or (isinstance(rebuttal_letter, str) and not rebuttal_letter.strip()):
        print(f"⚠️  Case {matched_id} found but rebuttal_letter is empty or missing")
        print(f"   rebuttal_letter value: {repr(rebuttal_letter)}")
        print(f"   Case keys: {list(case.keys())}")
        # Try to generate a basic rebuttal if we have denial_reason
        if case.get('denial_reason'):
            print(f"   Generating basic rebuttal from denial_reason...")
            case['rebuttal_letter'] = f"""# APPEAL LETTER

**Date:** {datetime.now().strftime('%B %d, %Y')}  
**RE:** Appeal of Denial - Medical Necessity  
**Patient:** {case.get('patient_name', 'Patient')}  
**Claim:** {case.get('case_id', 'N/A')}

---

Dear Medical Director,

I am writing to formally appeal the denial of medical necessity for our patient.

## Rebuttal of Denial Reason

{case.get('denial_reason', 'Denial reason not specified')}

## Request

We request immediate reversal of this denial and authorization for the requested services.

Please contact me for Peer-to-Peer review at your earliest convenience.

Respectfully,  
[Attending Physician]
"""
            # Also ensure talking_points exists
            if not case.get('talking_points'):
                case['talking_points'] = [
                    f"Patient meets medical necessity criteria for {case.get('denial_reason', 'the requested service')}",
                    "Clinical documentation supports the requested level of care",
                    "Request immediate peer-to-peer review for expedited resolution"
                ]
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Case found but no rebuttal letter available and no denial_reason to generate one. Case has denial_detected: {case.get('denial_detected')}"
            )
    
    try:
        print(f"📄 Generating PDF for case {matched_id}...")
        pdf_generator: PDFGenerator = app.state.pdf_generator
        pdf_bytes = pdf_generator.generate_rebuttal_letter(case)
        print(f"✅ PDF generated: {len(pdf_bytes)} bytes")
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=rebuttal-letter-{case_id}.pdf"}
        )
    except Exception as e:
        import traceback
        error_msg = f"Failed to generate PDF: {str(e)}"
        print(f"❌ {error_msg}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_msg)


# ==================== WEBSOCKET FOR REAL-TIME UPDATES ====================

@app.websocket("/ws/cases/{case_id}")
async def websocket_endpoint(websocket: WebSocket, case_id: str):
    """WebSocket for real-time agent status updates"""
    await websocket.accept()
    
    orchestrator: SentinelOrchestrator = app.state.orchestrator
    queue = orchestrator.subscribe(case_id)
    
    try:
        while True:
            update = await asyncio.wait_for(queue.get(), timeout=120.0)
            await websocket.send_json(update)
    except asyncio.TimeoutError:
        await websocket.send_json({"status": "timeout", "message": "Connection timed out"})
    except WebSocketDisconnect:
        pass
    finally:
        orchestrator.unsubscribe(case_id)


# ==================== DEMO ENDPOINTS ====================

@app.post("/api/demo/dictation")
async def demo_dictation():
    """Run demo with sample physician dictation"""
    
    sample_dictation = """
    Patient is a 67-year-old male presenting with weakness and fatigue for the past 3 days.
    He has a history of chronic kidney disease stage 3 and is on lisinopril for hypertension.
    
    Vitals: BP 142/88, HR 78, Temp 98.6F, SpO2 97% on room air.
    
    Labs drawn in ED show potassium of 6.1 milliequivalents per liter, up from 5.2 last week.
    Creatinine is 2.8, up from baseline of 2.1. BUN is 45.
    
    EKG shows peaked T waves in leads V2 through V4, concerning for hyperkalemia.
    No widened QRS or sine wave pattern.
    
    Assessment: Acute hyperkalemia with EKG changes in setting of acute on chronic kidney injury.
    Likely precipitated by ACE inhibitor in setting of volume depletion.
    
    Plan: Admit to telemetry for cardiac monitoring. 
    Give calcium gluconate for cardiac membrane stabilization.
    Insulin and D50 for potassium shift. Kayexalate for potassium removal.
    Hold lisinopril. Nephrology consult for possible dialysis if refractory.
    """
    
    case_id = "demo-dictation"
    
    orchestrator: SentinelOrchestrator = app.state.orchestrator
    result = await orchestrator.process_dictation(
        case_id=case_id,
        patient_name="Demo Patient (Hyperkalemia)",
        dictation_text=sample_dictation
    )
    
    cases_store[case_id] = result
    return {
        "case_id": case_id,
        "workflow": "dictation_demo",
        **result
    }

@app.post("/api/demo/full")
async def demo_full_workflow():
    """
    Run full demo with sample dictation + simulated denial.
    Shows the complete 4-agent workflow.
    """
    
    sample_dictation = """
    Patient is a 67-year-old male with hyperkalemia. 
    Potassium level is 5.3 mmol/L on repeat. 
    EKG shows peaked T waves. 
    Admitting for telemetry monitoring and IV calcium gluconate.
    """
    
    # Since we may not have a real PDF, simulate the denial scenario
    case_id = "demo-full"
    
    orchestrator: SentinelOrchestrator = app.state.orchestrator
    
    # First run dictation workflow
    dictation_result = await orchestrator.process_dictation(
        case_id=case_id,
        patient_name="Demo Patient",
        dictation_text=sample_dictation
    )
    
    # Simulate denial response (in real use, this would come from uploaded PDF)
    simulated_result = {
        **dictation_result,
        "denial_detected": True,
        "denial_reason": "Patient's potassium level of 5.3 mmol/L does not meet our threshold of ≥5.5 mmol/L for hyperkalemia requiring inpatient admission.",
        "peer_to_peer_deadline": "2026-01-11T14:00:00",
        "rebuttal_letter": """# APPEAL LETTER

**Date:** January 9, 2026  
**RE:** Appeal of Denial - Medical Necessity for Inpatient Admission  
**Patient:** Demo Patient  
**Claim:** Hyperkalemia Management

---

Dear Medical Director,

I am writing to formally appeal the denial of inpatient admission for our patient with hyperkalemia.

## Rebuttal of Denial Reason

Your denial states the potassium level of 5.3 mmol/L does not meet the threshold of ≥5.5 mmol/L. However, this determination fails to consider critical clinical factors that your own policy acknowledges:

### 1. EKG Changes Present
The patient demonstrates **peaked T waves on EKG**, which per your policy bulletin 2026-HK-001, Section 2 (Electrocardiographic Criteria), independently qualifies for inpatient admission regardless of absolute potassium level.

### 2. Trajectory of Rise
The patient's potassium rose from 5.0 to 5.3 mmol/L within 24 hours while already on treatment, indicating a rapidly rising trajectory that poses imminent risk.

### 3. Underlying Renal Dysfunction  
With acute kidney injury (Cr 2.8, up from 2.1 baseline), the patient cannot effectively excrete potassium, making outpatient management unsafe.

## Policy Compliance

Your own Medical Policy Bulletin 2026-HK-001 states: *"Clinical judgment should be applied. Patients with values slightly below thresholds may still qualify if there is documented clinical concern or trajectory suggesting imminent deterioration."*

This patient meets that standard.

## Request

We request immediate reversal of this denial and authorization for inpatient admission. The patient requires continuous cardiac monitoring that cannot be safely provided in an outpatient setting.

Please contact me for Peer-to-Peer review at your earliest convenience.

Respectfully,  
[Attending Physician]
""",
        "talking_points": [
            "The EKG shows peaked T waves - per your own policy section 2, this independently qualifies for admission regardless of the absolute K+ level.",
            "The potassium is rapidly rising despite treatment, going from 5.0 to 5.3 in 24 hours - your policy explicitly covers 'trajectory suggesting deterioration.'",
            "With a creatinine of 2.8 and acute kidney injury, outpatient management is clinically unsafe - the patient cannot excrete potassium and needs monitoring for potential emergent dialysis."
        ]
    }
    
    cases_store[case_id] = simulated_result
    
    return {
        "case_id": case_id,
        "workflow": "full_demo",
        "message": "This demo simulates the full workflow. Upload a real denial PDF for actual processing.",
        **simulated_result
    }
