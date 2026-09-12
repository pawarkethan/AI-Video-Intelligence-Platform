from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import cv2


class VisionService:
    """Local, privacy-preserving person detection and scene-change analysis.

    OpenCV's built-in HOG detector is used, so no external model download is
    required. It detects people; a future object model can add more labels.
    """

    def __init__(self) -> None:
        self.detector = cv2.HOGDescriptor()
        self.detector.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

    def analyze_frames(self, frames: list[str]) -> dict[str, Any]:
        detections: list[dict[str, Any]] = []
        scenes: list[dict[str, Any]] = []
        previous_hist = None

        for frame_number, frame_path in enumerate(frames):
            image = cv2.imread(str(frame_path))
            if image is None:
                continue
            timestamp = self._timestamp(frame_path)
            boxes, weights = self.detector.detectMultiScale(
                image, winStride=(8, 8), padding=(8, 8), scale=1.05
            )
            people = []
            for box, weight in zip(boxes, weights):
                x, y, width, height = [int(value) for value in box]
                confidence = float(weight)
                people.append({"label": "person", "confidence": round(confidence, 3), "bbox": [x, y, width, height]})

            detections.append({
                "frame_number": frame_number,
                "frame_path": str(frame_path),
                "timestamp_seconds": timestamp,
                "people_count": len(people),
                "objects": people,
            })

            histogram = cv2.calcHist([image], [0, 1], None, [16, 16], [0, 256, 0, 256])
            cv2.normalize(histogram, histogram)
            if previous_hist is not None:
                change = float(cv2.compareHist(previous_hist, histogram, cv2.HISTCMP_BHATTACHARYYA))
                if change >= 0.45:
                    scenes.append({"timestamp_seconds": timestamp, "type": "scene_change", "score": round(change, 3)})
            previous_hist = histogram

        return {
            "engine": "OpenCV HOG people detector",
            "limitations": "Detects people locally. Other object labels require an additional object-detection model.",
            "frames": detections,
            "scene_changes": scenes,
        }

    @staticmethod
    def _timestamp(frame_path: str) -> float:
        match = re.search(r"_(\d+)s\.(?:jpg|jpeg|png)$", Path(frame_path).name, re.IGNORECASE)
        return float(match.group(1)) if match else 0.0
