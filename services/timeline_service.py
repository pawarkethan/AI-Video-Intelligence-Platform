from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config.settings import OCR_DIR, OUTPUT_DIR, TRANSCRIPT_DIR


class TimelineService:
    """Persist and search the time-aligned OCR and transcript timeline."""

    def __init__(self, output_directory: str | Path | None = None) -> None:
        self.output_directory = Path(output_directory or OUTPUT_DIR) / "timelines"
        self.output_directory.mkdir(parents=True, exist_ok=True)

    def save(
        self,
        video_id: str,
        ocr_results: list[dict[str, Any]],
        transcript_segments: list[dict[str, Any]],
    ) -> Path:
        """Save a structured, time-aligned JSON document for one video."""

        timeline = {
            "video_id": video_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "ocr_results": self._normalize_ocr_results(ocr_results),
            "transcript_segments": self._normalize_transcript_segments(
                transcript_segments
            ),
        }

        timeline_path = self.get_timeline_path(video_id)
        temporary_path = timeline_path.with_suffix(".tmp")
        temporary_path.write_text(
            json.dumps(timeline, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary_path.replace(timeline_path)

        return timeline_path

    def save_ocr(
        self,
        video_id: str,
        ocr_results: list[dict[str, Any]],
    ) -> Path:
        """Persist OCR independently so it survives Streamlit reruns."""

        results = self._normalize_ocr_results(ocr_results)
        payload = {
            "video_id": video_id,
            "frames_analyzed": len(results),
            "frames_with_text": sum(1 for result in results if result["text"]),
            "total_detections": sum(
                len(result["detections"]) for result in results
            ),
            "results": results,
        }

        return self._write_json(
            OCR_DIR / f"{video_id}_ocr.json",
            payload,
        )

    def save_transcript(
        self,
        video_id: str,
        language: str,
        segments: list[dict[str, Any]],
        text: str = "",
    ) -> Path:
        """Persist timestamped ASR output independently of the UI session."""

        payload = {
            "video_id": video_id,
            "language": language,
            "text": text,
            "segments": self._normalize_transcript_segments(segments),
        }

        return self._write_json(
            TRANSCRIPT_DIR / f"{video_id}.json",
            payload,
        )

    def load(self, video_id: str) -> dict[str, Any]:
        """Load a saved timeline, returning empty collections if none exists."""

        timeline_path = self.get_timeline_path(video_id)

        if not timeline_path.exists():
            return {
                "video_id": video_id,
                "ocr_results": [],
                "transcript_segments": [],
            }

        with timeline_path.open(encoding="utf-8") as file:
            return json.load(file)

    def search_by_time(
        self,
        video_id: str,
        timestamp_seconds: float,
        window_seconds: float = 5.0,
    ) -> dict[str, Any]:
        """Return OCR frames and transcript speech close to a video timestamp."""

        timestamp_seconds = float(timestamp_seconds)
        window_seconds = max(0.0, float(window_seconds))
        start = max(0.0, timestamp_seconds - window_seconds)
        end = timestamp_seconds + window_seconds
        timeline = self.load(video_id)

        ocr_results = [
            result
            for result in timeline.get("ocr_results", [])
            if start <= float(result.get("timestamp_seconds", 0)) <= end
        ]

        transcript_segments = [
            segment
            for segment in timeline.get("transcript_segments", [])
            if float(segment.get("end", 0)) >= start
            and float(segment.get("start", 0)) <= end
        ]

        return {
            "timestamp_seconds": timestamp_seconds,
            "window_seconds": window_seconds,
            "ocr_results": ocr_results,
            "transcript_segments": transcript_segments,
        }

    def get_timeline_path(self, video_id: str) -> Path:
        """Return the deterministic JSON path for a video timeline."""

        return self.output_directory / f"{video_id}_timeline.json"

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any]) -> Path:
        """Atomically write a UTF-8 JSON payload, creating its directory."""

        path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = path.with_suffix(".tmp")
        temporary_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary_path.replace(path)
        return path

    @staticmethod
    def _normalize_ocr_results(
        ocr_results: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        normalized_results: list[dict[str, Any]] = []

        for result in ocr_results:
            detections = result.get("texts", result.get("detections", []))
            detections = detections if isinstance(detections, list) else []
            text = "\n".join(
                str(item.get("text", "")).strip()
                for item in detections
                if isinstance(item, dict) and item.get("text")
            )

            normalized_results.append(
                {
                    "frame_number": int(result.get("frame_number", 0)),
                    "timestamp_seconds": float(
                        result.get("timestamp_seconds", 0)
                    ),
                    "timestamp": str(result.get("timestamp", "00:00:00")),
                    "frame_path": str(result.get("frame_path", "")),
                    "text": text,
                    "detections": detections,
                }
            )

        return normalized_results

    @staticmethod
    def _normalize_transcript_segments(
        segments: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        return [
            {
                "start": float(segment.get("start", 0)),
                "end": float(segment.get("end", 0)),
                "text": str(segment.get("text", "")).strip(),
            }
            for segment in segments
            if isinstance(segment, dict) and segment.get("text")
        ]
