# Prompt pentru Claude Code — Agent Financiar Personal (România)

---

## CONTEXT ȘI OBIECTIV

Construiește o aplicație web completă pentru un **agent financiar personal AI** destinat investitorilor din România. Aplicația combină:
- **RAG** (Retrieval-Augmented Generation) pe documente reglementare românești
- **Internet search în timp real** pentru date de piață
- **Procesare și anonimizare tranzacții** bancare
- **Obiective financiare** cu memorie persistentă per utilizator
- **Chat AI** cu context financiar personalizat

---

## STACK TEHNIC

**Backend:**
- Python 3.11+
- FastAPI (REST API + WebSockets pentru chat)
- LangChain sau LlamaIndex pentru RAG orchestration
- Qdrant (vector database, self-hosted via Docker)
- PostgreSQL (user profiles, goals, transactions)
- Redis (cache sesiuni, rate limiting)

**LLM & AI:**
- Anthropic Claude (claude-opus-4-6 sau claude-sonnet-4-6) — model principal
- OpenAI text-embedding-3-small — embeddings pentru RAG
- Tavily API — web search pentru date live

**Frontend:**
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- Recharts pentru vizualizări financiare
- React Hook Form + Zod pentru validare

**Infrastructure:**
- Docker + Docker Compose pentru development
- `.env` pentru toate cheile API

---

## STRUCTURA PROIECTULUI

```
financial-agent/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── chat.py
│   │   │   ├── transactions.py
│   │   │   ├── goals.py
│   │   │   └── documents.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   └── security.py
│   │   ├── services/
│   │   │   ├── rag_service.py
│   │   │   ├── transaction_service.py
│   │   │   ├── anonymizer.py
│   │   │   ├── categorizer.py
│   │   │   ├── goals_service.py
│   │   │   └── agent_service.py
│   │   └── models/
│   │       ├── transaction.py
│   │       ├── goal.py
│   │       └── user.py
│   ├── documents/          # Documente RAG locale
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   └── (routes)/
│   │       ├── transactions/
│   │       ├── insights/
│   │       ├── goals/
│   │       └── chat/
│   ├── components/
│   ├── lib/
│   └── package.json
├── docker-compose.yml
└── .env.example
```

---

## MODULE DE IMPLEMENTAT

### 1. RAG SERVICE (`backend/app/services/rag_service.py`)

Implementează un RAG pipeline complet:

```python
# Cerințe funcționale:
# - Încarcă documente PDF/DOCX din folderul /documents
# - Chunking: 512 tokens cu overlap 64
# - Embeddings via OpenAI text-embedding-3-small
# - Stocare în Qdrant collection "financial_docs_ro"
# - Retrieval: top-5 chunks relevante per query
# - Re-ranking după relevanță

class RAGService:
    async def ingest_documents(self, folder_path: str) -> dict
    async def query(self, question: str, top_k: int = 5) -> list[Document]
    async def get_context_for_prompt(self, question: str) -> str
```

**Documente de indexat automat** (descărcate sau copiate manual în `/documents`):
- Regulamente ASF (asf.ro)
- Template KID/KIID fonduri mutuale
- Documentație FIDELIS / TEZAUR (mfinante.ro)
- MiFID II summary în română
- Ghid investitor BVB

---

### 2. TRANSACTION SERVICE (`backend/app/services/transaction_service.py`)

#### 2a. Parser CSV/XLSX

Suportă formate de export de la băncile românești principale:

```python
class TransactionParser:
    def parse_bcr(self, file: bytes) -> list[Transaction]
    def parse_ing(self, file: bytes) -> list[Transaction]  
    def parse_raiffeisen(self, file: bytes) -> list[Transaction]
    def parse_bt(self, file: bytes) -> list[Transaction]
    def parse_revolut(self, file: bytes) -> list[Transaction]
    def parse_generic_csv(self, file: bytes) -> list[Transaction]
    
    # Auto-detectează banca după structura fișierului
    def auto_detect_and_parse(self, file: bytes, filename: str) -> list[Transaction]
```

#### 2b. Anonymizer (`backend/app/services/anonymizer.py`)

```python
class TransactionAnonymizer:
    # Regulile de anonimizare:
    # 1. IBAN-uri: RO49AAAA1B31007593840000 → RO49****3840000 (păstrează primele 4 + ultimele 7)
    # 2. Numere de card: **** **** **** 1234
    # 3. Nume persoane fizice (regex + NLP): înlocuiește cu "Persoană fizică"
    # 4. CNP-uri: înlocuiește cu [CNP_ANONIM]
    # 5. Adrese: detectează și înlocuiește cu [ADRESĂ]
    # 6. Telefoane: înlocuiește cu [TELEFON]
    # Păstrează: merchant names, sume, date, categorii
    
    def anonymize_transaction(self, transaction: Transaction) -> Transaction
    def anonymize_batch(self, transactions: list[Transaction]) -> list[Transaction]
    def get_anonymization_report(self, original, anonymized) -> dict
```

#### 2c. Categorizer (`backend/app/services/categorizer.py`)

```python
# Categorii principale + subcategorii
CATEGORIES = {
    "grocery": ["Kaufland", "Lidl", "Mega Image", "Carrefour", "Auchan", "Penny"],
    "transport": ["Rompetrol", "OMV", "MOL", "Bolt", "Uber", "CFR", "STB"],
    "food_delivery": ["Glovo", "Bolt Food", "Uber Eats", "Tazz"],
    "subscriptions": ["Netflix", "Spotify", "Digi", "Orange", "Vodafone", "RCS"],
    "utilities": ["Enel", "CEZ", "E.ON", "Electrica", "Distrigaz", "RAJA"],
    "housing": ["chirie", "ipoteca", "率 asociatie"],
    "health": ["Farmacia", "Catena", "Sensiblu", "Dr. Max", "Regina Maria"],
    "shopping": ["Zara", "H&M", "IKEA", "Decathlon", "Altex", "eMAG"],
    "coffee": ["Starbucks", "Five to Go", "Ted's Coffee", "Tucano"],
    "online": ["Amazon", "PayPal", "eMag"],
    "income": ["Salar", "Venit", "Dividende", "Pensie"],
    "transfers": ["Transfer", "Virament"],
    "atm": ["ATM", "Numerar"],
    "education": ["Udemy", "Coursera", "Scoala", "Facultate"],
    "entertainment": ["Cinema", "Theater", "Sport"],
}

class TransactionCategorizer:
    # Folosește mai întâi regex/keyword matching
    # Fallback: LLM classification pentru tranzacții necunoscute
    def categorize(self, transaction: Transaction) -> CategoryResult
    def categorize_batch(self, transactions: list[Transaction]) -> list[Transaction]
    def recategorize(self, transaction_id: str, new_category: str) -> Transaction  # manual override
```

---

### 3. GOALS SERVICE (`backend/app/services/goals_service.py`)

```python
class GoalsService:
    # CRUD complet cu persistență PostgreSQL
    async def create_goal(self, user_id: str, goal: GoalCreate) -> Goal
    async def get_goals(self, user_id: str) -> list[Goal]
    async def update_goal(self, goal_id: str, update: GoalUpdate) -> Goal
    async def delete_goal(self, goal_id: str) -> bool
    async def add_contribution(self, goal_id: str, amount: float) -> Goal
    
    # Calcule automate
    def calculate_months_to_goal(self, goal: Goal) -> int | None
    def calculate_required_monthly(self, goal: Goal) -> float
    def get_goal_recommendations(self, goal: Goal, income: float) -> list[str]
    def check_goal_feasibility(self, goal: Goal, monthly_savings: float) -> GoalFeasibility
```

**Schema Goal (PostgreSQL):**
```sql
CREATE TABLE goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    name VARCHAR(200) NOT NULL,
    icon VARCHAR(10) DEFAULT '🎯',
    target_amount DECIMAL(12,2) NOT NULL,
    saved_amount DECIMAL(12,2) DEFAULT 0,
    monthly_contribution DECIMAL(10,2),
    deadline DATE,
    priority INTEGER DEFAULT 1,  -- 1=low, 2=medium, 3=high
    status VARCHAR(20) DEFAULT 'active',  -- active, completed, paused
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

### 4. AGENT SERVICE (`backend/app/services/agent_service.py`)

Orchestrează întregul flow al agentului:

```python
class FinancialAgentService:
    def __init__(self, rag_service, search_service, goals_service):
        self.tools = [
            # Tool 1: RAG query
            Tool(name="query_financial_docs", func=rag_service.query,
                 description="Caută în documentele reglementare românești (ASF, BVB, fonduri mutuale, TEZAUR)"),
            
            # Tool 2: Web search live
            Tool(name="search_market_data", func=search_service.search,
                 description="Caută date live: cotații BVB, curs BNR, dobânzi, știri financiare"),
            
            # Tool 3: BNR rates
            Tool(name="get_bnr_rates", func=self._get_bnr_rates,
                 description="Obține cursurile valutare zilnice de la BNR"),
            
            # Tool 4: Goals summary
            Tool(name="get_user_goals", func=goals_service.get_goals,
                 description="Returnează obiectivele financiare ale utilizatorului"),
            
            # Tool 5: Spending analysis
            Tool(name="analyze_spending", func=self._analyze_spending,
                 description="Analizează cheltuielile utilizatorului pe categorii"),
        ]
    
    async def chat(self, user_id: str, message: str, session_id: str) -> AgentResponse:
        # 1. Încarcă contextul utilizatorului (goals, spending summary)
        # 2. Decide ce tools să folosească (Router LLM)
        # 3. Execută tools în paralel unde e posibil
        # 4. Sintetizează răspunsul cu Claude
        # 5. Adaugă disclaimer MiFID II când e relevant
        # 6. Salvează în conversation history
        ...

SYSTEM_PROMPT = """
Ești FinAgent, un asistent financiar personal pentru investitori din România.

PERSONALITATE:
- Direct și concis, fără fluff
- Folosești date reale când sunt disponibile
- Citezi întotdeauna sursa informației (RAG doc sau web search)
- Ești familiar cu piața românească: BVB, fonduri în lei, TEZAUR, FIDELIS, pensii private

CONTEXT UTILIZATOR (injectat dinamic):
{user_context}

REGULI OBLIGATORII:
1. Când oferi informații despre produse de investiții, adaugă: 
   "⚠️ Informație generală — nu constituie consultanță financiară personalizată conform MiFID II / Legea 126/2018."
2. Citează sursa pentru orice afirmație specifică
3. Dacă nu știi ceva cu certitudine, spune-o explicit
4. Răspunzi în română, cu termeni financiari corecți

INSTRUMENTE DISPONIBILE: {tools}
"""
```

---

### 5. API ENDPOINTS (`backend/app/api/`)

```python
# chat.py
POST /api/chat                    # Send message, returns streaming response
GET  /api/chat/history/{session}  # Get conversation history
DELETE /api/chat/history/{session}

# transactions.py  
POST /api/transactions/upload     # Upload CSV/XLSX (multipart)
GET  /api/transactions            # List transactions (paginated, filterable)
POST /api/transactions/anonymize  # Anonymize batch
PUT  /api/transactions/{id}/category  # Manual recategorize
GET  /api/transactions/summary    # Aggregated stats by category + period
GET  /api/transactions/insights   # AI-generated savings tips

# goals.py
GET    /api/goals                 # List user goals
POST   /api/goals                 # Create goal
PUT    /api/goals/{id}            # Update goal
DELETE /api/goals/{id}            # Delete goal
POST   /api/goals/{id}/contribute # Add contribution amount
GET    /api/goals/{id}/projection # Calculate timeline projection

# documents.py
POST /api/documents/ingest        # Trigger RAG re-indexing
GET  /api/documents               # List indexed documents
DELETE /api/documents/{id}        # Remove document from index
```

---

### 6. FRONTEND (`frontend/`)

#### Layout principal — 4 tab-uri:

**Tab 1: `/transactions`**
- Upload zone drag & drop (acceptă CSV, XLSX)
- Auto-detect bancă din structura fișierului
- Tabel cu tranzacții: data, descriere, sumă, categorie (editabilă)
- Buton "🔒 Anonimizează" — afișează raport înainte/după
- Stats bar: venit total / cheltuieli / sold net / rată economii
- Filtru pe perioadă, categorie, sumă

**Tab 2: `/insights`**
- Pie chart sau bar chart cheltuieli pe categorii (Recharts)
- Progress bars per categorie cu comparație față de luna precedentă
- Secțiune "Oportunități economii" — cards cu sumă potențială
- Secțiune "Potențial investiție" — recomandări bazate pe surplus
- Export PDF raport lunar

**Tab 3: `/goals`**
- Grid de cards cu obiective active
- Progress bar animat per obiectiv
- Calcul automat luni rămase
- Form creare obiectiv: nume, icon picker, target, contribuție lunară, deadline
- Quick-add contribuție (+100, +500, custom)
- Stare: activ / completat / în pauză

**Tab 4: `/chat`**
- Chat interface cu streaming responses
- Context badge: "📊 Cunoaște X tranzacții · Y obiective"
- Suggested questions dinamice bazate pe date utilizator
- Citare surse inline în răspunsuri (RAG doc sau web)
- Disclaimer MiFID II auto-afișat pentru sfaturi investiții

---

### 7. DOCKER COMPOSE (`docker-compose.yml`)

```yaml
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    env_file: .env
    depends_on: [postgres, qdrant, redis]
    volumes: ["./documents:/app/documents"]

  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    env_file: .env

  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: financial_agent
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes: ["postgres_data:/var/lib/postgresql/data"]

  qdrant:
    image: qdrant/qdrant:latest
    ports: ["6333:6333"]
    volumes: ["qdrant_data:/qdrant/storage"]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
```

---

### 8. ENVIRONMENT VARIABLES (`.env.example`)

```env
# LLM
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...          # pentru embeddings

# Search
TAVILY_API_KEY=tvly-...

# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=financial_agent
POSTGRES_USER=agent
POSTGRES_PASSWORD=changeme

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Redis
REDIS_URL=redis://localhost:6379

# App
SECRET_KEY=generate-random-32-chars
CORS_ORIGINS=http://localhost:3000
ENVIRONMENT=development

# RAG
DOCUMENTS_FOLDER=./documents
EMBEDDING_MODEL=text-embedding-3-small
QDRANT_COLLECTION=financial_docs_ro
CHUNK_SIZE=512
CHUNK_OVERLAP=64
```

---

## CERINȚE DE CALITATE

### Securitate & Privacy
- Toate datele financiare stocate encrypted at rest (PostgreSQL pgcrypto)
- Anonimizarea rulează **client-side sau înainte de orice call LLM extern**
- Nu trimite IBAN-uri sau CNP-uri reale la API-uri externe
- Rate limiting pe toate endpoint-urile (Redis)
- Input validation strictă pe upload (tipuri fișiere, dimensiune max 10MB)

### Error Handling
- Fallback graceful dacă Tavily API nu e disponibil (răspunde fără date live)
- Fallback dacă Qdrant e gol (răspunde fără context RAG, menționează explicit)
- Retry logic pentru API calls externe (3 retries, exponential backoff)

### Performance
- Embeddings calculate async la upload document
- Transaction categorization în batch (nu per tranzacție)
- Streaming responses pentru chat (nu aștepți tot răspunsul)
- Cache BNR rates (TTL: 1 oră în Redis)

### Compliance
- Adaugă disclaimer MiFID II automat când agentul menționează produse de investiții
- Log toate interogările (fără date personale) pentru audit trail
- GDPR: endpoint `DELETE /api/users/{id}/data` pentru ștergere completă

---

## ORDINEA DE IMPLEMENTARE

1. **Docker Compose** + servicii de bază (Postgres, Qdrant, Redis)
2. **Database migrations** (Alembic) + modele SQLAlchemy
3. **RAG Service** — ingestie documente + query
4. **Transaction Service** — parser + anonymizer + categorizer
5. **Goals Service** — CRUD + calcule
6. **Agent Service** — LangChain agent cu tools
7. **FastAPI endpoints** + auth basic
8. **Frontend Next.js** — toate cele 4 tab-uri
9. **Docker build** pentru producție
10. **README.md** cu instrucțiuni setup complet

---

## NOTE FINALE

- Comentează codul în **română** pentru business logic, **engleză** pentru cod tehnic
- Adaugă `pytest` tests pentru anonymizer și categorizer (cele mai critice)
- Creează un script `seed_demo_data.py` cu 30 de tranzacții demo pentru testare rapidă
- README să conțină pași de la `git clone` la `docker compose up` în sub 5 minute
