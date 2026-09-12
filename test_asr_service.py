from pathlib import Path

from services.asr_service import ASRService


AUDIO_PATH = Path(
    "data/audio/test_video.wav"
)


def format_timestamp(
    seconds: float,
) -> str:

    total_seconds = max(
        0,
        int(seconds),
    )

    hours = total_seconds // 3600

    minutes = (
        total_seconds % 3600
    ) // 60

    remaining_seconds = (
        total_seconds % 60
    )

    if hours > 0:

        return (
            f"{hours:02d}:"
            f"{minutes:02d}:"
            f"{remaining_seconds:02d}"
        )

    return (
        f"{minutes:02d}:"
        f"{remaining_seconds:02d}"
    )


def main():

    print()
    print("=" * 60)
    print("Testing Automatic Speech Recognition")
    print("=" * 60)

    print(
        f"Audio: {AUDIO_PATH}"
    )

    if not AUDIO_PATH.exists():

        print()
        print(
            "ERROR: Audio file does not exist."
        )

        print(
            f"Expected path: {AUDIO_PATH}"
        )

        return

    # --------------------------------------------------
    # Load ASR
    # --------------------------------------------------

    print()
    print(
        "Initializing Faster-Whisper..."
    )

    asr_service = ASRService(
        model_name="small",
        device="cuda",
        compute_type="int8_float16",
    )

    # --------------------------------------------------
    # Transcription
    # --------------------------------------------------

    print()
    print(
        "Transcribing audio..."
    )

    result = asr_service.transcribe(
        audio_path=AUDIO_PATH,
        language=None,
    )

    # --------------------------------------------------
    # Results
    # --------------------------------------------------

    print()
    print("=" * 60)
    print("TRANSCRIPTION RESULT")
    print("=" * 60)

    print()
    print(
        f"Detected language: "
        f"{result['language']}"
    )

    print(
        f"Language probability: "
        f"{result['language_probability']}"
    )

    print(
        f"Device: "
        f"{result['device']}"
    )

    print(
        f"Model: "
        f"{result['model']}"
    )

    print(
        f"Segments: "
        f"{len(result['segments'])}"
    )

    # --------------------------------------------------
    # Full transcript
    # --------------------------------------------------

    print()
    print("-" * 60)
    print("FULL TRANSCRIPT")
    print("-" * 60)

    print(
        result["text"]
    )

    # --------------------------------------------------
    # Timestamped transcript
    # --------------------------------------------------

    print()
    print("-" * 60)
    print("TIMESTAMPED TRANSCRIPT")
    print("-" * 60)

    for segment in result["segments"]:

        start = format_timestamp(
            segment["start"]
        )

        end = format_timestamp(
            segment["end"]
        )

        text = segment["text"]

        print(
            f"[{start} - {end}] "
            f"{text}"
        )

    print()
    print("=" * 60)
    print("ASR TEST COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()