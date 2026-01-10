# Project Sentinel - Autonomous Revenue & Clinical Operations (ARCO)

An AI-powered healthcare administrative automation system that processes physician dictations, audits against insurance policies, and generates evidence-based appeal letters for denials.

## Tech Stack

- **Backend**: FastAPI + Python 3.11+
- **Agent Framework**: LangGraph
- **LLM**: Claude 3.5 Sonnet (text + vision)
- **Vector DB**: ChromaDB (for RAG over insurance policies)
- **Frontend**: Next.js 14 + Tailwind CSS + Framer Motion
- **Real-time**: WebSockets

## Quick Start

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
python setup_demo_data.py
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```
sentinel/
├── backend/
│   ├── app/
│   │   ├── agents/      # 4 AI agents (Scribe, Coder, Intake, Rebuttal)
│   │   ├── services/    # Core services (LLM, Vector DB, Speech)
│   │   ├── models/      # Pydantic schemas
│   │   └── data/        # Demo data (policies, dictations)
│   └── tests/           # Unit and integration tests
└── frontend/
    └── src/
        ├── app/         # Next.js pages
        ├── components/  # React components
        ├── hooks/      # Custom hooks
        └── lib/         # API client
```

## Testing

```bash
# Backend tests
cd backend
pytest

# Frontend type checking
cd frontend
npm run type-check
```

## License

MIT
