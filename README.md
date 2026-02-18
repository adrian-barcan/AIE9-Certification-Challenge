# Personal Financial Agent 🇷🇴

**AI-powered financial assistant for Romanian investors** — built as a certification demo for the AI Engineering Bootcamp (AIE9).

Demonstrates mastery of **RAG**, **LangGraph Agents**, **Evaluations (RAGAS)**, and **Synthetic Data Generation**.

## Quick Start

```bash
# 1. Copy environment template and add your API keys
cp .env.example .env

# 2. Start all services
docker compose up --build

# 3. Verify
open http://localhost:8000/docs   # FastAPI Swagger UI
open http://localhost:8000/health # Health check
```

## Architecture

```
┌─────────────┐     ┌──────────────────────────────────────────┐
│  Next.js    │────▶│  FastAPI Backend (:8000)                  │
│  Frontend   │     │  ┌─────────────────────────────────────┐  │
│  (:3000)    │     │  │  LangGraph Supervisor (GPT-4o)      │  │
│             │     │  │  ├── RAG Agent (docs + Cohere)      │  │
│             │     │  │  ├── Market Agent (Tavily)          │  │
│             │     │  │  └── Goals Agent (PostgreSQL)       │  │
└─────────────┘     │  └─────────────────────────────────────┘  │
                    └──────┬────────────┬────────────┬──────────┘
                           │            │            │
                    ┌──────┴──┐  ┌──────┴──┐  ┌─────┴──────┐
                    │ Qdrant  │  │ Postgres │  │  OpenAI    │
                    │ (:6333) │  │ (:5432)  │  │  Tavily    │
                    │         │  │          │  │  Cohere    │
                    └─────────┘  └──────────┘  └────────────┘
```

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | OpenAI GPT-4o / GPT-4o-mini |
| Agent | LangChain + LangGraph (Supervisor pattern) |
| Vector DB | Qdrant |
| Embeddings | OpenAI text-embedding-3-small |
| Reranking | Cohere |
| Search | Tavily |
| Evaluation | RAGAS + LangSmith |
| Backend | FastAPI (Python 3.11) |
| Frontend | Next.js 14 + TypeScript + Tailwind |
| Database | PostgreSQL 16 |

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app
│   │   ├── config.py        # Pydantic Settings
│   │   ├── database.py      # SQLAlchemy async
│   │   ├── schemas.py       # Pydantic request/response models
│   │   ├── models/          # SQLAlchemy models (User, Goal)
│   │   ├── api/             # REST endpoints
│   │   └── services/        # Business logic (RAG, Agent, Goals)
│   ├── documents/           # Romanian financial PDFs
│   ├── evals/               # Jupyter notebook + eval scripts
│   └── Dockerfile
├── frontend/                # Next.js (Phase 8)
├── docker-compose.yml
└── .env.example
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/users` | Create user (name only) |
| GET | `/api/users/{id}` | Get user profile |
| GET | `/api/goals?user_id=` | List goals |
| POST | `/api/goals?user_id=` | Create goal |
| PUT | `/api/goals/{id}` | Update goal |
| DELETE | `/api/goals/{id}` | Delete goal |
| POST | `/api/goals/{id}/contribute` | Add contribution |
| POST | `/api/chat` | Chat with agent (streaming) |
| GET | `/api/chat/history/{session_id}` | Chat history |
| POST | `/api/documents/ingest` | Index documents |
| GET | `/api/documents` | List indexed documents |

## License

MIT
