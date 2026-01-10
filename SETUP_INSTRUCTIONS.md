# Project Sentinel - Setup Instructions

## Quick Start

### 1. Backend Setup

```bash
cd backend

# Install dependencies (already done)
# pip install -r requirements.txt

# Set up API keys in .env file
# Edit .env and add your actual API keys:
# ANTHROPIC_API_KEY=sk-ant-...
# OPENAI_API_KEY=sk-...

# Run demo data setup (already done)
# python setup_demo_data.py

# Start the backend server
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies (already done)
# npm install

# Start the frontend development server
npm run dev
```

### 3. Access the Application

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Important Notes

1. **API Keys**: You MUST update the `.env` file in the `backend/` directory with your actual API keys:
   - Get Anthropic API key from: https://console.anthropic.com/
   - Get OpenAI API key from: https://platform.openai.com/api-keys

2. **Running Servers**: The backend and frontend need to run in separate terminal windows:
   - Terminal 1: `cd backend && uvicorn app.main:app --reload`
   - Terminal 2: `cd frontend && npm run dev`

3. **First Run**: The backend will automatically load policy data from `app/data/payer_policies/` on startup.

## Testing

```bash
# Backend tests
cd backend
pytest

# Frontend type checking
cd frontend
npm run type-check
```

## Troubleshooting

- If backend fails to start, check that `.env` file exists and has valid API keys
- If frontend can't connect, ensure backend is running on port 8000
- If ChromaDB errors occur, the vector store will still work but may be slower
