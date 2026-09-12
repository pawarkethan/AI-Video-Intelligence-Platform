from pathlib import Path
import sys

from services.ocr_service import OCRService


# ============================================================
# Configuration
# ============================================================

# Put your test image here:
# data/test_images/text_test.png

IMAGE_PATH = Path(
    "data/test_images/text_test.png"
)


# ============================================================
# Main
# ============================================================

def main():

    # PaddleOCR can return Unicode text from screenshots.  Use UTF-8 on
    # Windows terminals so displaying a valid OCR result cannot abort a test.
    if hasattr(sys.stdout, "reconfigure"):

        sys.stdout.reconfigure(encoding="utf-8")

    print("=" * 60)
    print("Testing OCR on Single Image")
    print("=" * 60)

    print(
        f"\nImage: {IMAGE_PATH}"
    )

    # --------------------------------------------------------
    # Check image
    # --------------------------------------------------------

    if not IMAGE_PATH.exists():

        print(
            "\nERROR: Image file not found."
        )

        print(
            "\nExpected image location:"
        )

        print(
            f"  {IMAGE_PATH.resolve()}"
        )

        print(
            "\nCreate the folder:"
        )

        print(
            "  data/test_images/"
        )

        print(
            "\nThen place a text image inside it "
            "with the name:"
        )

        print(
            "  text_test.png"
        )

        return

    # --------------------------------------------------------
    # Initialize OCR
    # --------------------------------------------------------

    print(
        "\nInitializing PaddleOCR..."
    )

    try:

        ocr_service = OCRService(
            language="en"
        )

    except Exception as error:

        print(
            "\nERROR: Failed to initialize OCR."
        )

        print(
            f"Details: {error}"
        )

        return

    # --------------------------------------------------------
    # Run OCR
    # --------------------------------------------------------

    print(
        "\nRunning OCR..."
    )

    try:

        results = (
            ocr_service.extract_text(
                IMAGE_PATH
            )
        )

    except Exception as error:

        print(
            "\nERROR: OCR failed."
        )

        print(
            f"Details: {error}"
        )

        return

    # ========================================================
    # Results
    # ========================================================

    print("\n" + "=" * 60)
    print("OCR RESULTS")
    print("=" * 60)

    if not results:

        print(
            "\nNo text detected."
        )

        print(
            "\nTry using an image with:"
        )

        print(
            "  • Large English text"
        )

        print(
            "  • Good lighting"
        )

        print(
            "  • High resolution"
        )

        print(
            "  • Clear background"
        )

        return

    print(
        f"\nText detections: {len(results)}"
    )

    print("\nDetected text:\n")

    for index, item in enumerate(
        results,
        start=1,
    ):

        print(
            f"{index}. {item['text']}"
        )

        print(
            f"   Confidence: "
            f"{item['confidence']}"
        )

        print(
            f"   Bounding box: "
            f"{item['bbox']}"
        )

        print()

    # --------------------------------------------------------
    # Combined text
    # --------------------------------------------------------

    combined_text = (
        ocr_service.get_combined_text(
            [
                {
                    "frame_index": 0,
                    "frame_path": str(
                        IMAGE_PATH
                    ),
                    "texts": results,
                }
            ]
        )
    )

    print("=" * 60)
    print("COMBINED TEXT")
    print("=" * 60)

    print()

    if combined_text:

        print(
            combined_text
        )

    else:

        print(
            "No text detected."
        )

    print(
        "\n" + "=" * 60
    )


# ============================================================
# Entry point
# ============================================================

if __name__ == "__main__":
    main()
