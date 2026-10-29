import json
import os
from dataclasses import dataclass


@dataclass
class ToolCall:
    id: str | None
    name: str
    args: dict


class AgentBackend:
    def chat(
        self, messages: list[dict[str, str]], tools: dict[str, callable]
    ) -> tuple[dict[str, str], str, list[ToolCall]]:
        pass

    def tool_message(
        self, call: ToolCall, result: dict[str, str] | str
    ) -> dict[str, str]:
        pass


class OllamaBackend(AgentBackend):
    """Local Ollama."""

    def __init__(self, model_name: str):
        from ollama import chat

        self._chat = chat
        self._model_name = model_name

    def chat(self, messages, tools):
        response = self._chat(
            model=self._model_name, messages=messages, tools=list(tools.values())
        )
        message = response.message
        calls = [
            ToolCall(None, c.function.name, dict(c.function.arguments))
            for c in message.tool_calls or []
        ]
        return message, message.content or "", calls

    def tool_message(self, call, result):
        return {"role": "tool", "tool_name": call.name, "content": json.dumps(result)}


class OpenAIBackend(AgentBackend):
    """Any OpenAI-compatible API."""

    def __init__(self, model_name: str, base_url: str, api_key: str):
        from ollama._utils import convert_function_to_tool
        from openai import OpenAI

        if not base_url or not api_key:
            raise RuntimeError(
                "LLM_PROVIDER=openai requires LLM_BASE_URL and LLM_API_KEY"
            )
        self._client = OpenAI(base_url=base_url, api_key=api_key)
        self._to_schema = convert_function_to_tool
        self._model_name = model_name

    def chat(self, messages, tools):
        schemas = [
            self._to_schema(fn).model_dump(exclude_none=True) for fn in tools.values()
        ]
        response = self._client.chat.completions.create(
            model=self._model_name, messages=messages, tools=schemas
        )
        message = response.choices[0].message
        calls = [
            ToolCall(c.id, c.function.name, json.loads(c.function.arguments or "{}"))
            for c in message.tool_calls or []
        ]

        assistant_msg = {"role": "assistant", "content": message.content or ""}
        if message.tool_calls:
            assistant_msg["tool_calls"] = [
                {
                    "id": c.id,
                    "type": "function",
                    "function": {
                        "name": c.function.name,
                        "arguments": c.function.arguments,
                    },
                }
                for c in message.tool_calls
            ]
        return assistant_msg, message.content or "", calls

    def tool_message(self, call, result):
        return {
            "role": "tool",
            "tool_call_id": call.id,
            "content": json.dumps(result),
        }


def get_backend(llm_provider: str, model_name: str) -> AgentBackend:
    if llm_provider == "ollama":
        return OllamaBackend(model_name)
    if llm_provider == "openai":
        base_url = os.getenv("LLM_BASE_URL")
        api_key = os.getenv("LLM_API_KEY")
        return OpenAIBackend(model_name, base_url, api_key)
    raise RuntimeError(
        f"Unknown LLM_PROVIDER: {llm_provider!r} (use 'ollama' or 'openai')"
    )
