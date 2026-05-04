import json
import re
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.schemas.models import PlannerOutput, ArchitectOutput
from app.prompts.templates import ARCHITECT_SYSTEM_PROMPT


def clean_json(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"^```\s*",     "", text)
    text = re.sub(r"\s*```$",     "", text)
    return text.strip()


def run_architect(planner_output: PlannerOutput, settings: dict = {}) -> ArchitectOutput:
    llm = ChatOpenAI(
        model       = settings.get("model", "gpt-4o"),
        temperature = settings.get("temperature", 0.2),
        api_key     = settings.get("api_key"),
    )

    planner_json = planner_output.model_dump_json(indent=2)

    messages = [
        SystemMessage(content=ARCHITECT_SYSTEM_PROMPT),
        HumanMessage(content=f"Planner output:\n{planner_json}"),
    ]

    response = llm.invoke(messages)
    raw      = clean_json(response.content)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Architect returned invalid JSON: {e}\n\nRaw output:\n{raw}")

    return ArchitectOutput(**data)