import json
import uuid
import os
import redis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from app.schemas.models import GenerateRequest, ChatRequest, AgentStatus
from app.graph import run_pipeline
from app.agents.planner import run_planner
from app.agents.architect import run_architect
from app.agents.coder import run_coder

router = APIRouter()

# ── Redis session store ───────────────────────────────────
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)
SESSION_TTL = 60 * 60 * 24  # 24 hours


def save_session(session_id: str, data: dict):
    try:
        redis_client.setex(session_id, SESSION_TTL, json.dumps(data))
    except Exception as e:
        print(f"Redis save error: {e}")


def load_session(session_id: str) -> dict | None:
    try:
        raw = redis_client.get(session_id)
        return json.loads(raw) if raw else None
    except Exception as e:
        print(f"Redis load error: {e}")
        return None


def serialize_session(planner_output, architect_output, coder_output, prompt, settings, chat_history):
    return {
        "planner_output":   planner_output.model_dump()   if planner_output   else None,
        "architect_output": architect_output.model_dump() if architect_output else None,
        "coder_output":     coder_output.model_dump()     if coder_output     else None,
        "original_prompt":  prompt,
        "settings":         settings,
        "chat_history":     chat_history,
    }


# ── REST endpoint ─────────────────────────────────────────
@router.post("/generate")
async def generate(request: GenerateRequest):
    session_id = request.session_id or str(uuid.uuid4())
    try:
        result = run_pipeline(
            user_prompt = request.prompt,
            settings    = request.settings or {},
            session_id  = session_id,
        )
        save_session(session_id, {
            "original_prompt": request.prompt,
            "chat_history":    [],
        })
        return {"session_id": session_id, "result": result.model_dump()}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


# ── WebSocket endpoint ────────────────────────────────────
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

        # ── Save to Redis & send done ─────────────────────
        save_session(session_id, serialize_session(
            planner_output, architect_output, coder_output,
            prompt, settings, []
        ))
        await websocket.send_json({"type": "done", "session_id": session_id})

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})


# ── Chat refinement ───────────────────────────────────────
@router.post("/chat")
async def chat(request: ChatRequest):
    session = load_session(request.session_id)
    if not session:
        print(f"Session {request.session_id} not found in Redis")
        return JSONResponse(status_code=404, content={"error": "Session not found. Please regenerate first."})

    chat_history = session.get("chat_history", [])
    chat_history.append({"role": "user", "message": request.message})

    try:
        from app.schemas.models import ArchitectOutput
        architect_data = session.get("architect_output")
        if not architect_data:
            return JSONResponse(status_code=400, content={"error": "No architect output in session"})

        architect_output = ArchitectOutput(**architect_data)
        settings = session.get("settings", {})
        settings["extra_instruction"] = request.message

        new_coder_output = run_coder(
            architect_output = architect_output,
            settings         = settings,
        )

        chat_history.append({
            "role": "assistant", "message": "Code updated based on your request."
        })

        # Update session in Redis
        session["coder_output"]  = new_coder_output.model_dump()
        session["chat_history"]  = chat_history
        session["settings"]      = settings
        save_session(request.session_id, session)

        return {
            "session_id":   request.session_id,
            "coder_output": new_coder_output.model_dump(),
            "chat_history": chat_history,
        }
    except Exception as e:
        print(f"Chat error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


# ── Export session ────────────────────────────────────────
@router.get("/export/{session_id}")
async def export_session(session_id: str):
    session = load_session(session_id)
    if not session:
        return JSONResponse(status_code=404, content={"error": "Session not found"})
    return {
        "session_id":       session_id,
        "original_prompt":  session.get("original_prompt"),
        "planner_output":   session.get("planner_output"),
        "architect_output": session.get("architect_output"),
        "coder_output":     session.get("coder_output"),
        "chat_history":     session.get("chat_history", []),
    }