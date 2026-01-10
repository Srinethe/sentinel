import pytest
from datetime import datetime
from app.models.schemas import (
    AgentType,
    AgentStatus,
    Urgency,
    ClinicalEntity,
    DenialExtraction,
    RebuttalOutput,
    AgentUpdate,
    CaseCreate,
    CaseResponse,
)


def test_agent_type_enum():
    """Test AgentType enum values"""
    assert AgentType.INTAKE == "intake"
    assert AgentType.CODER == "coder"
    assert AgentType.REBUTTAL == "rebuttal"
    assert AgentType.SCRIBE == "scribe"


def test_agent_status_enum():
    """Test AgentStatus enum values"""
    assert AgentStatus.IDLE == "idle"
    assert AgentStatus.RUNNING == "running"
    assert AgentStatus.COMPLETE == "complete"
    assert AgentStatus.ERROR == "error"


def test_urgency_enum():
    """Test Urgency enum values"""
    assert Urgency.P0_CRITICAL == "P0_CRITICAL"
    assert Urgency.P1_HIGH == "P1_HIGH"
    assert Urgency.P2_MEDIUM == "P2_MEDIUM"
    assert Urgency.P3_LOW == "P3_LOW"


def test_clinical_entity_required_fields():
    """Test ClinicalEntity requires type and value"""
    entity = ClinicalEntity(type="lab_value", value="5.3", unit="mmol/L")
    assert entity.type == "lab_value"
    assert entity.value == "5.3"
    assert entity.unit == "mmol/L"


def test_clinical_entity_optional_unit():
    """Test ClinicalEntity unit is optional"""
    entity = ClinicalEntity(type="diagnosis", value="Hyperkalemia")
    assert entity.unit is None


def test_denial_extraction_defaults():
    """Test DenialExtraction has correct defaults"""
    extraction = DenialExtraction(document_type="DENIAL")
    assert extraction.document_type == "DENIAL"
    assert extraction.patient_name is None
    assert extraction.peer_to_peer_available is False
    assert extraction.key_missing_criteria == []
    assert extraction.urgency == Urgency.P2_MEDIUM


def test_rebuttal_output_required_fields():
    """Test RebuttalOutput requires all fields"""
    output = RebuttalOutput(
        letter="Test letter",
        talking_points=["Point 1", "Point 2"],
        confidence_score=0.85
    )
    assert output.letter == "Test letter"
    assert len(output.talking_points) == 2
    assert output.confidence_score == 0.85


def test_agent_update_timestamp():
    """Test AgentUpdate has timestamp"""
    update = AgentUpdate(
        agent=AgentType.CODER,
        status=AgentStatus.RUNNING,
        message="Processing..."
    )
    assert isinstance(update.timestamp, datetime)
    assert update.agent == AgentType.CODER
    assert update.status == AgentStatus.RUNNING


def test_case_create_required_fields():
    """Test CaseCreate requires patient_name"""
    case = CaseCreate(patient_name="John Doe")
    assert case.patient_name == "John Doe"
    assert case.account_number is None


def test_case_response_defaults():
    """Test CaseResponse has correct defaults"""
    response = CaseResponse(
        case_id="test-123",
        patient_name="John Doe",
        status="processing"
    )
    assert response.case_id == "test-123"
    assert response.denial_detected is False
    assert response.rebuttal_letter is None
    assert response.talking_points == []
    assert response.agent_logs == []


def test_schema_validation_errors():
    """Test that invalid enum values raise validation errors"""
    with pytest.raises(ValueError):
        AgentUpdate(
            agent="invalid_agent",  # type: ignore
            status=AgentStatus.RUNNING,
            message="Test"
        )
    
    with pytest.raises(ValueError):
        DenialExtraction(
            document_type="DENIAL",
            urgency="INVALID"  # type: ignore
        )
