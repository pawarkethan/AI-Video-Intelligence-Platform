from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import streamlit as st
from google import genai

from config.settings import OUTPUT_DIR
from services.analysis_service import AnalysisService


class VideoInsightsService:
    """Generate and persist structured, evidence-grounded video insights."""

    def __init__(self, api_key: str | None = None) -> None:
        api_key = api_key or st.secrets.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured in Streamlit secrets.")
        self.client = genai.Client(api_key=api_key)
        self.output_directory = OUTPUT_DIR / "insights"
        self.output_directory.mkdir(parents=True, exist_ok=True)

    def get_path(self, video_id: str) -> Path:
        return self.output_directory / f"{video_id}_insights.json"

    def load(self, video_id: str) -> dict[str, Any] | None:
        path = self.get_path(video_id)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def generate(
        self,
        video_id: str,
        transcript: Any = None,
        ocr_results: Any = None,
        video_metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        transcript_text = self._format_transcript(transcript)
        ocr_text = self._format_ocr(ocr_results)

        if not transcript_text and not ocr_text:
            raise ValueError("Generate a transcript or OCR results before creating insights.")

        prompt = f"""
You are a precise video-intelligence analyst. Use only the evidence below.
Do not invent names, events, dates, or timestamps. Return valid JSON only, with
no Markdown fences and exactly this structure:
{{
  "short_summary": "one sentence overview",
  "detailed_summary": "2-4 sentence overview",
  "key_points": ["point"],
  "topics": ["topic"],
  "keywords": ["keyword"],
  "important_concepts": ["concept"],
  "action_items": ["action item"],
  "important_moments": [
    {{"timestamp_seconds": 0, "title": "short title", "description": "why it matters"}}
  ]
}}

Rules:
- Include 3-6 key_points, 3-8 topics and keywords when evidence permits.
- Include action_items only when explicitly supported; otherwise use an empty list.
- Include 3-6 important_moments only when timestamps are present in the transcript
  or OCR; timestamps must be grounded in the evidence.
- Prefer concise, professional language.

VIDEO METADATA:
{json.dumps(video_metadata or {}, ensure_ascii=False)}

TRANSCRIPT:
{self._truncate(transcript_text)}

ON-SCREEN TEXT:
{self._truncate(ocr_text)}
"""

        # Use the stable Generate Content endpoint for structured JSON. The
        # Interactions endpoint currently rejects JSON MIME responses in this
        # SDK/server combination unless it receives a different format shape.
        response = self._generate_with_retry(prompt)
        output_text = getattr(response, "text", "") or ""
        if not output_text:
            raise RuntimeError("Gemini returned an empty insights response.")

        try:
            insights = json.loads(self._strip_json_fence(output_text))
        except json.JSONDecodeError as error:
            raise RuntimeError("Gemini returned invalid structured insights.") from error

        insights = self._normalize(insights)
        insights.update(
            {
                "video_id": video_id,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "sources": {
                    "transcript_available": bool(transcript_text),
                    "ocr_available": bool(ocr_text),
                },
            }
        )
        self._save(video_id, insights)
        AnalysisService().update(video_id, insights=insights)
        AnalysisService().save_component(video_id, "summary", insights)
        return insights

    def _generate_with_retry(self, prompt: str) -> Any:
        """Retry temporary Gemini capacity failures before surfacing an error."""
        attempts = 3
        for attempt in range(attempts):
            try:
                return self.client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=prompt,
                    config={
                        "response_mime_type": "application/json",
                        "response_json_schema": self._response_schema(),
                        "max_output_tokens": 2400,
                    },
                )
            except Exception as error:
                if not self._is_temporary_model_error(error) or attempt == attempts - 1:
                    raise
                time.sleep(2 ** attempt)

        raise RuntimeError("Unable to generate insights after retrying.")

    @staticmethod
    def _is_temporary_model_error(error: Exception) -> bool:
        """Return whether an API failure is normally resolved by retrying."""
        message = str(error).upper()
        return any(marker in message for marker in ("503", "UNAVAILABLE", "RESOURCE_EXHAUSTED", "429", "TIMEOUT"))

    def _save(self, video_id: str, insights: dict[str, Any]) -> None:
        path = self.get_path(video_id)
        temporary_path = path.with_suffix(".tmp")
        temporary_path.write_text(
            json.dumps(insights, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        temporary_path.replace(path)

    @staticmethod
    def _truncate(text: str, limit: int = 45_000) -> str:
        return text[:limit]

    @staticmethod
    def _response_schema() -> dict[str, Any]:
        """Return the JSON schema expected from the insights interaction."""
        string_list = {"type": "array", "items": {"type": "string"}}
        return {
            "type": "object",
            "properties": {
                "short_summary": {"type": "string"},
                "detailed_summary": {"type": "string"},
                "key_points": string_list,
                "topics": string_list,
                "keywords": string_list,
                "important_concepts": string_list,
                "action_items": string_list,
                "important_moments": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "timestamp_seconds": {"type": "number"},
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                        },
                        "required": ["timestamp_seconds", "title", "description"],
                    },
                },
            },
            "required": [
                "short_summary", "detailed_summary", "key_points", "topics",
                "keywords", "important_concepts", "action_items", "important_moments",
            ],
        }

    @staticmethod
    def _strip_json_fence(text: str) -> str:
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1]
            text = text.rsplit("```", 1)[0]
        return text.strip()

    @staticmethod
    def _format_transcript(transcript: Any) -> str:
        if isinstance(transcript, dict):
            transcript = transcript.get("segments", transcript.get("text", ""))
        if isinstance(transcript, str):
            return transcript.strip()
        if not isinstance(transcript, list):
            return ""
        return "\n".join(
            f"[{float(item.get('start', 0)):.1f}s - {float(item.get('end', 0)):.1f}s] "
            f"{str(item.get('text', '')).strip()}"
            for item in transcript
            if isinstance(item, dict) and item.get("text")
        )

    @staticmethod
    def _format_ocr(ocr_results: Any) -> str:
        if isinstance(ocr_results, dict):
            ocr_results = ocr_results.get("results", ocr_results.get("frames", []))
        if not isinstance(ocr_results, list):
            return ""
        lines = []
        for item in ocr_results:
            if not isinstance(item, dict):
                continue
            text = item.get("text", "")
            if not text:
                detections = item.get("texts", item.get("detections", []))
                text = " ".join(
                    str(detection.get("text", "")).strip()
                    for detection in detections
                    if isinstance(detection, dict) and detection.get("text")
                )
            if text:
                timestamp = item.get("timestamp_seconds", item.get("timestamp", 0))
                lines.append(f"[{timestamp}] {str(text).strip()}")
        return "\n".join(lines)

    @staticmethod
    def _normalize(insights: Any) -> dict[str, Any]:
        if not isinstance(insights, dict):
            raise RuntimeError("Gemini returned an unexpected insights format.")

        def string_list(key: str) -> list[str]:
            values = insights.get(key, [])
            return [str(value).strip() for value in values if str(value).strip()] if isinstance(values, list) else []

        moments = []
        for moment in insights.get("important_moments", []):
            if not isinstance(moment, dict):
                continue
            try:
                timestamp = max(0.0, float(moment.get("timestamp_seconds", 0)))
            except (TypeError, ValueError):
                continue
            moments.append({
                "timestamp_seconds": timestamp,
                "title": str(moment.get("title", "Important moment")).strip(),
                "description": str(moment.get("description", "")).strip(),
            })

        return {
            "short_summary": str(
                insights.get("short_summary", insights.get("summary", ""))
            ).strip(),
            "detailed_summary": str(
                insights.get("detailed_summary", insights.get("summary", ""))
            ).strip(),
            "key_points": string_list("key_points"),
            "topics": string_list("topics"),
            "keywords": string_list("keywords"),
            "important_concepts": string_list("important_concepts"),
            "action_items": string_list("action_items"),
            "important_moments": sorted(moments, key=lambda item: item["timestamp_seconds"]),
        }
