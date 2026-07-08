# AI-First CRM — HCP Module: "Log Interaction Screen"

A production-ready Customer Relationship Management (CRM) module specifically tailored for life-sciences field sales representatives. This application features a dual-mode interaction logging screen allowing reps to log doctor visits, phone calls, and emails either through a **Structured Form** or using natural language via a **Conversational AI Agent**.

---

## 🏗️ System Architecture

The application is split into three main components:
1. **Frontend**: React (Vite) + Redux Toolkit for clean state management and premium typography (Google Inter).
2. **Backend**: Python + FastAPI exposing high-performance REST APIs.
3. **AI Layer**: LangGraph (StateGraph) coordinating conversational threads, intent routing, JSON entity extraction, database tool execution, and natural response formatting, powered by **Groq**.

```
┌─────────────────────────────┐
│   React + Redux Frontend    │
│  ┌───────────┐ ┌──────────┐ │
│  │ Structured│ │Conversat.│ │
│  │   Form    │ │ Chat UI  │ │
│  └─────┬─────┘ └────┬─────┘ │
└────────┼────────────┼───────┘
         │ REST/JSON   │
         │             │
┌────────▼────────────▼───────┐
│        FastAPI Backend      │
│  /interactions   /chat      │
│  /hcps  /followups  /agent  │
└────────┬─────────────────────┘
         │
┌────────▼─────────────────────┐
│      LangGraph Agent          │
│  StateGraph orchestrating:    │
│   - intent router node        │
│   - tool-calling node (Groq)  │
│   - tool execution node       │
│   - response formatter node   │
└────────┬───────────┬──────────┘
         │            │
┌────────▼───┐  ┌─────▼──────────┐
│ Groq LLM   │  │ 5 Agent Tools   │
│ API        │  │ (Python funcs)  │
│            │  └─────┬───────────┘
└────────────┘        │
             ┌────────▼────────┐
             │ SQLite / Postgres│
             │  HCPs, Interac-  │
             │  tions, Users    │
             └──────────────────┘
```

---

## 🛠️ The 5 LangGraph Tools

The conversational AI agent is equipped with five specific tools, each mapping to a real Python function executing operations against the SQLAlchemy database:

1. **`log_interaction`**: Resolves an HCP by name (or creates a new record if they do not exist), invokes the primary LLM to write a 1-2 sentence professional summary of the meeting notes, and logs the interaction.
2. **`edit_interaction`**: Modifies an existing interaction log (e.g., updating sentiment, topics, or sample distribution quantities) and writes an audit log to `interaction_edits` for history tracking.
3. **`lookup_hcp`**: Performs a fuzzy search of HCPs by name or specialty and returns matching profiles alongside their last three visits.
4. **`schedule_followup`**: Flags an interaction as requiring follow-up and saves the follow-up date (format: `YYYY-MM-DD`).
5. **`summarize_interaction_history`**: Aggregates all historical visits for a specific doctor and calls the context LLM to generate an actionable relationship summary (highlights talking points, sentiment trends, and recent samples given) — preparing the rep for their next visit.

---

## ⚡ Note on Groq Models Choice

The original assignment specifies `gemma2-9b-it`. As of Groq's official deprecation timeline, `gemma2-9b-it` has been retired. Consequently, this project is built using:
- **Primary Model**: `llama-3.1-8b-instant` (handles fast intent classification, JSON entity extraction, and response formatting).
- **Context/Reasoning Model**: `llama-3.3-70b-versatile` (handles complex relationship summaries).

These models are fully configurable via `.env` variables so they can be changed instantly.

---

## 🚀 Setup & Running Instructions

Ensure you have **Node.js** (v18+) and **Python** (3.11+) installed on your machine.

### 1. Configuration & Environments
Copy the environment template files in both backend and frontend, and input your Groq API key:

**Backend Setup:**
```bash
cd backend
cp .env.example .env
# Edit .env and enter your GROQ_API_KEY
```

**Frontend Setup:**
```bash
cd ../frontend
cp .env.example .env
```

### 💾 Database Configuration & Production Warnings

* **Local Dev Fallback**: By default, the application runs on **SQLite** (`aicrm.db`) for easy local development without setting up database servers.
* **Production Database (PostgreSQL/MySQL)**: In production (e.g. deployed on Render), you must set the `DATABASE_URL` environment variable pointing to a PostgreSQL or MySQL instance. 
* > [!WARNING]
  > **Do not use SQLite in production.** Render's free tier has an ephemeral filesystem. If you run SQLite in production on Render, the database file will be deleted and reset on every server restart or redeploy, causing you to lose all logged interactions. Always provision and link a PostgreSQL database for production deployments.

---

### 2. Running Locally (Directly)

#### Run Backend Server:
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the FastAPI development server:
   ```bash
   # Run from backend/app folder to ensure imports resolve correctly
   cd app
   python -m uvicorn main:app --host 127.0.0.1 --port 8000
   ```
   *Note: Upon starting, the backend will automatically initialize a local SQLite database (`aicrm.db`) and seed it with 5 mock Healthcare Professionals (Cardiology, Endocrinology, etc.) and 2 initial interactions so you have data on load.*

#### Run Frontend Client:
1. Open a new terminal and navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install Node dependencies:
   ```bash
   npm install
   ```
3. Run the Vite development server:
   ```bash
   npm run dev
   ```
4. Open the application in your browser:
   `http://localhost:5173/`

---

### 3. Running via Docker Compose (Docker Setup)
If you have Docker installed and wish to run the full PostgreSQL-backed multi-service stack:
```bash
docker-compose up --build
```
- Frontend will be available at: `http://localhost:3000`
- Backend API docs will be available at: `http://localhost:8000/docs`
