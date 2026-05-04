# ⚡ AI Coding Assistant

A multi-agent AI system that converts natural language prompts into complete, multi-file applications. Built with LangGraph, FastAPI, and React.

**Live Demo:** https://ai-coading-assistant.vercel.app  
**Backend API:** https://ai-coading-assistant.onrender.com

---

## What It Does

Type a prompt like _"Build me a React todo app with localStorage"_ and the system automatically generates a complete, runnable multi-file project using a coordinated pipeline of three specialized AI agents.

---

## Agent Pipeline

```
User Prompt → Planner Agent → Architect Agent → Coder Agent → Generated Code
```

| Agent         |                          Role                             |                               Output                          |
|---------------|---------------------------------------------------------- |---------------------------------------------------------------|
| **Planner**   | Breaks down the prompt into a structured project plan     | List of files, features, tech stack — Pydantic-validated JSON |
| **Architect** | Defines system architecture and inter-component contracts | Directory tree, file schemas, import/export contracts         |
| **Coder**     | Generates complete, runnable code for every file          | Full multi-file application                                   |

Each agent is a separate node in a LangGraph DAG. State is propagated across all nodes with zero data loss between handoffs.

---

## Tech Stack

|           Layer     |                 Technology                  |
|---------------------|---------------------------------------------|
| Agent Orchestration | LangGraph (stateful DAG)                    |
| LLM Framework       | LangChain                                   |
| Backend             | FastAPI + WebSocket streaming               |
| Frontend            | React + Vite                                |
| Schema Validation   | Pydantic (enforced at every agent boundary) |
| LLM Model           | GPT-4o (user provides their own API key)    | 
| Backend Hosting     | Render                                      |
| Frontend Hosting    | Vercel                                      |

---

## Features

- **Real-time streaming** — WebSocket delivers agent status updates live as each agent completes
- **File explorer** — Browse all generated files with syntax highlighting
- **Download All** — Export the entire project as a `.zip`
- **Refinement Chat** — Follow-up instructions re-run the Coder agent without regenerating everything
- **Session Export** — Export the full session (prompt, agent outputs, chat history) as JSON
- **No hardcoded keys** — Users paste their own OpenAI API key in the UI

---

## Project Structure

```
ai-coding-assistant/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── planner.py       # Planner agent
│   │   │   ├── architect.py     # Architect agent
│   │   │   └── coder.py         # Coder agent
│   │   ├── api/
│   │   │   └── routes.py        # FastAPI routes + WebSocket
│   │   ├── schemas/
│   │   │   └── models.py        # Pydantic models for all agent I/O
│   │   ├── prompts/
│   │   │   └── templates.py     # All system prompts (configurable)
│   │   ├── graph.py             # LangGraph DAG definition
│   │   └── main.py              # FastAPI app entry point
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── InputPanel.jsx       # Prompt input + API key
│       │   ├── AgentPipeline.jsx    # Live agent status display
│       │   ├── OutputPanel.jsx      # File explorer + code viewer
│       │   └── ChatPanel.jsx        # Refinement chat + export
│       ├── hooks/
│       │   └── useWebSocket.js      # WebSocket state management
│       ├── utils/
│       │   └── download.js          # Zip download + session export
│       └── App.jsx
├── samples/                         # Real test run exports
└── README.md
```

---

## Local Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- An OpenAI API key (GPT-4o access)

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend runs at `http://localhost:8000`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`

---

## Prompt Strategy

### Planner Agent
Uses **few-shot examples** with two complete input/output pairs to enforce strict JSON output structure. Temperature is set to `0.3` to balance creativity with consistency. The prompt explicitly forbids free-form text and requires all fields.

### Architect Agent
Uses **few-shot examples** showing complete file schemas with explicit imports, exports, and interface definitions. Temperature `0.2` — lower than Planner because architecture decisions need to be precise and consistent.

### Coder Agent
Uses **chain-of-thought prompting** — the prompt instructs the model to reason about each file before writing it (what it needs to do, what it imports, what it exports). Temperature `0.1` — lowest setting to minimize hallucinated imports or placeholder logic. When a chat refinement instruction is present, it is appended explicitly to the user message so the Coder applies changes across all affected files.

All prompts live in `backend/app/prompts/templates.py` and are never hardcoded in agent logic.

---

## Architecture Decisions & Tradeoffs

**Why LangGraph over plain LangChain?**  
LangGraph gives explicit control over the DAG structure, making the Planner → Architect → Coder sequence easy to reason about and extend. Each node has clear input/output contracts enforced by Pydantic.

**Why Pydantic at every boundary?**  
Each agent's output is validated before being passed to the next agent. This catches hallucinated or malformed JSON early and gives clear error messages instead of silent failures downstream.

**Why WebSockets over REST for generation?**  
Each agent call takes 10-30 seconds. WebSockets allow the frontend to show live progress per agent rather than waiting for the full pipeline to complete, which significantly improves perceived performance.

**In-memory session store**  
Sessions are stored in memory and persisted to a local pickle file on disk. This is intentional — the assignment doesn't require a database, and adding one would be over-engineering. The tradeoff is that sessions are lost if the server restarts and are not shared across multiple instances.

**Chat refinement only re-runs Coder**  
Follow-up instructions only re-run the Coder agent, not the full pipeline. This is faster and cheaper but means structural changes (like adding a new field to a type) may require a full regeneration. This is a known tradeoff documented here.

**Free tier cold starts**  
The Render free tier spins down after 15 minutes of inactivity. The first request after inactivity takes ~50 seconds to respond. For the interview, open the app 1-2 minutes before running a live prompt.

---

## Known Limitations

- Chat refinement works best for additive changes (adding features, styling). Structural changes to data models work better as a fresh generation.
- Generated code is not automatically executed or tested — output quality depends on the LLM.
- Sessions are not persistent across server restarts on Render free tier.
- `author` and `created_at` fields were occasionally omitted by the Planner when not explicitly emphasized in the prompt — always be specific in prompts.

---

## Sample Test Runs

See `/samples` directory for exported sessions from real test runs across multiple domains:
- React todo app with localStorage
- FastAPI blog REST API with comments

---

## Submission

Built by Swastika Pandit  
Deadline: 10 days from receipt
