from pathlib import Path
import textwrap

import streamlit as st

from config.settings import (
    APP_NAME,
    initialize_directories,
)

from ui.home import render_home
from ui.upload import render_upload
from ui.transcript import render_transcript
from ui.ask_video import render as render_ask_video
from ui.summary import render_summary
from ui.education import render_education
from ui.exports import render_exports


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🎥",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# INITIALIZE APPLICATION DIRECTORIES
# ============================================================

initialize_directories()


# ============================================================
# LOAD GLOBAL CSS
# ============================================================

def load_css():
    """
    Load the application's global CSS file.
    """

    project_root = Path(__file__).resolve().parent

    css_path = (
        project_root
        / "assets"
        / "styles.css"
    )

    if not css_path.exists():

        st.warning(
            "Global stylesheet was not found: "
            f"{css_path}"
        )

        return

    try:

        css_content = css_path.read_text(
            encoding="utf-8"
        )

        st.markdown(
            f"""
            <style>
            {css_content}
            </style>
            """,
            unsafe_allow_html=True,
        )

    except Exception as error:

        st.warning(
            "Unable to load application "
            f"stylesheet: {error}"
        )


load_css()


# ============================================================
# SESSION STATE
# ============================================================

def initialize_session_state():
    """
    Initialize application-wide session state.
    """

    defaults = {

        # ----------------------------------------------------
        # Video information
        # ----------------------------------------------------

        "video_path": None,

        "video_id": None,

        "video_metadata": {},

        "video_filename": "",

        "video_file_size_mb": 0.0,

        "video_frames": [],


        # ----------------------------------------------------
        # Audio information
        # ----------------------------------------------------

        "audio_path": None,


        # ----------------------------------------------------
        # Speech / ASR
        # ----------------------------------------------------

        "transcript": "",

        "transcript_segments": [],

        "detected_language": "",


        # ----------------------------------------------------
        # Video analysis
        # ----------------------------------------------------

        "detected_objects": [],

        "detected_people": [],

        "detected_events": [],

        "ocr_results": [],


        # ----------------------------------------------------
        # AI generated content
        # ----------------------------------------------------

        "video_summary": "",

        "video_insights": "",

        "video_questions": [],


        # ----------------------------------------------------
        # Processing status
        # ----------------------------------------------------

        "video_processing": False,

        "processing_error": "",

    }

    for key, default_value in defaults.items():

        if key not in st.session_state:

            st.session_state[key] = default_value


initialize_session_state()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.html(
        textwrap.dedent(
            """
        <div
            style="
                text-align: center;
                padding: 10px 0 20px 0;
            "
        >

            <div
                style="
                    font-size: 42px;
                "
            >
                🎥
            </div>

            <div
                style="
                    font-size: 20px;
                    font-weight: 700;
                    color: #f8f7ff;
                    margin-top: 8px;
                    letter-spacing: -0.3px;
                "
            >
                AI Video Intelligence
            </div>

            <div
                style="
                    font-size: 12px;
                    color: #c4b5fd;
                    margin-top: 5px;
                    font-weight: 500;
                "
            >
                Multimodal Video Understanding
            </div>

        </div>
            """
        ).strip(),
    )

    st.divider()

    page = st.radio(
        "Navigation",
        [
            "🏠 Dashboard",
            "🎥 Video Analysis",
            "🎙️ Transcript",
            "🧠 AI Summary",
            "\U0001F4AC Ask Your Video",
            "🎓 Education",
            "📤 Export",
        ],
        label_visibility="collapsed",
    )

    st.divider()

    st.caption(
        "Computer Vision • Speech AI • OCR • LLM"
    )


# ============================================================
# MAIN APPLICATION
# ============================================================

if page == "🏠 Dashboard":

    render_home()


elif page == "🎥 Video Analysis":

    render_upload()


elif page == "🎙️ Transcript":

    render_transcript()


elif page == "🧠 AI Summary":

    render_summary()


elif page == "\U0001F4AC Ask Your Video":

    render_ask_video()


elif page == "🎓 Education":

    render_education()


elif page == "📤 Export":

    render_exports()
