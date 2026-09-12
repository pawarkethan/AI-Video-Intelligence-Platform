from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st
from google import genai

from config.settings import OUTPUT_DIR


class VideoQAService:
    """
    Generates answers about a video using the available
    transcript and OCR context.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-3.6-flash",
    ):
        self.model = model

        api_key = api_key or st.secrets.get("GEMINI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured in "
                ".streamlit/secrets.toml"
            )

        self.client = genai.Client(
            api_key=api_key
        )

        print("=" * 60)
        print("Initializing Video Q&A")
        print("=" * 60)
        print(f"Model: {self.model}")
        print("=" * 60)

    @staticmethod
    def _context_to_text(data: Any) -> str:
        """Convert saved transcript or OCR data into prompt-ready text."""

        if isinstance(data, str):
            return data.strip()

        if isinstance(data, dict):
            if data.get("text"):
                return str(data["text"]).strip()

            data = data.get("segments", data.get("results", data.get("frames", [])))

        if isinstance(data, list):
            lines = []
            for item in data:
                if isinstance(item, dict):
                    text = str(item.get("text", "")).strip()
                    if not text:
                        continue
                    start = item.get("start", item.get("timestamp", item.get("time")))
                    prefix = f"[{start}] " if start is not None else ""
                    lines.append(prefix + text)
                elif item:
                    lines.append(str(item).strip())
            return "\n".join(lines)

        return "" if data is None else str(data).strip()

    def answer_question(
        self,
        question: str,
        transcript: str = "",
        ocr_text: str = "",
        insights: Optional[Dict[str, Any]] = None,
    ) -> str:

        if not question or not question.strip():
            return "Please enter a question about the video."

        transcript = transcript.strip()
        ocr_text = ocr_text.strip()

        if not transcript and not ocr_text:
            return (
                "I don't have enough video information yet. "
                "Please run Transcript and OCR analysis first."
            )

        context_parts = []

        if transcript:
            context_parts.append(
                "===== VIDEO TRANSCRIPT =====\n"
                + transcript
            )

        if ocr_text:
            context_parts.append(
                "===== ON-SCREEN OCR TEXT =====\n"
                + ocr_text
            )

        context = "\n\n".join(context_parts)

        insights_text = ""
        if insights:
            insights_text = (
                "===== SAVED VIDEO INSIGHTS =====\n"
                f"Summary: {insights.get('short_summary', insights.get('summary', ''))}\n"
                f"Key points: {'; '.join(insights.get('key_points', []))}\n"
                f"Important moments: {json.dumps(insights.get('important_moments', []), ensure_ascii=False)}"
            )

        prompt = f"""
You are the AI assistant for an AI Video Intelligence Platform.

Your job is to answer questions about the uploaded video.

Use ONLY the information provided in the video transcript
and OCR text below.

If the information is not available in the provided context,
clearly say that the video data does not contain enough
information to answer the question.

Do not invent facts.

When possible:
- Give a direct answer first.
- Mention relevant timestamps if they are available.
- Use the OCR information when the question is about
  text visible on screen.
- Use the transcript when the question is about what
  the speaker said.
- Combine transcript and OCR when necessary.
- Use the saved summary and key moments only as supporting context; the
  transcript and OCR remain the source of truth.
- End every answer with a new line beginning with "📍 Sources:" and list the
  most relevant timestamp or timestamp range from the evidence. If no timing
  evidence is available, write "📍 Sources: No timestamp available."

VIDEO DATA:

{context}

{insights_text}

USER QUESTION:

{question}

ANSWER:
"""

        try:

            interaction = self.client.interactions.create(
                model=self.model,
                input=prompt,
                generation_config={
                    "max_output_tokens": 1200,
                },
            )

            # The Interactions API exposes the assembled model response as
            # ``output_text``. It does not provide the legacy ``outputs``
            # attribute used by the Generate Content API.
            answer = getattr(interaction, "output_text", "") or ""

            if not answer:
                return "The AI returned an empty response."

            return answer.strip()

        except Exception as exc:

            return (
                "Failed to generate answer.\n\n"
                f"Error: {exc}"
            )

    def ask(
        self,
        question: str,
        transcript: Any = None,
        ocr_results: Any = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        video_id: Optional[str] = None,
    ) -> str:
        """Compatibility entry point used by the Ask Your Video page."""

        transcript_text = self._context_to_text(transcript)
        ocr_text = self._context_to_text(ocr_results)

        if conversation_history:
            history = "\n".join(
                f"{message.get('role', 'user').title()}: "
                f"{message.get('content', '')}"
                for message in conversation_history
            )
            if history:
                transcript_text = (
                    f"Previous conversation:\n{history}\n\n"
                    f"{transcript_text}"
                )

        return self.answer_question(
            question=question,
            transcript=transcript_text,
            ocr_text=ocr_text,
            insights=self._load_saved_insights(video_id),
        )

    @staticmethod
    def _load_saved_insights(video_id: Optional[str]) -> Dict[str, Any]:
        """Read a previously generated intelligence brief, if present."""

        if not video_id:
            return {}

        path = OUTPUT_DIR / "insights" / f"{video_id}_insights.json"
        try:
            payload = json.loads(Path(path).read_text(encoding="utf-8"))
            return payload if isinstance(payload, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}
