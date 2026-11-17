from __future__ import annotations

import os

try:
    from groq import Groq
except ImportError:
    Groq = None  # type: ignore[assignment]


class GroqEquipmentHost:
    """Example real host model, not called by the local MCP tests."""

    def __init__(self, api_key: str | None = None) -> None:
        key = api_key or os.getenv("GROQ_API_KEY")
        if not key:
            raise ValueError("GROQ_API_KEY is required to call Groq.")
        if Groq is None:
            raise ImportError("Install groq before running the application.")
        self.client = Groq(api_key=key)

    def answer(self, user_text: str, tool_result: str) -> str:
        response = self.client.chat.completions.create(
            model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
            messages=[
                {"role": "user", "content": user_text},
                {"role": "system", "content": f"Local MCP result: {tool_result}"},
            ],
        )
        return response.choices[0].message.content or ""
