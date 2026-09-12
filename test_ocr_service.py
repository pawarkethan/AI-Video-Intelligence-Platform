from pathlib import Path
import sys

from services.video_ocr_service import VideoOCRService


FRAME_DIRECTORY = Path(
    "data/frames"
)


def find_frames():

    if not FRAME_DIRECTORY.exists():
        return []

    supported_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
    }

    frames = []

    for file in FRAME_DIRECTORY.rglob("*"):

        if (
            file.is_file()
            and file.suffix.lower()
            in supported_extensions
        ):
            frames.append(file)

    return sorted(frames)


def main():

    if hasattr(sys.stdout, "reconfigure"):

        sys.stdout.reconfigure(encoding="utf-8")

    print("=" * 60)
    print("Testing OCR Service")
    print("=" * 60)

    frames = find_frames()

    if not frames:

        print(
            "\nNo frames found."
        )

        print(
            "First extract frames from your "
            "video using the Video Analysis page."
        )

        return

    print(
        f"\nFrames found: {len(frames)}"
    )

    print(
        "\nInitializing PaddleOCR..."
    )

    ocr_service = VideoOCRService(
        language="en"
    )

    print(
        "\nRunning OCR..."
    )

    results = (
        ocr_service.process_frames(frames)
    )

    print(
        "\n" + "=" * 60
    )

    print(
        "OCR RESULTS"
    )

    print(
        "=" * 60
    )

    total_text = 0

    for result in results:

        print(
            f"\nFrame: "
            f"{result['frame_number']} "
            f"at {result['timestamp']}"
        )

        print(
            f"Path: "
            f"{result['frame_path']}"
        )

        texts = result.get(
            "texts",
            [],
        )

        if not texts:

            print(
                "No text detected."
            )

            continue

        for item in texts:

            total_text += 1

            print(
                f"  Text: "
                f"{item['text']}"
            )

            print(
                f"  Confidence: "
                f"{item['confidence']}"
            )

    combined_text = "\n".join(
        item["text"]
        for result in results
        for item in result.get("texts", [])
    )

    print(
        "\n" + "=" * 60
    )

    print(
        f"Total text detections: "
        f"{total_text}"
    )

    print(
        "\nCombined OCR text:"
    )

    print(
        combined_text
        if combined_text
        else "No text detected."
    )

    print(
        "\n" + "=" * 60
    )


if __name__ == "__main__":
    main()
