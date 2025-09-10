from __future__ import annotations

from typing import Optional

from ..config import GEMINI_API_KEY, DEFAULT_TEMPERATURE, THINKING_BUDGET


class GeminiClient:
    def __init__(self):
        try:
            from google import genai  # type: ignore

            self._client = genai.Client(api_key=GEMINI_API_KEY)
            self._model = "gemini-2.5-flash"
            self._ok = True
        except Exception:
            self._client = None
            self._model = None
            self._ok = False

    def text(self, user_text: str, system_text: Optional[str] = None) -> str:
        if not self._ok:
            return "[flavor unavailable]"

        try:
            from google.genai import types  # type: ignore

            contents = [types.Content(role="user", parts=[types.Part.from_text(text=user_text)])]
            cfg = types.GenerateContentConfig(
                temperature=DEFAULT_TEMPERATURE,
                thinking_config=types.ThinkingConfig(thinking_budget=THINKING_BUDGET),
                system_instruction=[types.Part.from_text(text=system_text or "")],
            )
            out: list[str] = []
            for chunk in self._client.models.generate_content_stream(
                model=self._model,
                contents=contents,
                config=cfg,
            ):
                if getattr(chunk, "text", None):
                    out.append(chunk.text)
            return "".join(out).strip() or "[flavor unavailable]"
        except Exception:
            return "[flavor unavailable]"

