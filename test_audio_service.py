from pathlib import Path

from config.settings import AUDIO_DIR
from services.audio_service import AudioService


# ============================================================
# Test video
# ============================================================

VIDEO_PATH = Path("data") / "uploads" / "AI_Video.mp4"

VIDEO_ID = "test_video"


# ============================================================
# Main test
# ============================================================

def main():

    print("=" * 60)
    print("Testing Audio Extraction")
    print("=" * 60)

    print(f"\nVideo: {VIDEO_PATH}")

    # --------------------------------------------------------
    # Check video exists
    # --------------------------------------------------------

    if not VIDEO_PATH.exists():

        print("\n❌ Video file not found.")

        print(
            f"Expected path:\n"
            f"{VIDEO_PATH.resolve()}"
        )

        return

    print(
        f"Video size: "
        f"{VIDEO_PATH.stat().st_size / (1024 * 1024):.2f} MB"
    )

    # --------------------------------------------------------
    # Initialize AudioService
    # --------------------------------------------------------

    try:

        audio_service = AudioService(
            output_directory=AUDIO_DIR
        )

        print(
            "\n✅ AudioService initialized successfully."
        )

    except Exception as error:

        print(
            "\n❌ Failed to initialize AudioService:"
        )

        print(error)

        return

    # --------------------------------------------------------
    # Extract audio
    # --------------------------------------------------------

    print("\nExtracting audio...")

    try:

        audio_path = (
            audio_service.extract_audio(
                video_path=VIDEO_PATH,
                video_id=VIDEO_ID,
            )
        )

    except Exception as error:

        print(
            "\n❌ Audio extraction failed:"
        )

        print(error)

        return

    # --------------------------------------------------------
    # No audio stream
    # --------------------------------------------------------

    if audio_path is None:

        print(
            "\n⚠️ No audio stream found "
            "in the video."
        )

        return

    # --------------------------------------------------------
    # Verify extracted audio
    # --------------------------------------------------------

    audio_path = Path(audio_path)

    if not audio_path.exists():

        print(
            "\n❌ Audio extraction returned a path "
            "but the audio file does not exist."
        )

        print(
            f"Expected audio path:\n"
            f"{audio_path}"
        )

        return

    print(
        "\n✅ Audio extracted successfully!"
    )

    print(
        f"Audio path: {audio_path}"
    )

    print(
        f"Audio size: "
        f"{audio_path.stat().st_size / (1024 * 1024):.2f} MB"
    )

    # --------------------------------------------------------
    # Audio metadata
    # --------------------------------------------------------

    print("\nReading audio metadata...")

    try:

        metadata = (
            audio_service.get_audio_metadata(
                audio_path
            )
        )

    except Exception as error:

        print(
            "\n❌ Failed to read audio metadata:"
        )

        print(error)

        return

    print(
        "\nAudio metadata:"
    )

    if metadata:

        for key, value in metadata.items():

            print(
                f"  {key}: {value}"
            )

    else:

        print(
            "  No metadata returned."
        )

    # --------------------------------------------------------
    # Completed
    # --------------------------------------------------------

    print(
        "\n" + "=" * 60
    )

    print(
        "✅ Audio extraction test completed."
    )

    print(
        "=" * 60
    )


# ============================================================
# Python entry point
# ============================================================

if __name__ == "__main__":
    main()