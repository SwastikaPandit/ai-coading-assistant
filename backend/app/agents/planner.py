import json
import re
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.schemas.models import PlannerOutput
from app.prompts.templates import PLANNER_SYSTEM_PROMPT


def clean_json(text: str) -> str:
    """Strip markdown fences if the model wraps output in ```json ... ```"""
    text = text.strip()
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"^```\s*",     "", text)
    text = re.sub(r"\s*```$",     "", text)
    return text.strip()


def run_planner(user_prompt: str, settings: dict = {}) -> PlannerOutput:
    llm = ChatOpenAI(
        model       = settings.get("model", "gpt-4o"),
        temperature = settings.get("temperature", 0.3),
        api_key     = settings.get("api_key"),
    )

    messages = [
        SystemMessage(content=PLANNER_SYSTEM_PROMPT),
        HumanMessage(content=f"User request: {user_prompt}"),
    ]

    response = llm.invoke(messages)
    raw      = clean_json(response.content)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Planner returned invalid JSON: {e}\n\nRaw output:\n{raw}")

    return PlannerOutput(**data)