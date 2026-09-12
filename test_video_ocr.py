from __future__ import annotations

import sys
from pathlib import Path

from services.video_ocr_service import VideoOCRService


FRAME_DIRECTORY = Path("data/frames")


def find_frames() -> list[Path]:
    """Find frames created by VideoService in chronological filename order."""

    supported_extensions = {".jpg", ".jpeg", ".png", ".webp"}

    return sorted(
        path
        for path in FRAME_DIRECTORY.rglob("*")
        if path.is_file() and path.suffix.lower() in supported_extensions
    )


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    frames = find_frames()

    if not frames:
        print("No extracted frames found in data/frames.")
        return

    print(f"Running OCR on {len(frames)} extracted frame(s)...")

    service = VideoOCRService(language="en")
    results = service.process_frames(frames)

    for result in results:
        print("\n" + "=" * 60)
        print(
            f"Frame {result['frame_number']} | "
            f"Timestamp: {result['timestamp']}"
        )

        if result.get("error"):
            print(f"OCR error: {result['error']}")
            continue

        texts = result["texts"]

        if not texts:
            print("No text detected.")
            continue

        for item in texts:
            print(f"Text: {item['text']}")
            print(f"Confidence: {item['confidence']}")


if __name__ == "__main__":
    main()
