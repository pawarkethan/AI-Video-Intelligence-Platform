from __future__ import annotations

from pathlib import Path
from typing import Optional

import ffmpeg


class AudioService:
    """
    Service responsible for extracting audio from videos.

    The extracted audio is converted to:

        WAV
        PCM signed 16-bit
        16 kHz
        Mono

    This format is suitable for speech-recognition
    models such as Faster-Whisper.
    """

    def __init__(
        self,
        output_directory: Path,
    ) -> None:

        self.output_directory = Path(
            output_directory
        )

        self.output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    def extract_audio(
        self,
        video_path: Path,
        video_id: str,
    ) -> Optional[Path]:
        """
        Extract audio from a video.

        Parameters
        ----------
        video_path:
            Path to the input video.

        video_id:
            Unique identifier for the video.

        Returns
        -------
        Path | None
            Path to extracted WAV audio.

            Returns None if the video does not
            contain an audio stream.
        """

        video_path = Path(video_path)

        if not video_path.exists():

            raise FileNotFoundError(
                f"Video file not found: "
                f"{video_path}"
            )

        output_path = (
            self.output_directory
            / f"{video_id}.wav"
        )

        # -------------------------------------------------
        # Check whether the video contains an audio stream
        # -------------------------------------------------

        try:

            probe = ffmpeg.probe(
                str(video_path)
            )

        except ffmpeg.Error as error:

            error_message = (
                error.stderr.decode(
                    "utf-8",
                    errors="ignore",
                )
                if error.stderr
                else str(error)
            )

            raise RuntimeError(
                "Unable to inspect video "
                f"with FFmpeg:\n{error_message}"
            ) from error

        audio_streams = [
            stream
            for stream in probe.get(
                "streams",
                [],
            )
            if stream.get("codec_type") == "audio"
        ]

        if not audio_streams:

            return None

        # -------------------------------------------------
        # Extract audio
        # -------------------------------------------------

        try:

            (
                ffmpeg
                .input(str(video_path))
                .output(
                    str(output_path),
                    acodec="pcm_s16le",
                    ac=1,
                    ar=16000,
                    vn=None,
                )
                .overwrite_output()
                .run(
                    capture_stdout=True,
                    capture_stderr=True,
                )
            )

        except ffmpeg.Error as error:

            error_message = (
                error.stderr.decode(
                    "utf-8",
                    errors="ignore",
                )
                if error.stderr
                else str(error)
            )

            raise RuntimeError(
                "FFmpeg failed while extracting "
                f"audio:\n{error_message}"
            ) from error

        if not output_path.exists():

            raise RuntimeError(
                "Audio extraction completed, "
                "but the output file was not created."
            )

        if output_path.stat().st_size == 0:

            raise RuntimeError(
                "Extracted audio file is empty."
            )

        return output_path

    def get_audio_metadata(
        self,
        audio_path: Path,
    ) -> dict:
        """
        Return basic metadata for an extracted audio file.
        """

        audio_path = Path(audio_path)

        if not audio_path.exists():

            raise FileNotFoundError(
                f"Audio file not found: "
                f"{audio_path}"
            )

        try:

            probe = ffmpeg.probe(
                str(audio_path)
            )

        except ffmpeg.Error as error:

            error_message = (
                error.stderr.decode(
                    "utf-8",
                    errors="ignore",
                )
                if error.stderr
                else str(error)
            )

            raise RuntimeError(
                "Unable to read audio metadata:\n"
                f"{error_message}"
            ) from error

        audio_stream = next(
            (
                stream
                for stream in probe.get(
                    "streams",
                    [],
                )
                if stream.get("codec_type")
                == "audio"
            ),
            None,
        )

        if audio_stream is None:

            return {}

        duration = float(
            audio_stream.get(
                "duration",
                0,
            )
            or 0
        )

        sample_rate = int(
            audio_stream.get(
                "sample_rate",
                0,
            )
            or 0
        )

        channels = int(
            audio_stream.get(
                "channels",
                0,
            )
            or 0
        )

        return {
            "duration_seconds": duration,
            "sample_rate": sample_rate,
            "channels": channels,
            "codec": audio_stream.get(
                "codec_name",
                "",
            ),
            "format": audio_stream.get(
                "codec_long_name",
                "",
            ),
        }