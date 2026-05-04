import time
import uuid
from typing import Any, Callable, Optional
from langgraph.graph import StateGraph, END
from app.schemas.models import PipelineState, AgentStatus
from app.agents.planner import run_planner
from app.agents.architect import run_architect
from app.agents.coder import run_coder


# ── Node functions ───────────────────────────────────────

def planner_node(state: dict) -> dict:
    try:
        result = run_planner(
            user_prompt = state["user_prompt"],
            settings    = state.get("settings", {}),
        )
        return {
            **state,
            "planner_output": result,
            "status": AgentStatus.RUNNING,
        }
    except Exception as e:
        return {**state, "status": AgentStatus.FAILED, "error": str(e)}


def architect_node(state: dict) -> dict:
    if state.get("status") == AgentStatus.FAILED:
        return state
    try:
        result = run_architect(
            planner_output = state["planner_output"],
            settings       = state.get("settings", {}),
        )
        return {
            **state,
            "architect_output": result,
        }
    except Exception as e:
        return {**state, "status": AgentStatus.FAILED, "error": str(e)}


def coder_node(state: dict) -> dict:
    if state.get("status") == AgentStatus.FAILED:
        return state
    try:
        result = run_coder(
            architect_output = state["architect_output"],
            settings         = state.get("settings", {}),
        )
        return {
            **state,
            "coder_output": result,
            "status": AgentStatus.COMPLETED,
        }
    except Exception as e:
        return {**state, "status": AgentStatus.FAILED, "error": str(e)}


# ── Build the graph ──────────────────────────────────────

def build_graph():
    graph = StateGraph(dict)

    # Register nodes
    graph.add_node("planner",   planner_node)
    graph.add_node("architect", architect_node)
    graph.add_node("coder",     coder_node)

    # Define edges  Planner → Architect → Coder → END
    graph.set_entry_point("planner")
    graph.add_edge("planner",   "architect")
    graph.add_edge("architect", "coder")
    graph.add_edge("coder",     END)

    return graph.compile()


# ── Run the full pipeline ────────────────────────────────

def run_pipeline(
    user_prompt: str,
    settings:    dict = {},
    session_id:  Optional[str] = None,
    on_update:   Optional[Callable[[str, Any], None]] = None,
) -> PipelineState:

    session_id = session_id or str(uuid.uuid4())
    start_time = time.time()

    initial_state = {
        "session_id":       session_id,
        "user_prompt":      user_prompt,
        "settings":         settings,
        "planner_output":   None,
        "architect_output": None,
        "coder_output":     None,
        "status":           AgentStatus.PENDING,
        "error":            None,
        "generation_time":  None,
    }

    if on_update:
        on_update("planner", {"status": "running"})

    app = build_graph()
    final_state = app.invoke(initial_state)

    # Notify after each agent if callback provided
    if on_update:
        if final_state.get("planner_output"):
            on_update("planner", {"status": "completed"})
            on_update("architect", {"status": "running"})
        if final_state.get("architect_output"):
            on_update("architect", {"status": "completed"})
            on_update("coder", {"status": "running"})
        if final_state.get("coder_output"):
            on_update("coder", {"status": "completed"})

    final_state["generation_time"] = round(time.time() - start_time, 2)

    return PipelineState(**{
        k: v for k, v in final_state.items()
        if k in PipelineState.model_fields
    })