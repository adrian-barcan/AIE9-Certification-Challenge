# BaniWise — Personal Financial Agent 🇷🇴

**AI-powered financial assistant for Romanian investors** — built as a certification challenge for the AI Engineering Bootcamp (AIE9).

This project demonstrates advanced mastery of **Retrieval-Augmented Generation (RAG)**, **Agentic Workflows (LangGraph)**, **Evaluations (RAGAS)**, and **Synthetic Data Generation**. 

## 🧠 Core AI Technologies

### 1. LangGraph Supervisor Agent ("BaniWise")
The heartbeat of the system is a **Supervisor Agent Pattern** powered by `GPT-4o`. It intelligently routes user queries to specialized tools:
- **`rag_query`**: Searches Romanian financial documents (TEZAUR, FIDELIS, BVB guides).
- **`market_search`**: Live financial data and news retrieval via the **Tavily Search API**.
- **`goals_*`**: Interface with the PostgreSQL database to manage and track user savings goals.

### 2. CoALA Memory Architecture
Implements 3 of the 5 cognitive memory types from the CoALA framework using LangGraph's new Postgres checkpointers:
- **Short-Term Memory**: Conversation thread context (`AsyncPostgresSaver`).
- **Long-Term Memory**: Persistent user profile and preferences (`AsyncPostgresStore` namespace).
- **Semantic Memory**: Learned financial facts about the user (`AsyncPostgresStore` namespace).

### 3. Advanced RAG Pipeline with Reranking
A highly optimized document retrieval system designed to ingest and query Romanian financial PDFs:
- **Ingestion**: Document parsing via `PyMuPDFLoader` and intelligent chunking (`RecursiveCharacterTextSplitter`).
- **Vector Storage**: `text-embedding-3-small` embeddings stored securely in a **Qdrant Vector DB**.
- **Contextual Compression**: Two-stage retrieval using **Cohere Rerank** (`rerank-multilingual-v3.0`). Searches pull the top-K documents from Qdrant, which Cohere then reranks to provide the precise top-N most contextually relevant chunks to the LLM.

### 4. Synthetic Data Generation (SDG) & Evaluation (RAGAS)
The `backend/evals/` directory contains a robust, programmatic evaluation suite:
- **Synthetic Data Generation**: Automates the creation of test sets from the raw PDFs using RAGAS `TestsetGenerator`. Produces Simple, Multi-Context, and Reasoning questions.
- **RAG Evaluation**: Uses **RAGAS** metrics (*Faithfulness, Answer Relevancy, Context Precision/Recall*) to mathematically prove the performance delta between a baseline top-K pipeline vs. the Cohere-reranked pipeline.
- **Agent Evaluation**: Custom programmatic evaluation testing the Supervisor model on Tool Routing accuracy, Topic Adherence, and **MiFID II Regulatory Compliance**.

---

## 🏗 Architecture

### AI System Overview

End-to-end stack: Frontend → FastAPI → LangGraph Supervisor → Tools & CoALA Memory.

```mermaid
flowchart TB
    subgraph Client["🖥️ Client Layer"]
        FE[Next.js Frontend]
    end

    subgraph API["⚡ Backend API"]
        FastAPI[FastAPI]
        ChatAPI["/api/chat"]
        DocsAPI["/api/documents/ingest"]
        GoalsAPI["/api/goals"]
        FastAPI --> ChatAPI
        FastAPI --> DocsAPI
        FastAPI --> GoalsAPI
    end

    subgraph Agent["🧠 AI Agent Layer"]
        Supervisor[LangGraph Supervisor<br/>GPT-4o]
        Tools[Specialist Tools]
        Supervisor --> Tools
    end

    subgraph ToolsDetail[" "]
        RAG[rag_query]
        Market[market_search]
        GoalsTool[goals_summary<br/>create_goal]
        Tools --> RAG
        Tools --> Market
        Tools --> GoalsTool
    end

    subgraph Memory["📦 CoALA Memory"]
        STM[Short-Term<br/>AsyncPostgresSaver]
        LTM[Long-Term<br/>Profile Store]
        SEM[Semantic<br/>Knowledge Store]
    end

    subgraph External["☁️ External Services"]
        OpenAI[OpenAI API<br/>GPT-4o / Embeddings]
        Qdrant[Qdrant<br/>Vector DB]
        Cohere[Cohere<br/>Reranker]
        Tavily[Tavily<br/>Web Search]
        PG[(PostgreSQL)]
    end

    FE -->|HTTP/SSE| FastAPI
    ChatAPI --> Supervisor
    DocsAPI --> RAG
    GoalsAPI --> PG

    Supervisor <-->|context & history| Memory
    RAG --> Qdrant
    RAG --> Cohere
    RAG --> OpenAI
    Market --> Tavily
    GoalsTool --> PG
    Supervisor -->|completion| OpenAI
```

### RAG Pipeline

Ingestion (PDF → Qdrant + BM25) and retrieval (Ensemble → Cohere Rerank).

```mermaid
flowchart LR
    subgraph Ingest["📥 Ingestion"]
        PDF[PDF Files]
        Load[PyMuPDFLoader]
        ParentSplit[Parent Splitter<br/>2k chars]
        ChildSplit[Child Splitter<br/>400 chars]
        Embed[OpenAI Embeddings<br/>text-embedding-3-small]
        QdrantW[(Qdrant<br/>Vectors)]
        DocStore[(DocStore<br/>Parents)]
        BM25Store[BM25 Index]
        PDF --> Load
        Load --> ParentSplit
        ParentSplit --> ChildSplit
        ChildSplit --> Embed
        Embed --> QdrantW
        ParentSplit --> DocStore
        ParentSplit --> BM25Store
    end
```

```mermaid
flowchart TB
    subgraph Query["🔍 Query Path"]
        Q[User Question]
        EmbQ[Embed Question]
        VecRet[Vector Retriever<br/>ParentDocumentRetriever]
        BM25[BM25 Retriever]
        Ensemble[Ensemble Retriever<br/>0.3 BM25 + 0.7 Vector]
        Rerank[Cohere Rerank<br/>rerank-multilingual-v3.0]
        TopN[Top-N Chunks]
        Format[Formatted Context]
        Q --> EmbQ
        EmbQ --> VecRet
        VecRet --> Ensemble
        BM25 --> Ensemble
        Ensemble -->|top_k candidates| Rerank
        Rerank --> TopN
        TopN --> Format
    end

    subgraph Stores["Stores"]
        Qdrant[(Qdrant)]
        DocStore[(DocStore)]
        BM25Idx[BM25]
    end

    VecRet --> Qdrant
    VecRet --> DocStore
    BM25 --> BM25Idx
```

### CoALA Memory

Short-term, long-term, semantic memory and rolling summarization.

```mermaid
flowchart TB
    subgraph UserRequest["Incoming Request"]
        Req[user_id + session_id<br/>+ message]
    end

    subgraph ShortTerm["📌 Short-Term (Working) Memory"]
        Thread[Conversation Thread]
        Checkpointer[AsyncPostgresSaver]
        Thread -->|thread_id| Checkpointer
        Note1["Recent messages in context window"]
    end

    subgraph Consolidation["Rolling Consolidation"]
        Trim[Trim old messages]
        Summarize[MemoryService.summarize_messages<br/>GPT-4o-mini]
        SummaryKey["(user_id, summary, session_id)"]
        Trim --> Summarize
        Summarize --> SummaryKey
    end

    subgraph LongTerm["📚 Long-Term Memory"]
        ProfileNS["(user_id, profile)"]
        ProfileStore[AsyncPostgresStore]
        ProfileNS --> ProfileStore
        Note2["Persistent preferences"]
    end

    subgraph Semantic["🔬 Semantic Memory"]
        KnowledgeNS["(user_id, knowledge)"]
        KnowledgeStore[AsyncPostgresStore]
        KnowledgeNS --> KnowledgeStore
        Note3["Learned financial facts"]
    end

    subgraph Prompt["System Prompt Injection"]
        UserContext["USER CONTEXT: Conversation summary, User profile, Known financial context"]
    end

    Req --> Thread
    Req --> ProfileNS
    Req --> KnowledgeNS
    Checkpointer --> Trim
    SummaryKey --> UserContext
    ProfileStore --> UserContext
    KnowledgeStore --> UserContext
    UserContext --> Supervisor[Supervisor LLM]
```

### Agent Tool Routing

Supervisor routing to `rag_query`, `market_search`, `goals_summary`, `create_goal`.

```mermaid
flowchart TB
    User[User Message]
    Sys[System Prompt<br/>+ User Context + MiFID II rules]
    Supervisor[Supervisor<br/>GPT-4o]
    User --> Supervisor
    Sys --> Supervisor

    Supervisor --> Decision{Tool choice}

    Decision -->|Document/regulations<br/>HOW products work| RAG[rag_query]
    Decision -->|Live data, news<br/>prices, EUR/RON| Market[market_search]
    Decision -->|Goals, progress| GoalsSum[goals_summary]
    Decision -->|Create new goal| CreateGoal[create_goal]
    Decision -->|No tool / combine| Direct[Direct answer]

    RAG --> RAGService[RAG Service<br/>Qdrant + Cohere]
    Market --> Tavily[Tavily API]
    GoalsSum --> GoalsService[Goals Service<br/>PostgreSQL]
    CreateGoal --> GoalsService

    RAGService --> Context[Context to LLM]
    Tavily --> Context
    GoalsService --> Context
    Context --> Supervisor
    Direct --> Response[Streamed Response]
    Supervisor --> Response
```

More detail (and export options) in **[`diagrams/`](diagrams/)**.


## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| **LLM Models** | OpenAI GPT-4o (Supervisor) & GPT-4o-mini |
| **Agent Framework** | LangChain + LangGraph |
| **Vector DB** | Qdrant |
| **Embeddings** | OpenAI `text-embedding-3-small` |
| **Reranking** | Cohere `rerank-multilingual-v3.0` |
| **Web Search** | Tavily API |
| **Evaluation Suite** | RAGAS (`ragas`) + JupyterSDG |
| **Backend API** | FastAPI (Python 3.11) |
| **Frontend** | Next.js 14 + TypeScript + TailwindCSS |
| **Relational DB** | PostgreSQL 16 (sqlalchemy / asyncpg) |

---

## 🚀 Quick Start

```bash
# 1. Copy environment template and add your API keys (OpenAI, Cohere, Tavily)
cp .env.example .env

# 2. Start all services using Docker Compose
docker compose up --build

# 3. Verify services are running
open http://localhost:8000/docs   # FastAPI Swagger UI
open http://localhost:3000        # Next.js Frontend
```

## 📁 Project Structure

```text
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI application entry point
│   │   ├── api/             # REST API routers (chat, goals, docs, users)
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── schemas.py       # Pydantic validation schemas
│   │   └── services/
│   │       ├── agent_service.py # LangGraph Supervisor & CoALA Memory
│   │       ├── rag_service.py   # Qdrant + Cohere Contextual Compression
│   │       └── goals_service.py # Financial PostgreSQL logic
│   ├── documents/           # Romanian financial PDFs (Knowledge Base)
│   └── evals/
│       ├── sdg_and_evaluation.ipynb # Full SDG + Eval interactive walkthrough
│       ├── eval_rag.py      # Automated RAGAS baseline vs reranked tests
│       └── eval_agent.py    # Automated Agent routing & compliance tests
├── frontend/                # Next.js 14 Chat & Goals UI
├── docker-compose.yml       # Production-ready container orchestration
└── .env.example
```

## 🔌 Core API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/chat` | Streaming endpoint chatting directly with the LangGraph Agent |
| `GET` | `/api/chat/history/{session_id}` | Retrieves CoALA Short-Term memory history |
| `POST` | `/api/documents/ingest` | Triggers the RAG Pipeline to chunk and embed new PDFs |
| `GET` | `/api/goals?user_id=` | Fetches financial savings goals from PostgreSQL |
| `POST` | `/api/goals?user_id=` | Creates a new financial goal |

## 📜 License

[MIT License](LICENSE)
