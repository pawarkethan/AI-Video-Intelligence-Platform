from __future__ import annotations

import os

import streamlit as st

from config.settings import AUDIO_DIR
from services.asr_service import ASRService
from services.audio_service import AudioService
from services.timeline_service import TimelineService
from services.analysis_service import AnalysisService


# ============================================================
# SERVICE LOADERS
# ============================================================

@st.cache_resource(
    show_spinner=False
)
def load_audio_service():
    """
    Load the audio extraction service once.
    """

    return AudioService(
        output_directory=AUDIO_DIR
    )


@st.cache_resource(
    show_spinner=False
)
def load_asr_service(
    model_name: str = "small",
    device: str = "cpu",
    compute_type: str = "int8",
):
    """
    Load the ASR service once.

    Faster-Whisper is loaded only once and reused
    between Streamlit reruns.
    """

    return ASRService(
        model_name=model_name,
        device=device,
        compute_type=compute_type,
    )


# ============================================================
# TIMESTAMP FORMATTER
# ============================================================

def format_timestamp(
    seconds: float,
) -> str:
    """
    Convert seconds into HH:MM:SS or MM:SS.
    """

    total_seconds = max(
        0,
        int(float(seconds)),
    )

    hours = (
        total_seconds // 3600
    )

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


# ============================================================
# LANGUAGE OPTIONS
# ============================================================

LANGUAGE_MAP = {
    "Auto Detect": None,
    "English": "en",
    "Hindi": "hi",
    "Telugu": "te",
    "Tamil": "ta",
    "Kannada": "kn",
    "Malayalam": "ml",
    "Marathi": "mr",
    "Bengali": "bn",
}


# Smaller models and lower beam sizes complete substantially faster on CPUs.
# Keep the more accurate profiles available for recordings where quality matters
# more than turnaround time.
TRANSCRIPTION_PROFILES = {
    "Fast (recommended for CPU)": {
        "model_name": "base",
        "beam_size": 1,
        "description": "Fastest local option; suitable for clear speech.",
    },
    "Balanced": {
        "model_name": "small",
        "beam_size": 3,
        "description": "Better accuracy with a moderate processing time.",
    },
    "High accuracy": {
        "model_name": "medium",
        "beam_size": 5,
        "description": "Best local accuracy, but significantly slower on CPU.",
    },
}


# ============================================================
# TRANSCRIPT PAGE
# ============================================================

def render_transcript():

    # ========================================================
    # HEADER
    # ========================================================

    # Use Streamlit elements here instead of embedded HTML. This avoids any
    # Markdown/HTML parsing differences between Streamlit versions.
    st.markdown("## 🎙️ Speech & Transcript Intelligence")
    st.caption(
        "Extract speech from the uploaded video and generate a timestamped "
        "transcript using Faster-Whisper."
    )


    # ========================================================
    # CHECK VIDEO
    # ========================================================

    video_path = st.session_state.get(
        "video_path"
    )

    video_id = st.session_state.get(
        "video_id"
    )

    if not video_path:

        st.info(
            "📂 Upload a video first from "
            "the Video Analysis page."
        )

        return


    if not os.path.exists(
        video_path
    ):

        st.error(
            "❌ The uploaded video could not "
            "be found."
        )

        return


    st.success(
        "✅ Video is ready for speech recognition."
    )


    # ========================================================
    # TRANSCRIPTION SETTINGS
    # ========================================================

    st.markdown(
        "### ⚙️ Transcription Settings"
    )

    language_option = st.selectbox(
        "Language",
        list(
            LANGUAGE_MAP.keys()
        ),
        index=0,
    )

    selected_language = (
        LANGUAGE_MAP[
            language_option
        ]
    )

    profile_name = st.selectbox(
        "Speed and accuracy",
        list(TRANSCRIPTION_PROFILES.keys()),
        index=0,
        help=(
            "Fast uses a smaller local model and less search work, which "
            "greatly reduces CPU processing time."
        ),
    )

    transcription_profile = TRANSCRIPTION_PROFILES[
        profile_name
    ]

    st.caption(
        transcription_profile["description"]
    )


    # ========================================================
    # GENERATE TRANSCRIPT
    # ========================================================

    if st.button(
        "🎙️ Generate Transcript",
        type="primary",
        width="stretch",
    ):

        try:

            # ------------------------------------------------
            # AUDIO SERVICE
            # ------------------------------------------------

            audio_service = (
                load_audio_service()
            )

            with st.status(
                "Processing video...",
                expanded=True,
            ) as status:

                # ============================================
                # STEP 1
                # AUDIO EXTRACTION
                # ============================================

                st.write(
                    "🔊 Extracting audio from video..."
                )

                audio_path = (
                    audio_service.extract_audio(
                        video_path=video_path,
                        video_id=video_id,
                    )
                )


                # ------------------------------------------------
                # No audio
                # ------------------------------------------------

                if audio_path is None:

                    status.update(
                        label=(
                            "No audio stream found."
                        ),
                        state="error",
                    )

                    st.error(
                        "❌ This video does not "
                        "contain an audio stream."
                    )

                    return


                st.write(
                    "✅ Audio extraction completed."
                )

                st.write(
                    f"Audio: `{audio_path}`"
                )


                # ============================================
                # STEP 2
                # LOAD ASR
                # ============================================

                st.write(
                    "🧠 Loading Faster-Whisper..."
                )

                asr_service = (
                    load_asr_service(
                        model_name=(
                            transcription_profile["model_name"]
                        ),
                    )
                )


                st.write(
                    "✅ Faster-Whisper loaded."
                )


                # ============================================
                # STEP 3
                # TRANSCRIPTION
                # ============================================

                st.write(
                    "🎙️ Transcribing speech..."
                )

                result = (
                    asr_service.transcribe(
                        audio_path=audio_path,
                        language=(
                            selected_language
                        ),
                        beam_size=(
                            transcription_profile["beam_size"]
                        ),
                    )
                )


                # ============================================
                # STEP 4
                # STORE RESULTS
                # ============================================

                st.session_state[
                    "audio_path"
                ] = str(
                    audio_path
                )

                st.session_state[
                    "transcript"
                ] = result.get(
                    "text",
                    "",
                )

                st.session_state[
                    "transcript_segments"
                ] = result.get(
                    "segments",
                    [],
                )

                st.session_state[
                    "detected_language"
                ] = result.get(
                    "language",
                    "",
                )

                timeline_service = TimelineService()
                timeline_service.save_transcript(
                    video_id=video_id,
                    language=st.session_state["detected_language"],
                    segments=st.session_state["transcript_segments"],
                    text=st.session_state["transcript"],
                )

                timeline_service.save(
                    video_id=video_id,
                    ocr_results=st.session_state.get("ocr_results", []),
                    transcript_segments=st.session_state[
                        "transcript_segments"
                    ],
                )

                AnalysisService().update(
                    video_id,
                    transcript={
                        "language": st.session_state["detected_language"],
                        "text": st.session_state["transcript"],
                        "segments": st.session_state["transcript_segments"],
                    },
                )


                status.update(
                    label=(
                        "Transcription completed."
                    ),
                    state="complete",
                )


            st.success(
                "✅ Transcript generated successfully."
            )


        except Exception as error:

            st.error(
                "❌ Transcription failed: "
                f"{error}"
            )

            return


    # ========================================================
    # GET TRANSCRIPT
    # ========================================================

    transcript = (
        st.session_state.get(
            "transcript",
            "",
        )
    )

    if not transcript:

        st.info(
            "Click **Generate Transcript** "
            "to start speech recognition."
        )

        return


    # ========================================================
    # TRANSCRIPT INFORMATION
    # ========================================================

    st.divider()

    st.markdown(
        "### 📊 Transcript Information"
    )

    detected_language = (
        st.session_state.get(
            "detected_language",
            "",
        )
    )

    segments = (
        st.session_state.get(
            "transcript_segments",
            [],
        )
    )


    word_count = len(
        transcript.split()
    )


    col1, col2, col3 = st.columns(3)


    with col1:

        st.metric(
            "Detected Language",
            (
                detected_language
                if detected_language
                else "Unknown"
            ),
        )


    with col2:

        st.metric(
            "Transcript Segments",
            len(segments),
        )


    with col3:

        st.metric(
            "Word Count",
            word_count,
        )


    # ========================================================
    # FULL TRANSCRIPT
    # ========================================================

    st.markdown(
        "### 📝 Full Transcript"
    )

    st.text_area(
        "Transcript",
        value=transcript,
        height=350,
        disabled=True,
        label_visibility="collapsed",
    )


    # ========================================================
    # TIMESTAMPED TRANSCRIPT
    # ========================================================

    if not segments:

        return


    st.markdown(
        "### ⏱️ Timestamped Transcript"
    )

    for index, segment in enumerate(
        segments
    ):

        # ----------------------------------------------------
        # Dictionary result
        # ----------------------------------------------------

        if isinstance(
            segment,
            dict,
        ):

            start = segment.get(
                "start",
                0,
            )

            end = segment.get(
                "end",
                0,
            )

            text = segment.get(
                "text",
                "",
            )


        # ----------------------------------------------------
        # Object result
        # ----------------------------------------------------

        else:

            start = getattr(
                segment,
                "start",
                0,
            )

            end = getattr(
                segment,
                "end",
                0,
            )

            text = getattr(
                segment,
                "text",
                "",
            )


        start_time = (
            format_timestamp(
                start
            )
        )

        end_time = (
            format_timestamp(
                end
            )
        )


        # ----------------------------------------------------
        # Display segment
        # ----------------------------------------------------

        with st.container(
            border=True
        ):

            time_column, text_column = (
                st.columns(
                    [1, 5]
                )
            )


            with time_column:

                st.markdown(
                    f"**`{start_time}`**"
                )

                st.caption(
                    f"→ {end_time}"
                )


            with text_column:

                st.write(
                    text.strip()
                )
