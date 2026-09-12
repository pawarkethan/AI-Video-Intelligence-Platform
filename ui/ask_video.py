from pathlib import Path
import json

import streamlit as st

from config.settings import OCR_DIR, TRANSCRIPT_DIR
from services.qa_service import VideoQAService
from services.analysis_service import AnalysisService


# ==========================================================
# Paths
# ==========================================================

# ==========================================================
# Helpers
# ==========================================================

def load_latest_json(
    directory: Path
):

    if not directory.exists():
        return None

    files = list(
        directory.glob("*.json")
    )

    if not files:
        return None

    latest_file = max(
        files,
        key=lambda file: file.stat().st_mtime
    )

    try:

        with open(
            latest_file,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception as error:

        st.warning(
            f"Could not read {latest_file.name}: "
            f"{error}"
        )

        return None


def load_latest_text(
    directory: Path
):

    if not directory.exists():
        return None

    files = list(
        directory.glob("*.txt")
    )

    if not files:
        return None

    latest_file = max(
        files,
        key=lambda file: file.stat().st_mtime
    )

    try:

        return latest_file.read_text(
            encoding="utf-8"
        )

    except Exception as error:

        st.warning(
            f"Could not read {latest_file.name}: "
            f"{error}"
        )

        return None


# ==========================================================
# Load transcript
# ==========================================================

def load_transcript(video_id: str | None = None):

    if video_id:

        transcript_path = TRANSCRIPT_DIR / f"{video_id}.json"

        if transcript_path.exists():

            return load_json_file(transcript_path)

    transcript = load_latest_json(
        TRANSCRIPT_DIR
    )

    if transcript is not None:
        return transcript

    return load_latest_text(
        TRANSCRIPT_DIR
    )


# ==========================================================
# Load OCR
# ==========================================================

def load_ocr(video_id: str | None = None):

    if video_id:

        ocr_path = OCR_DIR / f"{video_id}_ocr.json"

        if ocr_path.exists():

            return load_json_file(ocr_path)

    return load_latest_json(
        OCR_DIR
    )


def load_json_file(path: Path):
    """Load one known analysis file and surface a useful read error."""

    try:

        return json.loads(path.read_text(encoding="utf-8"))

    except Exception as error:

        st.warning(f"Could not read {path.name}: {error}")
        return None


# ==========================================================
# Main page
# ==========================================================

def render():

    st.title(
        "💬 Ask Your Video"
    )

    st.caption(
        "Ask questions about your video's "
        "spoken content and on-screen text."
    )

    # ------------------------------------------------------
    # Load data
    # ------------------------------------------------------

    video_id = st.session_state.get("video_id")
    transcript = load_transcript(video_id)
    ocr_results = load_ocr(video_id)

    # ------------------------------------------------------
    # Data status
    # ------------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:

        if transcript:

            st.success(
                "🎙️ Transcript available"
            )

        else:

            st.warning(
                "🎙️ Transcript not found"
            )

    with col2:

        if ocr_results:

            st.success(
                "🔤 OCR data available"
            )

        else:

            st.info(
                "🔤 OCR data not found"
            )

    if not transcript and not ocr_results:

        st.warning(
            "No video analysis data is available yet."
        )

        st.info(
            "Run Video Analysis and Transcript/OCR "
            "processing first."
        )

        return

    try:

        api_key = st.secrets["GEMINI_API_KEY"]

    except Exception:

        api_key = None

    if not api_key:

        st.info(
            "Analysis data is saved. Add GEMINI_API_KEY to "
            ".streamlit/secrets.toml to enable answers."
        )

        return

    # ------------------------------------------------------
    # Initialize conversation
    # ------------------------------------------------------

    if "video_qa_messages" not in st.session_state:

        st.session_state.video_qa_messages = []

    # ------------------------------------------------------
    # Service
    # ------------------------------------------------------

    try:

        qa_service = VideoQAService(
            api_key=api_key
        )

    except Exception as error:

        st.error(
            f"Failed to initialize AI service: {error}"
        )

        return

    # ------------------------------------------------------
    # Example questions
    # ------------------------------------------------------

    st.subheader(
        "💡 Try asking"
    )

    examples = [
        "What is this video about?",
        "What did the speaker say about AI?",
        "What text appeared on screen?",
        "Summarize the main points.",
        "What was discussed around 2 minutes?",
    ]

    cols = st.columns(2)

    for index, example in enumerate(
        examples
    ):

        with cols[index % 2]:

            if st.button(
                example,
                key=f"example_{index}",
                width="stretch",
            ):

                st.session_state[
                    "selected_video_question"
                ] = example

    # ------------------------------------------------------
    # Question input
    # ------------------------------------------------------

    selected_question = st.session_state.pop(
        "selected_video_question",
        ""
    )

    question = st.chat_input(
        "Ask something about your video..."
    )

    if question is None and selected_question:

        question = selected_question

    # ------------------------------------------------------
    # Show conversation
    # ------------------------------------------------------

    for message in st.session_state.video_qa_messages:

        with st.chat_message(
            message["role"]
        ):

            st.markdown(
                message["content"]
            )

    # ------------------------------------------------------
    # Process question
    # ------------------------------------------------------

    if question:

        # User message

        st.session_state.video_qa_messages.append(
            {
                "role": "user",
                "content": question,
            }
        )

        with st.chat_message("user"):

            st.markdown(question)

        # Previous conversation for context

        previous_messages = (
            st.session_state.video_qa_messages[
                :-1
            ]
        )

        # AI response

        with st.chat_message("assistant"):

            with st.spinner(
                "Analyzing your video..."
            ):

                try:

                    answer = qa_service.ask(
                        question=question,
                        transcript=transcript,
                        ocr_results=ocr_results,
                        conversation_history=(
                            previous_messages
                        ),
                        video_id=video_id,
                    )

                    st.markdown(answer)

                    st.session_state.video_qa_messages.append(
                        {
                            "role": "assistant",
                            "content": answer,
                        }
                    )

                    if video_id:
                        AnalysisService().update(
                            video_id,
                            qa=st.session_state.video_qa_messages,
                        )

                except Exception as error:

                    st.error(
                        f"Failed to generate answer: "
                        f"{error}"
                    )

    # ------------------------------------------------------
    # Clear chat
    # ------------------------------------------------------

    if st.session_state.video_qa_messages:

        st.divider()

        if st.button(
            "🗑️ Clear Conversation"
        ):

            st.session_state.video_qa_messages = []

            st.rerun()
