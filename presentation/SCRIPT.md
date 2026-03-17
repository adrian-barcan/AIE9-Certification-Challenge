# BaniWise — 10-Minute Presentation Script

> **Total time: 10 minutes.** Speak naturally, don't read word-for-word. Use this as a guide. Bolded phrases are key points to emphasize.

---

## Slide 1: Title (30 sec)

> "Hi everyone, I'm Adrian Barcan. This is **BaniWise** - an AI financial assistant built for Romanian investors.
>
> **Mission:** turn financial confusion into clear next actions.
>
> The goal is simple: help users understand options faster, make better decisions, and plan their money with confidence."

**→ Click Next**

---

## Slide 2: Problem (1.5 min)

> "Let's start with the problem.
>
> Financial information is hard to use. It's spread across MFinante, ASF, BVB, and long PDF documents.
>
> A user asking *'What is TEZAUR and is it right for me?'* has to search multiple websites, compare products, and understand rules alone.
>
> Existing tools are either generic or too limited. They do not combine Romanian financial knowledge, user goals, and private spending insights in one place."

**→ Click Next**

---

## Slide 3: Success (1 min)

> "For this project, success is **user success**.
>
> Before BaniWise, users were in a reactive loop: search, compare, guess.
> With BaniWise, they get a proactive flow: ask, understand, act.
>
> Users get clear answers quickly, instead of reading dense documents.
>
> Users get practical next steps: understand products, compare options, create goals, and improve spending.
>
> Users also get safer guidance, with source-grounded answers and compliance-aware responses."

**→ Click Next**

---

## Slide 4: Audience (1.5 min)

> "We focus on three users.
>
> **First-time investors** who need simple answers about products like TEZAUR and FIDELIS.
>
> **Goal-oriented savers** who want to track progress and get advice based on their situation.
>
> **Privacy-conscious users** who want AI support without exposing raw transaction data.
>
> BaniWise is built to support all three in one flow.
>
> Business focus: start with Romanian retail users, then expand through bank, broker, and financial educator partnerships."

**→ Click Next**

---

## Slide 5: Solution (1.5 min)

> "BaniWise uses one supervisor agent that chooses the right tool for each question.
>
> If the user asks about Romanian financial products, it uses document retrieval.
> If the user asks for live rates, it uses market search.
> If the user asks about planning, it uses goals and savings tools.
>
> It also uses memory to keep context, and a privacy-first transaction flow where raw data stays local and only anonymized insights are shared.
>
> So the product is not just a chatbot - it is an assistant that guides decisions end to end."

**→ Click Next**

---

## Slide 6: Demo (3-4 min)

> "Enough slides — let me show you how it actually works."

**→ Switch to the app (have it already open in another tab)**

### Demo Flow:

**1. RAG — Financial Knowledge (~1 min)**

- Type: *"Ce este TEZAUR?"*
- While it loads, say: *"This goes to the document tool for Romanian financial knowledge."*
- Point out:
  - *"The answer is simple and source-grounded."*
  - *"For investment topics, compliance disclaimer appears automatically."*

**2. Market — Live Data (~45 sec)**

- Type: *"Care este cursul EUR/RON astazi?"*
- While it loads: *"Now it routes to live market search, not the PDF knowledge base."*
- Point out:
  - *"This is current data, not static content."*

**3. Goals — Create & Track (~45 sec)**

- Type: *"Creeaza un obiectiv de 50000 RON pentru o masina"*
- Point out:
  - *"The app stores the goal and uses it in future conversations."*
- Optional: *"Care sunt obiectivele mele financiare?"*

**4. Transactions — Spending Insights (~1 min)**

- Upload a sample CSV bank statement
- While processing: *"Transactions are categorized locally, and raw data stays private."*
- Type: *"Where can I save money?"*
  - *"The app gives practical saving suggestions by spending category."*
  - *"It uses categories, not raw sensitive details."*

> "In one conversation, the app answered knowledge questions, fetched live data, used personal goals, and gave privacy-preserving spending advice."

**→ Switch back to slides, Click Next**

---

## Slide 7: Architecture (1.5 min)

> "Architecture is simple to explain.
>
> Frontend sends user messages to a FastAPI backend.
> A supervisor agent routes each message to the right capability: documents, market data, goals, or savings insights.
>
> Data is stored in PostgreSQL and Qdrant.
> Live data comes from Tavily.
> Transaction categorization can run locally with Ollama for privacy.
>
> So the system is modular, practical, and ready for real usage."

**→ Click Next**

---

## Slide 8: Conclusions (1 min)

> "To wrap up:
>
> **What we built**: an AI assistant for Romanian investors that combines financial knowledge, live market context, personal goals, and spending insights.
>
> **What users get**: faster understanding, clearer decisions, and practical next steps in one app.
>
> **What matters most**: useful answers, trust, and privacy.
>
> **Roadmap**: improve personalization, expand financial document coverage, and move toward production partnerships."

**→ Click Next**

---

## Slide 9: Thank You (15 sec)

> "Thank you! I hope this showed how BaniWise makes investing simpler, more personal, and more trustworthy for Romanian users."

---

## Tips for Recording

- **Keep sentences short** — one idea at a time
- **Focus on user value** — avoid too much technical depth
- **Don't rush the demo** — narrate while waiting for responses
- **Point at the screen** when showing citations, goals, and privacy behavior
- **If something breaks**: use a backup screenshot and continue
- **Energy**: calm start, strongest energy during demo, clear close
- **Audio**: speak clearly and keep a steady volume
- **Confidence**: simple language sounds stronger than complex language

