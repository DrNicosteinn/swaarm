import json
from openai import OpenAI
from app.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL_NAME
from app.utils.logger import get_logger

logger = get_logger(__name__)

_client = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
    return _client


def chat(
    messages: list[dict],
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    response_format: str | None = None,
) -> str:
    client = get_client()
    kwargs = {
        "model": model or LLM_MODEL_NAME,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format == "json":
        kwargs["response_format"] = {"type": "json_object"}

    response = client.chat.completions.create(**kwargs)
    content = response.choices[0].message.content
    logger.info(
        f"LLM call: {response.usage.prompt_tokens} in / {response.usage.completion_tokens} out"
    )
    return content


def chat_json(
    messages: list[dict],
    model: str | None = None,
    temperature: float = 0.5,
) -> dict:
    raw = chat(messages, model=model, temperature=temperature, response_format="json")
    # Strip markdown code blocks if present
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    return json.loads(text)
