from __future__ import annotations

from pathlib import Path
from typing import Any

import cv2


class VideoService:
    """
    Handles basic video processing.

    Responsibilities:
        - Read video metadata
        - Validate video
        - Extract frames
    """

    def __init__(self):
        pass

    # -----------------------------------------------------
    # Video validation
    # -----------------------------------------------------

    def validate_video(
        self,
        video_path: str | Path,
    ) -> bool:
        """
        Check whether OpenCV can open the video.
        """

        capture = cv2.VideoCapture(
            str(video_path)
        )

        if not capture.isOpened():
            capture.release()
            return False

        capture.release()

        return True

    # -----------------------------------------------------
    # Metadata
    # -----------------------------------------------------

    def get_metadata(
        self,
        video_path: str | Path,
    ) -> dict[str, Any]:
        """
        Extract video metadata.
        """

        capture = cv2.VideoCapture(
            str(video_path)
        )

        if not capture.isOpened():
            raise ValueError(
                "Unable to open video file."
            )

        fps = float(
            capture.get(
                cv2.CAP_PROP_FPS
            )
        )

        frame_count = int(
            capture.get(
                cv2.CAP_PROP_FRAME_COUNT
            )
        )

        width = int(
            capture.get(
                cv2.CAP_PROP_FRAME_WIDTH
            )
        )

        height = int(
            capture.get(
                cv2.CAP_PROP_FRAME_HEIGHT
            )
        )

        duration = (
            frame_count / fps
            if fps > 0
            else 0
        )

        capture.release()

        return {
            "width": width,
            "height": height,
            "fps": round(fps, 2),
            "frame_count": frame_count,
            "duration_seconds": round(
                duration,
                2,
            ),
        }

    # -----------------------------------------------------
    # Frame extraction
    # -----------------------------------------------------

    def extract_frames(
        self,
        video_path: str | Path,
        output_directory: str | Path,
        interval_seconds: int = 5,
    ) -> list[str]:
        """
        Extract one frame every N seconds.
        """

        video_path = Path(video_path)

        output_directory = Path(
            output_directory
        )

        output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        capture = cv2.VideoCapture(
            str(video_path)
        )

        if not capture.isOpened():
            raise ValueError(
                "Unable to open video."
            )

        fps = float(
            capture.get(
                cv2.CAP_PROP_FPS
            )
        )

        frame_count = int(
            capture.get(
                cv2.CAP_PROP_FRAME_COUNT
            )
        )

        if fps <= 0:
            capture.release()

            raise ValueError(
                "Invalid video FPS."
            )

        duration = frame_count / fps

        extracted_frames = []

        current_time = 0.0

        frame_index = 0

        while current_time <= duration:

            capture.set(
                cv2.CAP_PROP_POS_MSEC,
                current_time * 1000,
            )

            success, frame = capture.read()

            if not success:
                break

            filename = (
                f"frame_{frame_index:06d}"
                f"_{int(current_time)}s.jpg"
            )

            frame_path = (
                output_directory / filename
            )

            cv2.imwrite(
                str(frame_path),
                frame,
            )

            extracted_frames.append(
                str(frame_path)
            )

            frame_index += 1

            current_time += interval_seconds

        capture.release()

        return extracted_frames