from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from services.ocr_service import OCRService


class VideoOCRService:
    """Run OCR on extracted video frames and preserve video timing metadata."""

    _FRAME_NAME_PATTERN = re.compile(
        r"^frame_(?P<frame_number>\d+)_(?P<timestamp>\d+(?:\.\d+)?)s$",
        re.IGNORECASE,
    )

    def __init__(
        self,
        language: str = "en",
        confidence_threshold: float = 0.50,
    ) -> None:
        self.ocr_service = OCRService(
            language=language,
            confidence_threshold=confidence_threshold,
        )

    def process_frames(
        self,
        frame_paths: list[str | Path],
    ) -> list[dict[str, Any]]:
        """
        Return OCR results for each extracted frame.

        Each result includes ``frame_number``, ``timestamp_seconds``, a
        human-readable ``timestamp``, and individual text detections with
        their confidence scores and bounding boxes.
        """

        results: list[dict[str, Any]] = []

        for fallback_index, frame_path in enumerate(frame_paths):
            path = Path(frame_path)
            frame_number, timestamp_seconds = self._get_frame_metadata(
                path,
                fallback_index,
            )

            frame_result: dict[str, Any] = {
                "frame_number": frame_number,
                "timestamp_seconds": timestamp_seconds,
                "timestamp": self.format_timestamp(timestamp_seconds),
                "frame_path": str(path),
                "texts": [],
            }

            try:
                frame_result["texts"] = self.ocr_service.extract_text(path)
            except Exception as error:
                frame_result["error"] = str(error)

            results.append(frame_result)

        return results

    @classmethod
    def _get_frame_metadata(
        cls,
        frame_path: Path,
        fallback_index: int,
    ) -> tuple[int, float]:
        """Read frame index and timestamp from VideoService frame filenames."""

        match = cls._FRAME_NAME_PATTERN.match(frame_path.stem)

        if match is None:
            return fallback_index, float(fallback_index)

        return (
            int(match.group("frame_number")),
            float(match.group("timestamp")),
        )

    @staticmethod
    def format_timestamp(seconds: float) -> str:
        """Format seconds as HH:MM:SS for OCR result displays."""

        total_seconds = max(0, int(seconds))
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

