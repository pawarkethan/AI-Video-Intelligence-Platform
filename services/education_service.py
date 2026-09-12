from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import streamlit as st
from google import genai

from config.settings import OUTPUT_DIR


class EducationService:
    """Create study notes, flashcards, and assessment questions from a video."""

    def __init__(self, api_key: str | None = None) -> None:
        api_key = api_key or st.secrets.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured in Streamlit secrets.")
        self.client = genai.Client(api_key=api_key)

    def generate(self, video_id: str, insights: dict[str, Any], transcript: str, count: int, difficulty: str) -> dict[str, Any]:
        prompt = f"""Create educational materials from the grounded video evidence below.
Make exactly {count} quiz questions at {difficulty} difficulty. Do not invent facts.
Keep every field concise. Create 3-5 lecture-note sections with at most 4 short
points each, and {count} flashcards. Each quiz question must have exactly four
options, with its answer matching one option exactly.
SUMMARY: {json.dumps(insights, ensure_ascii=False)}
TRANSCRIPT: {transcript[:40000]}"""
        # Generate Content supports JSON MIME responses directly. This avoids
        # the Interactions API's responseFormat validation error.
        result = self._generate_valid_pack(prompt)
        path = OUTPUT_DIR / video_id / "education.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        return result

    def _generate_valid_pack(self, prompt: str) -> dict[str, Any]:
        """Request a complete JSON pack, retrying temporary and malformed replies."""
        attempts = 3
        last_error: Exception | None = None

        for attempt in range(attempts):
            try:
                response = self.client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=prompt,
                    config={
                        "response_mime_type": "application/json",
                        "response_json_schema": self._response_schema(),
                        "max_output_tokens": 8192,
                    },
                )
                result = self._parse_response(response)
                self._validate_pack(result)
                return result
            except Exception as error:
                last_error = error
                if not self._is_retryable(error) or attempt == attempts - 1:
                    break
                time.sleep(2 ** attempt)

        if self._is_temporary_model_error(last_error):
            raise RuntimeError(
                "The AI service is temporarily busy. Please try creating the learning pack again shortly."
            ) from last_error
        raise RuntimeError(
            "The AI returned an incomplete learning pack after retrying. Please try again."
        ) from last_error

    @staticmethod
    def _parse_response(response: Any) -> dict[str, Any]:
        """Prefer the SDK's parsed JSON, with text parsing as a compatibility fallback."""
        parsed = getattr(response, "parsed", None)
        if isinstance(parsed, dict):
            return parsed

        text = getattr(response, "text", "") or ""
        if not text.strip():
            raise ValueError("Gemini returned an empty education response.")
        result = json.loads(EducationService._strip_fence(text))
        if not isinstance(result, dict):
            raise ValueError("Gemini returned an unexpected education format.")
        return result

    @staticmethod
    def _validate_pack(result: dict[str, Any]) -> None:
        required_sections = ("lecture_notes", "flashcards", "quiz")
        if any(not isinstance(result.get(section), list) for section in required_sections):
            raise ValueError("Gemini returned an incomplete education format.")

    @staticmethod
    def _is_temporary_model_error(error: Exception | None) -> bool:
        message = str(error).upper()
        return any(marker in message for marker in ("503", "UNAVAILABLE", "RESOURCE_EXHAUSTED", "429", "TIMEOUT"))

    @classmethod
    def _is_retryable(cls, error: Exception) -> bool:
        return cls._is_temporary_model_error(error) or isinstance(
            error, (ValueError, json.JSONDecodeError)
        )

    @staticmethod
    def load(video_id: str) -> dict[str, Any] | None:
        path = OUTPUT_DIR / video_id / "education.json"
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    @staticmethod
    def _strip_fence(text: str) -> str:
        text = text.strip()
        return text.split("\n", 1)[-1].rsplit("```", 1)[0].strip() if text.startswith("```") else text

    @staticmethod
    def _response_schema() -> dict[str, Any]:
        """Define the JSON structure required for a complete learning pack."""
        string_list = {"type": "array", "items": {"type": "string"}}
        return {
            "type": "object",
            "properties": {
                "lecture_notes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "heading": {"type": "string"},
                            "points": string_list,
                        },
                        "required": ["heading", "points"],
                    },
                },
                "flashcards": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "front": {"type": "string"},
                            "back": {"type": "string"},
                        },
                        "required": ["front", "back"],
                    },
                },
                "quiz": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "question": {"type": "string"},
                            "options": {
                                "type": "array",
                                "items": {"type": "string"},
                                "minItems": 4,
                                "maxItems": 4,
                            },
                            "answer": {"type": "string"},
                            "explanation": {"type": "string"},
                        },
                        "required": ["question", "options", "answer", "explanation"],
                    },
                },
            },
            "required": ["lecture_notes", "flashcards", "quiz"],
        }
