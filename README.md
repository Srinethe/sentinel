# Project Sentinel - Autonomous Revenue & Clinical Operations (ARCO)

An AI-powered healthcare administrative automation system that processes physician dictations, audits against insurance policies, and generates evidence-based appeal letters for denials.

## 🎯 Overview

Project Sentinel uses a **4-agent AI system** to automate healthcare revenue cycle management:

1. **👂 The Ear (Scribe Agent)**: Transcribes dictations and extracts clinical entities
2. **🧠 The Brain (Coder Agent)**: Audits documentation against payer policies, suggests ICD-11 codes, and flags preemptive alerts
3. **📂 The Sorter (Intake Agent)**: Reads denial PDFs using vision AI and extracts key information
4. **⚔️ The Negotiator (Rebuttal Agent)**: Generates evidence-based appeal letters and peer-to-peer talking points

## 🚀 Key Features

- **Real-time Dictation Processing**: Audio or text dictation → SOAP notes + clinical entities
- **Preemptive Policy Auditing**: Identifies documentation gaps BEFORE claim submission
- **ICD-11 Coding**: Suggests accurate ICD-11 codes with supporting evidence
- **Denial PDF Processing**: Vision AI reads scanned/faxed denial letters
- **Automated Appeals**: Generates professional appeal letters with policy citations
- **PDF Generation**: Downloadable audit reports and rebuttal letters
- **Step-by-Step Workflow**: Guided UI for sequential case processing
- **Real-time Updates**: WebSocket-based agent activity logs

## 🛠️ Tech Stack

- **Backend**: FastAPI + Python 3.11+
- **Agent Framework**: LangGraph
- **LLM**: Claude 3.5 Sonnet (text + vision) via Anthropic API
- **Speech-to-Text**: OpenAI Whisper
- **Vector DB**: ChromaDB (for RAG over insurance policies)
- **Frontend**: Next.js 14 + Tailwind CSS + Framer Motion
- **Real-time**: WebSockets
- **PDF Generation**: ReportLab

## 📋 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- API Keys:
  - Anthropic API key (for Claude)
  - OpenAI API key (for Whisper)

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys:
# ANTHROPIC_API_KEY=your_key_here
# OPENAI_API_KEY=your_key_here
python setup_demo_data.py
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The app will be available at `http://localhost:3000`

## 📖 Usage Guide

### Step-by-Step Workflow

1. **Step 1: Enter Dictation**
   - Paste physician dictation text OR upload audio file
   - Enter patient name
   - Click "Process Dictation"

2. **Step 2: View Audit Report**
   - Review SOAP note, clinical entities, ICD codes
   - Check preemptive alerts and policy gaps
   - Download audit report PDF
   - Click "Continue to Step 3"

3. **Step 3: Upload Denial PDF**
   - Upload the insurance denial letter (PDF)
   - System processes with loading indicator
   - Shows denial details if detected

4. **Step 4: View Rebuttal Letter**
   - Review generated appeal letter
   - Check peer-to-peer talking points
   - Download rebuttal letter PDF

### API Endpoints

#### Dictation Workflow
- `POST /api/dictation/text` - Process text dictation
- `POST /api/dictation/audio` - Process audio dictation

#### Denial Workflow
- `POST /api/denial/process` - Process denial PDF

#### Full Workflow
- `POST /api/case/full` - Complete workflow (dictation + denial)

#### PDF Downloads
- `GET /api/case/{case_id}/audit-report` - Download audit report PDF
- `GET /api/case/{case_id}/rebuttal-pdf` - Download rebuttal letter PDF

#### Case Retrieval
- `GET /api/cases/{case_id}` - Get case details

#### WebSocket
- `WS /ws/cases/{case_id}` - Real-time agent updates

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest

# Run specific test file
pytest tests/unit/test_agents.py
pytest tests/integration/test_api.py

# Run with coverage
pytest --cov=app --cov-report=html
```

### Test Coverage

- **Unit Tests**: Individual agents, services, models
- **Integration Tests**: API endpoints, workflows, PDF generation
- **Test Files**:
  - `tests/unit/test_agents.py` - Agent unit tests
  - `tests/unit/test_services.py` - Service tests
  - `tests/unit/test_pdf_generator.py` - PDF generation tests
  - `tests/integration/test_api.py` - API endpoint tests
  - `tests/integration/test_workflows.py` - Workflow integration tests
  - `tests/integration/test_pdf_endpoints.py` - PDF download tests

### Frontend Type Checking

```bash
cd frontend
npm run type-check
```

## 📁 Project Structure

```
sentinel/
├── backend/
│   ├── app/
│   │   ├── agents/          # 4 AI agents
│   │   │   ├── scribe_agent.py      # The Ear
│   │   │   ├── coder_agent.py        # The Brain
│   │   │   ├── intake_agent.py       # The Sorter
│   │   │   ├── rebuttal_agent.py     # The Negotiator
│   │   │   └── orchestrator.py       # LangGraph orchestrator
│   │   ├── services/
│   │   │   ├── speech_service.py     # Whisper transcription
│   │   │   ├── vector_db.py          # ChromaDB RAG
│   │   │   └── pdf_generator.py     # PDF report generation
│   │   ├── models/
│   │   │   └── schemas.py            # Pydantic models
│   │   ├── data/
│   │   │   ├── payer_policies/       # Insurance policy documents
│   │   │   ├── sample_dictations/    # Demo dictations
│   │   │   └── sample_denials/       # Demo denial PDFs
│   │   ├── config.py                # Settings management
│   │   └── main.py                   # FastAPI app
│   ├── tests/
│   │   ├── unit/                     # Unit tests
│   │   └── integration/              # Integration tests
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    └── src/
        ├── app/
        │   ├── page.tsx              # Main dashboard
        │   ├── layout.tsx
        │   └── globals.css
        ├── components/
        │   ├── DictationInput.tsx    # Step 1: Dictation input
        │   ├── ClinicalDataPanel.tsx # Step 2: Audit results
        │   ├── RebuttalViewer.tsx    # Step 4: Appeal letter
        │   ├── StepIndicator.tsx     # Progress indicator
        │   ├── AgentWorkflow.tsx     # Agent status
        │   ├── MetricsDashboard.tsx  # Impact metrics
        │   └── LiveLogs.tsx          # Real-time logs
        ├── hooks/
        │   └── useWebSocket.ts       # WebSocket hook
        └── lib/
            └── api.ts                # API client
```

## 🔧 Configuration

### Environment Variables

Create `backend/.env`:

```env
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key
```

### Frontend Environment

Create `frontend/.env.local` (optional):

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 📊 Impact Metrics

- **Manual Process**: 2.5 hrs average case time
- **With Sentinel**: 45 sec AI-driven synthesis
- **Time Saved**: 95% per case
- **Appeal Success**: 68% denial reversal rate

## 🔍 How It Works

### Dictation Workflow

1. **Scribe Agent** processes dictation (audio or text)
   - Transcribes audio using Whisper
   - Extracts clinical entities using Claude
   - Generates structured SOAP note

2. **Coder Agent** audits documentation
   - Queries vector store for relevant policies
   - Suggests ICD-11 codes
   - Identifies policy gaps and preemptive alerts
   - Calculates medical necessity score

### Denial Workflow

1. **Intake Agent** reads denial PDF
   - Uses Claude Vision to extract information
   - Identifies denial reason, deadline, missing criteria
   - Determines urgency level

2. **Rebuttal Agent** generates appeal
   - Queries policies for relevant criteria
   - Combines clinical context from dictation
   - Generates evidence-based appeal letter
   - Creates peer-to-peer talking points

### Full Workflow

Combines both workflows: Dictation → Coding → Denial Processing → Appeal Generation

## 🐛 Troubleshooting

### Backend Issues

- **Rate Limit Errors**: Check API key quotas
- **PDF Generation Errors**: Ensure ReportLab is installed
- **Vector Store Not Loading**: Check OpenAI API key and quota

### Frontend Issues

- **API Connection Errors**: Verify backend is running on port 8000
- **WebSocket Errors**: Check WebSocket endpoint connectivity

## 📝 License

MIT

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure all tests pass
5. Submit a pull request

## 📚 Additional Documentation

- `SETUP_INSTRUCTIONS.md` - Detailed setup guide
- `TEST_DENIAL_PDF.md` - Testing denial PDF processing
- `FULL_DEMO_EXPLAINED.md` - Demo workflow explanation
