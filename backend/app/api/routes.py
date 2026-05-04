import json
import uuid
import os
import pickle
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from app.schemas.models import GenerateRequest, ChatRequest, AgentStatus
from app.graph import run_pipeline
from app.agents.planner import run_planner
from app.agents.architect import run_architect
from app.agents.coder import run_coder

router = APIRouter()

sessions: dict = {}
SESSIONS_FILE = "/tmp/ai_assistant_sessions.pkl"


def save_sessions():
    try:
        with open(SESSIONS_FILE, "wb") as f:
            pickle.dump(sessions, f)
    except Exception as e:
        print(f"Could not save sessions: {e}")


def load_sessions():
    global sessions
    try:
        if os.path.exists(SESSIONS_FILE):
            with open(SESSIONS_FILE, "rb") as f:
                sessions = pickle.load(f)
            print(f"Restored {len(sessions)} sessions from disk")
    except Exception as e:
        print(f"Could not load sessions: {e}")


# Load on startup
load_sessions()


# ── REST endpoint (simple, for testing) ─────────────────
@router.post("/generate")
async def generate(request: GenerateRequest):
    session_id = request.session_id or str(uuid.uuid4())
    try:
        result = run_pipeline(
            user_prompt = request.prompt,
            settings    = request.settings or {},
            session_id  = session_id,
        )
        sessions[session_id] = {
            "pipeline":        result,
            "chat_history":    [],
            "original_prompt": request.prompt,
        }
        save_sessions()
        return {"session_id": session_id, "result": result.model_dump()}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


# ── WebSocket endpoint (real-time streaming) ─────────────
@router.websocket("/ws/generate")
async def ws_generate(websocket: WebSocket):
    await websocket.accept()
    try:
        data       = await websocket.receive_text()
        payload    = json.loads(data)
        prompt     = payload.get("prompt", "")
        settings   = payload.get("settings", {})
        session_id = payload.get("session_id") or str(uuid.uuid4())

        await websocket.send_json({
            "type": "session", "session_id": session_id
        })

        # ── Planner ──────────────────────────────────────
        await websocket.send_json({
            "type": "agent_status", "agent": "planner", "status": "running"
        })
        try:
            planner_output = run_planner(prompt, settings)
            await websocket.send_json({
                "type":   "agent_complete",
                "agent":  "planner",
                "output": planner_output.model_dump(),
            })
        except Exception as e:
            await websocket.send_json({
                "type": "error", "agent": "planner", "message": str(e)
            })
            return

        # ── Architect ─────────────────────────────────────
        await websocket.send_json({
            "type": "agent_status", "agent": "architect", "status": "running"
        })
        try:
            architect_output = run_architect(planner_output, settings)
            await websocket.send_json({
                "type":   "agent_complete",
                "agent":  "architect",
                "output": architect_output.model_dump(),
            })
        except Exception as e:
            await websocket.send_json({
                "type": "error", "agent": "architect", "message": str(e)
            })
            return

        # ── Coder ─────────────────────────────────────────
        await websocket.send_json({
            "type": "agent_status", "agent": "coder", "status": "running"
        })
        try:
            coder_output = run_coder(architect_output, settings)
            await websocket.send_json({
                "type":   "agent_complete",
                "agent":  "coder",
                "output": coder_output.model_dump(),
            })
        except Exception as e:
            await websocket.send_json({
                "type": "error", "agent": "coder", "message": str(e)
            })
            return

        # ── Save session & send done ──────────────────────
        sessions[session_id] = {
            "planner_output":   planner_output,
            "architect_output": architect_output,
            "coder_output":     coder_output,
            "chat_history":     [],
            "original_prompt":  prompt,
            "settings":         settings,
        }
        save_sessions()  # ← persists to disk
        await websocket.send_json({"type": "done", "session_id": session_id})

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})


# ── Chat refinement endpoint ──────────────────────────────
@router.post("/chat")
async def chat(request: ChatRequest):
    session = sessions.get(request.session_id)
    if not session:
        print(f"Session {request.session_id} not found. Active sessions: {list(sessions.keys())}")
        return JSONResponse(status_code=404, content={"error": f"Session not found. Active sessions: {list(sessions.keys())}"})

    session["chat_history"].append({
        "role": "user", "message": request.message
    })

    try:
        architect_output = session.get("architect_output")
        if not architect_output:
            return JSONResponse(status_code=400, content={"error": "No architect output in session"})

        settings = session.get("settings", {})
        settings["extra_instruction"] = request.message

        new_coder_output = run_coder(
            architect_output = architect_output,
            settings         = settings,
        )
        session["coder_output"] = new_coder_output
        session["chat_history"].append({
            "role": "assistant", "message": "Code updated based on your request."
        })
        save_sessions()  # ← persists chat updates too
        return {
            "session_id":   request.session_id,
            "coder_output": new_coder_output.model_dump(),
            "chat_history": session["chat_history"],
        }
    except Exception as e:
        print(f"Chat error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


# ── Export session ────────────────────────────────────────
@router.get("/export/{session_id}")
async def export_session(session_id: str):
    session = sessions.get(session_id)
    if not session:
        return JSONResponse(status_code=404, content={"error": "Session not found"})
    return {
        "session_id":       session_id,
        "original_prompt":  session.get("original_prompt"),
        "planner_output":   session["planner_output"].model_dump()   if session.get("planner_output")   else None,
        "architect_output": session["architect_output"].model_dump() if session.get("architect_output") else None,
        "coder_output":     session["coder_output"].model_dump()     if session.get("coder_output")     else None,
        "chat_history":     session.get("chat_history", []),
    }