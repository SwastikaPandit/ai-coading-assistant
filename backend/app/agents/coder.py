import json
import re
from langchain_openai import ChatOpenAI

from langchain_core.messages import SystemMessage, HumanMessage
from app.schemas.models import ArchitectOutput, CoderOutput
from app.prompts.templates import CODER_SYSTEM_PROMPT


def clean_json(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"^```\s*",     "", text)
    text = re.sub(r"\s*```$",     "", text)
    return text.strip()


def run_coder(architect_output: ArchitectOutput, settings: dict = {}) -> CoderOutput:
    llm = ChatOpenAI(
        model       = settings.get("model", "gpt-4o"),
        temperature = settings.get("temperature", 0.1),
        api_key     = settings.get("api_key"),
    )

    architect_json = architect_output.model_dump_json(indent=2)

    # Build the user message — include extra instruction if present
    extra = settings.get("extra_instruction", "")
    user_message = f"Architect output:\n{architect_json}"
    if extra:
        user_message += f"\n\nIMPORTANT MODIFICATION REQUEST: {extra}\nMake sure ALL files reflect this change completely."

    messages = [
        SystemMessage(content=CODER_SYSTEM_PROMPT),
        HumanMessage(content=user_message),
    ]

    response = llm.invoke(messages)
    raw      = clean_json(response.content)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Coder returned invalid JSON: {e}\n\nRaw output:\n{raw}")

    return CoderOutput(**data)