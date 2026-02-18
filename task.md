# Personal Financial Agent — Certification Demo App

## Phase 1: Planning
- [x] Read and analyze `claude-code-prompt.md`
- [x] Analyze AIE9 course modules and tech stack
- [x] Identify gaps between prompt and course technologies
- [x] Ask user for key decisions
- [x] Write detailed implementation plan
- [x] Get user approval on implementation plan

## Phase 2: Project Setup
- [x] Initialize project structure
- [x] Docker Compose (PostgreSQL, Qdrant)
- [x] Python backend (FastAPI + LangChain/LangGraph)
- [x] Next.js frontend scaffold
- [x] Environment config (.env)

## Phase 3: RAG Pipeline (Mandatory)
- [x] Document loader (PDF/DOCX from `/documents`)
- [x] Chunking + embeddings (OpenAI text-embedding-3-small)
- [x] Qdrant vector store setup
- [x] RAG query service with top-k retrieval
- [x] Reranking (Cohere)

## Phase 4: Agent Service (Mandatory)
- [x] LangGraph agent with tools (RAG, Tavily, goals)
- [x] Agent architecture (Supervisor or ReAct — TBD in plan)
- [x] System prompt with Romanian financial context
- [x] LangGraph memory (short-term + long-term + semantic)
- [x] MiFID II disclaimer logic

## Phase 5: Goals Service (Mandatory)
- [x] PostgreSQL schema + SQLAlchemy models
- [x] CRUD API endpoints
- [x] Goal calculations (months to goal, feasibility)

## Phase 6: Chat + API (Mandatory)
- [x] FastAPI endpoints (chat, goals, documents, users)
- [x] Simple user identity (name prompt → user_id in localStorage)
- [x] Streaming responses
- [x] Conversation history
- [x] Seed demo data script (demo user + 3 goals)

## Phase 7: Evals + SDG (Mandatory for Certification)
- [x] Jupyter notebook `sdg_and_evaluation.ipynb` (primary demo)
- [x] Synthetic data generation with RAGAS
- [x] RAG evaluation (baseline vs. Cohere reranked — iteration story)
- [x] Agent evaluation (Tool Call Accuracy, Goal Accuracy)
- [x] LangSmith integration for tracing

## Phase 8: Frontend (Mandatory, built last)
- [x] Next.js app with Chat tab
- [x] Goals tab
- [x] Basic document management UI
- [x] UI Redesign (Modern, Dark Theme, Floating Elements)

## Phase 9: Future / Nice-to-Have
- [ ] Ollama Docker service (`llama3.2:3b`) for private data processing
- [ ] Transaction import + parsing (CSV/XLSX)
- [ ] Transaction anonymization (verified by Ollama locally)
- [ ] Transaction categorization (keyword + Ollama LLM fallback)
- [ ] Insights/analytics tab
- [ ] Export PDF reports
- [ ] Full JWT authentication (registration, login, tokens)
- [x] Full i18n UI toggle (RO/EN language switcher for labels)
