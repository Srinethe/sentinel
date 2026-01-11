from typing import TypedDict, Annotated, Optional
from langgraph.graph import StateGraph, END
import operator
import asyncio
from datetime import datetime

from app.agents.scribe_agent import ScribeAgent
from app.agents.coder_agent import CoderAgent
from app.agents.intake_agent import IntakeAgent
from app.agents.rebuttal_agent import RebuttalAgent
from app.services.vector_db import PolicyVectorStore
from app.models.schemas import AgentType, AgentStatus


class SentinelState(TypedDict):
    """Complete state for the Sentinel workflow"""
    # Case identifiers
    case_id: str
    patient_name: str
    
    # Input data
    audio_bytes: Optional[bytes]
    dictation_text: Optional[str]
    pdf_bytes: Optional[bytes]
    workflow_type: str  # "dictation" | "denial" | "full"
    
    # Agent 1: Scribe (The Ear) outputs
    raw_transcript: str
    soap_note: dict
    clinical_entities: list
    proposed_treatments: list
    chief_complaint: str
    
    # Agent 2: Coder (The Brain) outputs
    icd_codes: list
    policy_gaps: list
    preemptive_alerts: list
    medical_necessity_score: float
    denial_risk: str
    
    # Agent 3: Intake (The Sorter) outputs
    denial_detected: bool
    denial_reason: str
    peer_to_peer_deadline: str
    denial_extraction: dict
    
    # Agent 4: Rebuttal (The Negotiator) outputs
    rebuttal_letter: str
    talking_points: list
    
    # Workflow tracking
    current_agent: str
    agent_logs: Annotated[list, operator.add]
    error: str


class SentinelOrchestrator:
    """
    Main orchestrator using LangGraph for the complete agent workflow.
    
    Supports three workflow types:
    1. "dictation" - Process physician dictation through Scribe -> Coder
    2. "denial" - Process denial PDF through Intake -> Rebuttal  
    3. "full" - Complete workflow with all agents
    """
    
    def __init__(self, vector_store: PolicyVectorStore):
        self.vector_store = vector_store
        self.scribe = ScribeAgent()
        self.coder = CoderAgent(vector_store)
        self.intake = IntakeAgent()
        self.rebuttal = RebuttalAgent(vector_store)
        
        # Build separate graphs for different workflows
        self.dictation_graph = self._build_dictation_graph()
        self.denial_graph = self._build_denial_graph()
        self.full_graph = self._build_full_graph()
        
        self.active_streams: dict[str, asyncio.Queue] = {}
    
    def _build_dictation_graph(self) -> StateGraph:
        """Workflow: Dictation -> Scribe -> Coder"""
        workflow = StateGraph(SentinelState)
        
        workflow.add_node("scribe", self._run_scribe)
        workflow.add_node("coder", self._run_coder)
        
        workflow.set_entry_point("scribe")
        workflow.add_edge("scribe", "coder")
        workflow.add_edge("coder", END)
        
        return workflow.compile()
    
    def _build_denial_graph(self) -> StateGraph:
        """Workflow: Denial PDF -> Intake -> Rebuttal"""
        workflow = StateGraph(SentinelState)
        
        workflow.add_node("intake", self._run_intake)
        workflow.add_node("rebuttal", self._run_rebuttal)
        
        workflow.set_entry_point("intake")
        workflow.add_conditional_edges(
            "intake",
            self._route_after_intake,
            {"generate_rebuttal": "rebuttal", "end": END}
        )
        workflow.add_edge("rebuttal", END)
        
        return workflow.compile()
    
    def _build_full_graph(self) -> StateGraph:
        """
        Full Workflow DAG:
        
        [Dictation] -> Scribe -> Coder -> (check alerts)
                                              |
        [Denial PDF] -> Intake ---------------+-> Rebuttal -> END
        """
        workflow = StateGraph(SentinelState)
        
        # Add all agent nodes
        workflow.add_node("scribe", self._run_scribe)
        workflow.add_node("coder", self._run_coder)
        workflow.add_node("intake", self._run_intake)
        workflow.add_node("rebuttal", self._run_rebuttal)
        
        # Entry point based on input type
        workflow.set_entry_point("scribe")
        
        # Scribe -> Coder
        workflow.add_edge("scribe", "coder")
        
        # Coder -> Check if we have denial PDF to process
        workflow.add_conditional_edges(
            "coder",
            self._route_after_coder,
            {"process_denial": "intake", "end": END}
        )
        
        # Intake -> Rebuttal if denial detected
        workflow.add_conditional_edges(
            "intake",
            self._route_after_intake,
            {"generate_rebuttal": "rebuttal", "end": END}
        )
        
        workflow.add_edge("rebuttal", END)
        
        return workflow.compile()
    
    # ==================== AGENT RUNNERS ====================
    
    async def _run_scribe(self, state: SentinelState) -> dict:
        """Run Agent 1: The Ear - Ambient Scribe"""
        case_id = state.get("case_id", "unknown")
        print(f"👂 [Scribe] Starting dictation processing for case: {case_id}")
        
        # Log input to verify it's fresh
        dictation_text = state.get("dictation_text", "")
        has_audio = bool(state.get("audio_bytes"))
        print(f"📝 [Scribe] Input: {'Audio file' if has_audio else f'Text dictation ({len(dictation_text)} chars)'}")
        if dictation_text:
            print(f"   Preview: {dictation_text[:150]}...")
        
        await self._emit_update(case_id, "scribe", "running", "Listening to dictation...")
        
        try:
            if state.get("audio_bytes"):
                from io import BytesIO
                audio_file = BytesIO(state["audio_bytes"])
                result = await self.scribe.process_audio(audio_file)
            elif state.get("dictation_text"):
                result = await self.scribe.process_text(state["dictation_text"])
            else:
                result = {"error": "No audio or text provided"}
            
            print(f"✅ [Scribe] Processing complete:")
            print(f"   Transcript length: {len(result.get('raw_transcript', ''))}")
            print(f"   Clinical entities: {len(result.get('clinical_entities', []))}")
            print(f"   Assessment: {result.get('soap_note', {}).get('assessment', 'N/A')[:100]}")
            
            await self._emit_update(
                state["case_id"], "scribe", "complete",
                f"Extracted {len(result.get('clinical_entities', []))} clinical entities",
                {"entities_preview": result.get("clinical_entities", [])[:3]}
            )
            
            return {
                "raw_transcript": result.get("raw_transcript", ""),
                "soap_note": result.get("soap_note", {}),
                "clinical_entities": result.get("clinical_entities", []),
                "proposed_treatments": result.get("proposed_treatments", []),
                "chief_complaint": result.get("chief_complaint", ""),
                "current_agent": "scribe",
                "agent_logs": [{
                    "agent": "scribe",
                    "status": "complete",
                    "message": "Dictation processed",
                    "timestamp": datetime.now().isoformat()
                }]
            }
        except Exception as e:
            await self._emit_update(state["case_id"], "scribe", "error", str(e))
            return {"error": str(e), "agent_logs": [{"agent": "scribe", "status": "error", "message": str(e)}]}
    
    async def _run_coder(self, state: SentinelState) -> dict:
        """Run Agent 2: The Brain - Policy Auditor"""
        case_id = state.get("case_id", "unknown")
        print(f"🧠 [Coder] Starting audit for case: {case_id}")
        
        # Log the input data to verify it's fresh
        soap_note = state.get("soap_note", {})
        clinical_entities = state.get("clinical_entities", [])
        proposed_treatments = state.get("proposed_treatments", [])
        
        print(f"📋 [Coder] Input data:")
        print(f"   SOAP Assessment: {soap_note.get('assessment', 'N/A')[:100]}")
        print(f"   Clinical entities count: {len(clinical_entities)}")
        if clinical_entities:
            print(f"   First entity: {clinical_entities[0]}")
        print(f"   Proposed treatments: {proposed_treatments}")
        
        await self._emit_update(case_id, "coder", "running", "Auditing against payer policies...")
        
        try:
            result = await self.coder.process(
                soap_note=soap_note,
                clinical_entities=clinical_entities,
                proposed_treatments=proposed_treatments
            )
            
            print(f"✅ [Coder] Audit complete:")
            print(f"   ICD codes: {len(result.get('icd_codes', []))}")
            print(f"   Alerts: {len(result.get('preemptive_alerts', []))}")
            print(f"   Denial risk: {result.get('denial_risk', 'N/A')}")
            
            # Generate alert message
            alerts = result.get("preemptive_alerts", [])
            alert_msg = f"Found {len(alerts)} preemptive alerts" if alerts else "No policy gaps detected"
            
            await self._emit_update(
                state["case_id"], "coder", "complete", alert_msg,
                {
                    "denial_risk": result.get("denial_risk"),
                    "alerts": alerts[:2]  # Preview first 2
                }
            )
            
            return {
                "icd_codes": result.get("icd_codes", []),
                "policy_gaps": result.get("policy_gaps", []),
                "preemptive_alerts": alerts,
                "medical_necessity_score": result.get("medical_necessity_score", 0.5),
                "denial_risk": result.get("denial_risk", "medium"),
                "current_agent": "coder",
                "agent_logs": [{
                    "agent": "coder",
                    "status": "complete",
                    "message": alert_msg,
                    "timestamp": datetime.now().isoformat()
                }]
            }
        except Exception as e:
            await self._emit_update(state["case_id"], "coder", "error", str(e))
            return {"error": str(e), "agent_logs": [{"agent": "coder", "status": "error", "message": str(e)}]}
    
    async def _run_intake(self, state: SentinelState) -> dict:
        """Run Agent 3: The Sorter - PDF Intake"""
        case_id = state.get("case_id", "unknown")
        print(f"🔍 [Intake] Starting PDF processing for case: {case_id}")
        await self._emit_update(case_id, "intake", "running", "Reading denial PDF...")
        
        try:
            pdf_bytes = state.get("pdf_bytes")
            if not pdf_bytes:
                error_msg = "No PDF bytes provided in state"
                print(f"❌ [Intake] {error_msg}")
                await self._emit_update(case_id, "intake", "error", error_msg)
                return {"error": error_msg, "agent_logs": [{"agent": "intake", "status": "error", "message": error_msg}]}
            
            print(f"📄 [Intake] PDF size: {len(pdf_bytes)} bytes, calling intake.process()...")
            result = await self.intake.process(pdf_bytes)
            print(f"✅ [Intake] Processing complete. Denial detected: {result.get('is_denial', False)}")
            
            if result.get("error"):
                error_msg = f"Intake processing error: {result.get('error')}"
                await self._emit_update(state["case_id"], "intake", "error", error_msg)
                return {
                    "error": error_msg,
                    "agent_logs": [{"agent": "intake", "status": "error", "message": error_msg}]
                }
            
            status = "complete"
            message = "🚨 DENIAL DETECTED!" if result.get("is_denial") else "Document processed (not a denial)"
            
            await self._emit_update(state["case_id"], "intake", status, message, result)
            
            return {
                "denial_detected": result.get("is_denial", False),
                "denial_reason": result.get("denial_reason", ""),
                "peer_to_peer_deadline": result.get("peer_to_peer_deadline", ""),
                "denial_extraction": result.get("extraction", {}),
                "current_agent": "intake",
                "agent_logs": [{
                    "agent": "intake",
                    "status": status,
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                }]
            }
        except Exception as e:
            error_msg = f"Intake agent exception: {str(e)}"
            await self._emit_update(state["case_id"], "intake", "error", error_msg)
            return {"error": error_msg, "agent_logs": [{"agent": "intake", "status": "error", "message": error_msg}]}
    
    async def _run_rebuttal(self, state: SentinelState) -> dict:
        """Run Agent 4: The Negotiator - Appeal Generator"""
        await self._emit_update(state["case_id"], "rebuttal", "running", "Generating evidence-based rebuttal...")
        
        try:
            # Combine clinical context from scribe if available
            clinical_context = ""
            if state.get("soap_note"):
                clinical_context = f"""
SOAP Note:
- Subjective: {state['soap_note'].get('subjective', 'N/A')}
- Objective: {state['soap_note'].get('objective', 'N/A')}
- Assessment: {state['soap_note'].get('assessment', 'N/A')}
- Plan: {state['soap_note'].get('plan', 'N/A')}

Clinical Entities:
{self._format_entities(state.get('clinical_entities', []))}
"""
            
            result = await self.rebuttal.process(
                denial_reason=state["denial_reason"],
                patient_name=state.get("patient_name", "Patient"),
                clinical_context=clinical_context,
                extraction=state.get("denial_extraction")
            )
            
            await self._emit_update(
                state["case_id"], "rebuttal", "complete",
                "✅ Appeal letter and P2P script ready!",
                {"talking_points": result.get("talking_points", [])}
            )
            
            return {
                "rebuttal_letter": result["letter"],
                "talking_points": result["talking_points"],
                "current_agent": "rebuttal",
                "agent_logs": [{
                    "agent": "rebuttal",
                    "status": "complete",
                    "message": "Appeal generated",
                    "timestamp": datetime.now().isoformat()
                }]
            }
        except Exception as e:
            await self._emit_update(state["case_id"], "rebuttal", "error", str(e))
            return {"error": str(e), "agent_logs": [{"agent": "rebuttal", "status": "error", "message": str(e)}]}
    
    # ==================== ROUTING LOGIC ====================
    
    def _route_after_coder(self, state: SentinelState) -> str:
        """After coding, check if we have a denial PDF to process"""
        if state.get("pdf_bytes"):
            return "process_denial"
        return "end"
    
    def _route_after_intake(self, state: SentinelState) -> str:
        """After intake, generate rebuttal if denial detected"""
        if state.get("denial_detected"):
            return "generate_rebuttal"
        return "end"
    
    # ==================== PUBLIC METHODS ====================
    
    async def process_dictation(self, case_id: str, patient_name: str, 
                                 audio_bytes: bytes = None, dictation_text: str = None) -> dict:
        """Process physician dictation through Scribe -> Coder workflow"""
        initial_state = self._create_initial_state(
            case_id=case_id,
            patient_name=patient_name,
            audio_bytes=audio_bytes,
            dictation_text=dictation_text,
            workflow_type="dictation"
        )
        return await self.dictation_graph.ainvoke(initial_state)
    
    async def process_denial(self, case_id: str, patient_name: str, pdf_bytes: bytes) -> dict:
        """Process denial PDF through Intake -> Rebuttal workflow"""
        print(f"📋 Creating initial state for denial workflow: case_id={case_id}")
        initial_state = self._create_initial_state(
            case_id=case_id,
            patient_name=patient_name,
            pdf_bytes=pdf_bytes,
            workflow_type="denial"
        )
        print(f"🔄 Invoking denial graph...")
        try:
            result = await self.denial_graph.ainvoke(initial_state)
            print(f"✅ Denial graph completed successfully")
            return result
        except Exception as e:
            import traceback
            print(f"❌ Error in denial graph: {str(e)}")
            print(traceback.format_exc())
            raise
    
    async def process_full_case(self, case_id: str, patient_name: str,
                                 audio_bytes: bytes = None, dictation_text: str = None,
                                 pdf_bytes: bytes = None) -> dict:
        """Process complete workflow: Dictation -> Coding -> Denial -> Rebuttal"""
        initial_state = self._create_initial_state(
            case_id=case_id,
            patient_name=patient_name,
            audio_bytes=audio_bytes,
            dictation_text=dictation_text,
            pdf_bytes=pdf_bytes,
            workflow_type="full"
        )
        return await self.full_graph.ainvoke(initial_state)
    
    def _create_initial_state(self, **kwargs) -> SentinelState:
        """Create initial state with defaults"""
        # Ensure we're creating a fresh state - don't reuse any cached data
        dictation_text = kwargs.get("dictation_text")
        audio_bytes = kwargs.get("audio_bytes")
        
        print(f"🆕 Creating fresh initial state for case: {kwargs.get('case_id', 'unknown')}")
        print(f"   Has dictation_text: {bool(dictation_text)} ({len(dictation_text) if dictation_text else 0} chars)")
        print(f"   Has audio_bytes: {bool(audio_bytes)} ({len(audio_bytes) if audio_bytes else 0} bytes)")
        
        return {
            "case_id": kwargs.get("case_id", ""),
            "patient_name": kwargs.get("patient_name", ""),
            "audio_bytes": audio_bytes,  # Use fresh input
            "dictation_text": dictation_text,  # Use fresh input
            "pdf_bytes": kwargs.get("pdf_bytes"),
            "workflow_type": kwargs.get("workflow_type", "full"),
            "raw_transcript": "",  # Fresh empty state
            "soap_note": {},  # Fresh empty state
            "clinical_entities": [],  # Fresh empty state
            "proposed_treatments": [],  # Fresh empty state
            "chief_complaint": "",  # Fresh empty state
            "icd_codes": [],  # Fresh empty state
            "policy_gaps": [],
            "preemptive_alerts": [],
            "medical_necessity_score": 0.0,
            "denial_risk": "",
            "denial_detected": False,
            "denial_reason": "",
            "peer_to_peer_deadline": "",
            "denial_extraction": {},
            "rebuttal_letter": "",
            "talking_points": [],
            "current_agent": "",
            "agent_logs": [],
            "error": ""
        }
    
    def _format_entities(self, entities: list) -> str:
        """Format clinical entities for context"""
        if not entities:
            return "None extracted"
        return "\n".join([
            f"- {e.get('name', 'Unknown')}: {e.get('value', 'N/A')} {e.get('unit', '')}"
            for e in entities[:10]
        ])
    
    # ==================== WEBSOCKET STREAMING ====================
    
    async def _emit_update(self, case_id: str, agent: str, status: str, message: str, data: dict = None):
        """Emit update to WebSocket subscribers"""
        if case_id in self.active_streams:
            update = {
                "agent": agent,
                "status": status,
                "message": message,
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
            await self.active_streams[case_id].put(update)
    
    def subscribe(self, case_id: str) -> asyncio.Queue:
        """Subscribe to updates for a case"""
        if case_id not in self.active_streams:
            self.active_streams[case_id] = asyncio.Queue()
        return self.active_streams[case_id]
    
    def unsubscribe(self, case_id: str):
        """Unsubscribe from case updates"""
        if case_id in self.active_streams:
            del self.active_streams[case_id]
