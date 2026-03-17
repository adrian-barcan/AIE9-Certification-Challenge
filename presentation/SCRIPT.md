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

> "Let's talk about the problem.
>
> First -- financial literacy in Romania is still low. Many people want to invest, but they do not know where to start.
>
> Second -- information is everywhere. Government bonds, ETFs, mutual funds, stocks, and options are explained in different places, with different language and different rules. There is no single place that puts everything together in a simple way.
>
> Third -- there is no personal guidance. Generic AI tools can give general answers, but they do not know your goals, your risk level, or your spending habits. And most people do not feel comfortable uploading bank data to a cloud AI.
>
> The result is simple: many people delay investing, or keep money in low-interest deposits, because comparing options feels too hard."

**→ Click Next**

---

## Slide 3: Success (1 min)

> "For this project, success means **user success**.
>
> Before BaniWise, users were in a reactive loop: search, compare, guess.
> With BaniWise, they get a proactive flow: ask, understand, act.
>
> They can compare options like government bonds, ETFs, mutual funds, stocks, and options in one place.
>
> Users get practical next steps: create goals, track progress, and improve spending.
>
> Users also get safer guidance, with source-grounded answers and compliance-aware responses."

**→ Click Next**

---

## Slide 4: Audience (1.5 min)

> "I focus on three types of users.
>
> **First-time investors**. People who heard about government bonds, ETFs, or mutual funds but do not know which option is right for them.
>
> **Goal-oriented savers**. People who want to track their savings and get advice based on their real situation.
>
> **Privacy-conscious users**. People who want AI help but do not want to share their bank data with the cloud.
>
> BaniWise supports all three in one app.
>
> For business, the idea is to start with Romanian retail users, then grow through banks, brokers, and financial education partners."

**→ Click Next**

---

## Slide 5: Solution (1.5 min)

> "BaniWise uses one supervisor agent that picks the right tool for each question.
>
> If you ask about a financial product, it searches the document knowledge base -- thirteen Romanian financial PDFs.
> If you ask for a live rate, it goes to the web for current data.
> If you ask about your goals, it reads or creates them in the database.
> If you upload your bank statement, it categorizes your spending locally and suggests where you can save.
>
> It also remembers your context across conversations.
> And it works in both Romanian and English.
>
> So the product is not just a chatbot - it is an assistant that guides decisions end to end."

**→ Click Next**

---

## Slide 6: Demo (3-4 min)

> "Enough slides. Let me show you how it works."

**→ Switch to the app (have it already open in another tab)**

### Demo Flow:

**1. RAG — Financial Knowledge (~1 min)**

- Type: *"What is TEZAUR?"*
- While it loads, say: *"This goes to the document tool. It searches Romanian financial PDFs."*
- When result appears: *"The answer is clear and simple. You can see the sources it used. And because this is about investing, a compliance disclaimer shows up automatically."*

**2. Market — Live Data (~45 sec)**

- Type: *"What is the EUR/RON exchange rate today?"*
- While it loads: *"Now it routes to a different tool -- live market search. Not the PDF knowledge base."*
- When result appears: *"This is today's data, not something static."*

**3. Goals — Create & Track (~45 sec)**

- Type: *"Create a goal of 50000 RON for a car"*
- When result appears: *"The app saved this goal. It will use it in future conversations to give better advice."*
- Optional: *"What are my financial goals?"*

**4. Transactions — Spending Insights (~1 min)**

- Upload a sample CSV bank statement
- While processing: *"Transactions are categorized by a local model. Raw data stays private -- it never goes to OpenAI."*
- Type: *"Where can I save money?"*
  - *"It gives saving tips by category -- like fees, shopping, transport."*
  - *"It uses categories, not your raw transaction details."*

> "So in one conversation, the app answered knowledge questions, got live data, created a personal goal, and gave private spending advice. That is the full flow."

**→ Switch back to slides, Click Next**

---

## Slide 7: Architecture (1.5 min)

> "The architecture is simple.
>
> The frontend sends messages to a FastAPI backend.
> A supervisor agent decides which tool to use: documents, market data, goals, or spending insights.
>
> Data lives in PostgreSQL and Qdrant for vector search.
> Live data comes from Tavily.
> Transaction categorization runs locally with Ollama and Mistral, so your data stays on your machine.
>
> For deployment, the frontend runs on Vercel, the backend and database on Railway, and vector search on Qdrant Cloud. I also use LangSmith for tracing and monitoring.
>
> The system is modular, easy to extend, and ready for real use."

**→ Click Next**

---

## Slide 8: Conclusions (1 min)

> "To wrap up:
>
> **What I built**: an AI assistant for Romanian investors that combines financial knowledge, live market context, personal goals, and spending insights.
>
> **What users get**: faster understanding, clearer decisions, and practical next steps in one app.
>
> **What matters most**: useful answers, trust, and privacy.
>
> **Roadmap**: I want to improve personalization, expand financial document coverage, and move toward production partnerships."

**→ Click Next**

---

## Slide 9: Thank You (15 sec)

> "Thank you! I hope this showed how BaniWise can make investing simpler, more personal, and more trustworthy -- starting with Romanian users, and in the future, maybe for you too."

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

