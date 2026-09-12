from __future__ import annotations

from pathlib import Path
from typing import Optional

from faster_whisper import WhisperModel


class ASRService:
    """
    Automatic Speech Recognition service using Faster-Whisper.

    Responsibilities:
    - Load the Whisper model
    - Transcribe extracted audio
    - Detect spoken language
    - Generate timestamped transcript segments
    """

    def __init__(
        self,
        model_name: str = "small",
        device: str = "cpu",
        compute_type: str = "int8",
        engine_name: str | None = None,
    ):
        # ``engine_name`` was accepted by an earlier UI integration.  This
        # service is implemented with Faster-Whisper, so keep that argument
        # as a harmless compatibility alias while Streamlit reloads cached
        # application code.
        if engine_name not in (None, "faster-whisper"):
            raise ValueError(
                "Unsupported ASR engine. Only 'faster-whisper' is available."
            )

        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type

        print("=" * 60)
        print("Loading ASR Model")
        print("=" * 60)
        print(f"Model        : {self.model_name}")
        print(f"Device       : {self.device}")
        print(f"Compute type : {self.compute_type}")
        print("=" * 60)

        try:
            self.model = WhisperModel(
                self.model_name,
                device=self.device,
                compute_type=self.compute_type,
            )

        except Exception as error:

            print(
                "CUDA model loading failed."
            )

            print(
                f"Reason: {error}"
            )

            print(
                "Falling back to CPU..."
            )

            self.device = "cpu"
            self.compute_type = "int8"

            self.model = WhisperModel(
                self.model_name,
                device="cpu",
                compute_type="int8",
            )

        print(
            "ASR model loaded successfully."
        )

        print("=" * 60)

    def transcribe(
        self,
        audio_path: str | Path,
        language: Optional[str] = None,
        beam_size: int = 5,
    ) -> dict:
        """
        Transcribe an audio file.

        Returns:

        {
            "text": "...",
            "language": "en",
            "language_probability": 0.98,
            "segments": [
                {
                    "start": 0.0,
                    "end": 4.2,
                    "text": "Hello everyone."
                }
            ]
        }
        """

        audio_path = Path(audio_path)

        if not audio_path.exists():

            raise FileNotFoundError(
                f"Audio file not found: {audio_path}"
            )

        print()
        print("=" * 60)
        print("Starting Speech Recognition")
        print("=" * 60)

        print(
            f"Audio: {audio_path}"
        )

        if language:

            print(
                f"Language: {language}"
            )

        else:

            print(
                "Language: Auto Detect"
            )

        segments, info = self.model.transcribe(
            str(audio_path),
            language=language,
            beam_size=beam_size,
            vad_filter=True,
            word_timestamps=False,
        )

        transcript_segments = []

        full_text_parts = []

        for segment in segments:

            text = segment.text.strip()

            if not text:
                continue

            start = round(
                float(segment.start),
                2,
            )

            end = round(
                float(segment.end),
                2,
            )

            transcript_segments.append(
                {
                    "start": start,
                    "end": end,
                    "text": text,
                }
            )

            full_text_parts.append(text)

        full_text = " ".join(
            full_text_parts
        ).strip()

        detected_language = getattr(
            info,
            "language",
            None,
        )

        language_probability = getattr(
            info,
            "language_probability",
            0.0,
        )

        result = {
            "text": full_text,
            "language": detected_language,
            "language_probability": round(
                float(language_probability),
                4,
            ),
            "segments": transcript_segments,
            "device": self.device,
            "model": self.model_name,
        }

        print()
        print(
            "Transcription completed."
        )

        print(
            f"Detected language: "
            f"{detected_language}"
        )

        print(
            f"Language probability: "
            f"{language_probability:.2f}"
        )

        print(
            f"Segments: "
            f"{len(transcript_segments)}"
        )

        print("=" * 60)

        return result
