from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum

# ── Status ──────────────────────────────────────────────
class AgentStatus(str, Enum):
    PENDING   = "pending"
    RUNNING   = "running"
    COMPLETED = "completed"
    FAILED    = "failed"

# ── Planner Output ───────────────────────────────────────
class Fileplan(BaseModel):
    filename: str = Field(..., description="e.g. src/App.tsx")
    purpose:  str = Field(..., description="What this file does")

class PlannerOutput(BaseModel):
    project_name: str
    description:  str
    tech_stack:   List[str]
    features:     List[str]
    files:        List[Fileplan]

# ── Architect Output ─────────────────────────────────────
class FileSchema(BaseModel):
    filename:    str
    description: str
    exports:     List[str] = Field(default_factory=list, description="Functions/classes exported")
    imports:     List[str] = Field(default_factory=list, description="Dependencies it needs")
    interfaces:  Optional[str] = None  # Type definitions / data shapes

class ArchitectOutput(BaseModel):
    project_name:    str
    directory_tree:  str   # ASCII tree as a string
    files:           List[FileSchema]
    shared_types:    Optional[str] = None  # Global type definitions

# ── Coder Output ─────────────────────────────────────────
class GeneratedFile(BaseModel):
    filename: str
    language: str   # e.g. "python", "typescript", "json"
    content:  str   # The actual code

class CoderOutput(BaseModel):
    project_name: str
    files:        List[GeneratedFile]

# ── Pipeline State (shared across all agents) ────────────
class PipelineState(BaseModel):
    session_id:       str
    user_prompt:      str
    planner_output:   Optional[PlannerOutput]  = None
    architect_output: Optional[ArchitectOutput] = None
    coder_output:     Optional[CoderOutput]     = None
    status:           AgentStatus               = AgentStatus.PENDING
    error:            Optional[str]             = None
    generation_time:  Optional[float]           = None

# ── API Request/Response ──────────────────────────────────
class GenerateRequest(BaseModel):
    prompt:     str
    session_id: Optional[str] = None
    settings:   Optional[Dict] = None   # model, temperature, etc.

class ChatRequest(BaseModel):
    session_id: str
    message:    str