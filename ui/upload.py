from __future__ import annotations

from pathlib import Path

import streamlit as st

from config.constants import (
    MAX_UPLOAD_SIZE_MB,
    SUPPORTED_VIDEO_TYPES,
)

from config.settings import (
    FRAME_DIR,
    UPLOAD_DIR,
)

from services.video_service import VideoService
from services.video_ocr_service import VideoOCRService
from services.timeline_service import TimelineService
from services.analysis_service import AnalysisService
from services.vision_service import VisionService

from utils.file_utils import (
    create_safe_filename,
    generate_file_id,
)


# ============================================================
# Cached Services
# ============================================================

@st.cache_resource
def get_video_service():
    """
    Create and cache VideoService.

    Streamlit reruns the script frequently, so caching prevents
    unnecessary service initialization.
    """

    return VideoService()


@st.cache_resource
def get_ocr_service():
    """
    Create and cache PaddleOCR service.

    PaddleOCR model loading is expensive, so we only want
    to initialize it once during the Streamlit session.
    """

    return VideoOCRService(
        language="en",
    )


@st.cache_resource
def get_vision_service():
    """Create the lightweight local computer-vision service once."""

    return VisionService()


# ============================================================
# Helpers
# ============================================================

def format_duration(seconds: float) -> str:
    """
    Convert seconds into HH:MM:SS or MM:SS format.
    """

    total_seconds = max(
        0,
        int(float(seconds)),
    )

    hours = total_seconds // 3600

    minutes = (
        total_seconds % 3600
    ) // 60

    remaining = total_seconds % 60

    if hours > 0:
        return (
            f"{hours:02d}:"
            f"{minutes:02d}:"
            f"{remaining:02d}"
        )

    return (
        f"{minutes:02d}:"
        f"{remaining:02d}"
    )


def ensure_directories() -> None:
    """
    Make sure upload and frame directories exist.
    """

    UPLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    FRAME_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def reset_video_state() -> None:
    """
    Clear previous video-related session state.
    """

    st.session_state["video_path"] = None

    st.session_state["video_id"] = None

    st.session_state["video_metadata"] = {}

    st.session_state["video_filename"] = ""

    st.session_state["video_file_size_mb"] = 0.0

    st.session_state["video_frames"] = []

    st.session_state["ocr_results"] = []

    st.session_state["ocr_completed"] = False

    st.session_state["video_summary"] = ""
    st.session_state["video_insights"] = ""
    st.session_state["vision_results"] = {}


# ============================================================
# Main Upload UI
# ============================================================

def render_upload():

    ensure_directories()

    # --------------------------------------------------------
    # Header
    # --------------------------------------------------------

    # Native Streamlit elements prevent indented HTML from being rendered as
    # a Markdown code block on newer Streamlit versions.
    st.markdown(
        "## 🎥 Video Analysis"
    )

    st.caption(
        "Upload a video to begin multimodal video intelligence analysis."
    )

    # --------------------------------------------------------
    # Upload
    # --------------------------------------------------------

    uploaded_file = st.file_uploader(
        "Upload your video",
        type=SUPPORTED_VIDEO_TYPES,
        help=(
            f"Maximum file size: "
            f"{MAX_UPLOAD_SIZE_MB} MB"
        ),
    )

    # Streamlit clears file-uploader values while another page is active. Use
    # our saved copy so returning to this page preserves the completed work.
    using_saved_upload = False
    saved_video_path = st.session_state.get("video_path")
    if uploaded_file is None and saved_video_path:
        saved_path = Path(saved_video_path)
        if saved_path.is_file():
            saved_name = st.session_state.get("video_filename") or saved_path.name
            uploaded_file = type(
                "SavedVideoUpload",
                (),
                {
                    "name": saved_name,
                    "size": saved_path.stat().st_size,
                    "getvalue": lambda self: saved_path.read_bytes(),
                },
            )()
            using_saved_upload = True

    if uploaded_file is None:

        st.info(
            "📂 Upload a video to begin analysis."
        )

        return

    # --------------------------------------------------------
    # File size validation
    # --------------------------------------------------------

    file_size_mb = (
        uploaded_file.size
        / (1024 * 1024)
    )

    if file_size_mb > MAX_UPLOAD_SIZE_MB:

        st.error(
            f"❌ File is too large.\n\n"
            f"Maximum allowed size: "
            f"{MAX_UPLOAD_SIZE_MB} MB\n\n"
            f"Uploaded file: "
            f"{file_size_mb:.2f} MB"
        )

        return

    # --------------------------------------------------------
    # Read uploaded file
    # --------------------------------------------------------

    try:

        file_bytes = uploaded_file.getvalue()

    except Exception as error:

        st.error(
            f"Unable to read uploaded file: {error}"
        )

        return

    if not file_bytes:

        st.error(
            "The uploaded file is empty."
        )

        return

    # --------------------------------------------------------
    # Generate file identity
    # --------------------------------------------------------

    try:

        file_id = (
            st.session_state["video_id"]
            if using_saved_upload
            else generate_file_id(
                uploaded_file.name,
                file_bytes,
            )
        )

        safe_filename = create_safe_filename(uploaded_file.name)

    except Exception as error:

        st.error(
            f"Unable to prepare uploaded file: {error}"
        )

        return

    # --------------------------------------------------------
    # Detect new video
    # --------------------------------------------------------

    previous_video_id = (
        st.session_state.get(
            "video_id"
        )
    )

    if previous_video_id != file_id:

        reset_video_state()

    # --------------------------------------------------------
    # Build storage path
    # --------------------------------------------------------

    video_path = (
        UPLOAD_DIR
        / f"{file_id}_{safe_filename}"
    )

    # --------------------------------------------------------
    # Save uploaded video
    # --------------------------------------------------------

    try:

        if not video_path.exists():

            video_path.write_bytes(
                file_bytes
            )

    except Exception as error:

        st.error(
            f"Failed to save uploaded video: {error}"
        )

        return

    # --------------------------------------------------------
    # Video service
    # --------------------------------------------------------

    try:

        video_service = get_video_service()

    except Exception as error:

        st.error(
            f"Failed to initialize video service: {error}"
        )

        return

    # --------------------------------------------------------
    # Validate video
    # --------------------------------------------------------

    try:

        is_valid = (
            video_service.validate_video(
                video_path
            )
        )

    except Exception as error:

        st.error(
            f"Video validation failed: {error}"
        )

        return

    if not is_valid:

        st.error(
            "❌ The uploaded file could not be "
            "opened as a valid video."
        )

        return

    # ========================================================
    # Video Preview
    # ========================================================

    st.markdown(
        "### ▶️ Video Preview"
    )

    try:

        st.video(
            file_bytes
        )

    except Exception as error:

        st.warning(
            f"Video preview could not be displayed: {error}"
        )

    # ========================================================
    # Metadata
    # ========================================================

    try:

        with st.spinner(
            "Reading video metadata..."
        ):

            metadata = (
                video_service.get_metadata(
                    video_path
                )
            )

    except Exception as error:

        st.error(
            f"Unable to read video metadata: {error}"
        )

        return

    if not metadata:

        st.error(
            "No metadata was returned for this video."
        )

        return

    # --------------------------------------------------------
    # Store metadata
    # --------------------------------------------------------

    st.session_state[
        "video_path"
    ] = str(video_path)

    st.session_state[
        "video_id"
    ] = file_id

    st.session_state[
        "video_metadata"
    ] = metadata

    st.session_state["video_filename"] = uploaded_file.name

    st.session_state["video_file_size_mb"] = file_size_mb

    AnalysisService().update(
        file_id,
        video={
            "filename": uploaded_file.name,
            "file_size_mb": round(file_size_mb, 2),
            "metadata": metadata,
        },
    )

    # ========================================================
    # Video Information
    # ========================================================

    st.markdown(
        "### 📊 Video Information"
    )

    duration = metadata.get(
        "duration_seconds",
        0,
    )

    width = metadata.get(
        "width",
        0,
    )

    height = metadata.get(
        "height",
        0,
    )

    fps = metadata.get(
        "fps",
        0,
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Duration",
            format_duration(
                duration
            ),
        )

    with col2:

        st.metric(
            "Resolution",
            (
                f"{width} × "
                f"{height}"
            ),
        )

    with col3:

        st.metric(
            "FPS",
            f"{fps:.2f}"
            if isinstance(
                fps,
                (int, float),
            )
            else str(fps),
        )

    with col4:

        st.metric(
            "File Size",
            f"{file_size_mb:.2f} MB",
        )

    # ========================================================
    # Video Details
    # ========================================================

    with st.expander(
        "🔎 Video Details",
        expanded=False,
    ):

        detail_col1, detail_col2 = (
            st.columns(2)
        )

        with detail_col1:

            st.write(
                "**File name:**"
            )

            st.code(
                uploaded_file.name
            )

            st.write(
                "**Video ID:**"
            )

            st.code(
                file_id
            )

        with detail_col2:

            st.write(
                "**Stored path:**"
            )

            st.code(
                str(video_path)
            )

            st.write(
                "**Format:**"
            )

            st.code(
                Path(
                    uploaded_file.name
                ).suffix.lower()
            )

    # ========================================================
    # Frame Extraction
    # ========================================================

    st.divider()

    st.markdown(
        "### 🖼️ Key Frame Extraction"
    )

    st.caption(
        "Extract representative frames from the video "
        "for object detection, OCR, scene understanding, "
        "and visual analysis."
    )

    interval = st.slider(
        "Extract one frame every",
        min_value=1,
        max_value=30,
        value=5,
        step=1,
        format="%d seconds",
    )

    extract_button = st.button(
        "🖼️ Extract Key Frames",
        type="primary",
        width="stretch",
    )

    if extract_button:

        frame_output_directory = (
            FRAME_DIR / file_id
        )

        try:

            frame_output_directory.mkdir(
                parents=True,
                exist_ok=True,
            )

            with st.spinner(
                "Extracting key frames..."
            ):

                frames = (
                    video_service.extract_frames(
                        video_path=video_path,
                        output_directory=(
                            frame_output_directory
                        ),
                        interval_seconds=interval,
                    )
                )

            if frames is None:

                frames = []

            st.session_state[
                "video_frames"
            ] = frames

            AnalysisService().update(
                file_id,
                frames={"paths": [str(frame) for frame in frames]},
            )

            # Reset OCR when new frames are extracted
            st.session_state[
                "ocr_results"
            ] = []

            st.session_state[
                "ocr_completed"
            ] = False

            if frames:

                st.success(
                    f"✅ Successfully extracted "
                    f"{len(frames)} key frames."
                )

            else:

                st.warning(
                    "No frames were extracted."
                )

        except Exception as error:

            st.error(
                f"Frame extraction failed: {error}"
            )

    # ========================================================
    # Display Extracted Frames
    # ========================================================

    frames = st.session_state.get("video_frames", [])
    if not frames:
        saved_analysis = AnalysisService().load(file_id)
        saved_frames = saved_analysis.get("frames", {}).get("paths", [])
        if not saved_frames:
            saved_frames = [
                frame.get("frame_path", "")
                for frame in saved_analysis.get("vision", {}).get("frames", [])
                if isinstance(frame, dict)
            ]
        frames = [str(path) for path in saved_frames if Path(path).is_file()]
        if frames:
            st.session_state["video_frames"] = frames

    if frames:

        st.markdown(
            "#### 🖼️ Extracted Frames"
        )

        st.caption(
            f"{len(frames)} frame(s) extracted"
        )

        columns = st.columns(4)

        for index, frame_path in enumerate(
            frames
        ):

            with columns[index % 4]:

                try:

                    st.image(
                        str(frame_path),
                        width="stretch",
                        caption=(
                            f"Frame {index + 1}"
                        ),
                    )

                except Exception as error:

                    st.warning(
                        f"Could not display frame "
                        f"{index + 1}: {error}"
                    )

    # ========================================================
    # Computer Vision
    # ========================================================

    st.divider()
    st.markdown("### 👁️ Computer Vision")
    st.caption("Detect people and scene changes locally from extracted frames. It does not identify individuals.")

    if frames:
        if st.button("👁️ Analyze people & scenes", key="run_vision", width="stretch"):
            try:
                with st.spinner("Detecting people and scene changes..."):
                    vision_results = get_vision_service().analyze_frames(frames)
                st.session_state["vision_results"] = vision_results
                AnalysisService().update(file_id, vision=vision_results)
                AnalysisService().save_component(file_id, "vision", vision_results)
                st.success("Computer vision analysis completed.")
            except Exception as error:
                st.error(f"Computer vision analysis failed: {error}")

        vision_results = st.session_state.get("vision_results", {})
        if vision_results:
            vision_frames = vision_results.get("frames", [])
            people_frames = sum(1 for item in vision_frames if item.get("people_count", 0))
            scene_count = len(vision_results.get("scene_changes", []))
            metric_a, metric_b, metric_c = st.columns(3)
            metric_a.metric("Frames analyzed", len(vision_frames))
            metric_b.metric("Frames with people", people_frames)
            metric_c.metric("Scene changes", scene_count)
            with st.expander("View vision timeline"):
                for item in vision_frames:
                    st.write(f"{format_duration(item['timestamp_seconds'])}: {item['people_count']} person(s) detected")
    else:
        st.info("Extract frames to enable local computer vision.")

    # ========================================================
    # OCR Analysis
    # ========================================================

    st.divider()

    st.markdown(
        "### 🔤 OCR Text Detection"
    )

    st.caption(
        "Detect visible text inside the extracted "
        "video frames using PaddleOCR."
    )

    if not frames:

        st.info(
            "⏳ Extract video frames first, "
            "then run OCR."
        )

    else:

        st.write(
            f"Ready to analyze "
            f"**{len(frames)} frames**."
        )

        ocr_button = st.button(
            "🔍 Run OCR on Video Frames",
            type="primary",
            width="stretch",
        )

        if ocr_button:

            try:

                with st.spinner(
                    "Initializing PaddleOCR..."
                ):

                    ocr_service = (
                        get_ocr_service()
                    )

                with st.spinner(
                    f"Running OCR on "
                    f"{len(frames)} frames..."
                ):

                    ocr_results = (
                        ocr_service.process_frames(frames)
                    )

                if ocr_results is None:

                    ocr_results = []

                st.session_state[
                    "ocr_results"
                ] = ocr_results

                st.session_state[
                    "ocr_completed"
                ] = True

                timeline_service = TimelineService()
                ocr_path = timeline_service.save_ocr(
                    video_id=st.session_state["video_id"],
                    ocr_results=ocr_results,
                )
                timeline_path = timeline_service.save(
                    video_id=st.session_state["video_id"],
                    ocr_results=ocr_results,
                    transcript_segments=st.session_state.get(
                        "transcript_segments",
                        [],
                    ),
                )

                AnalysisService().update(
                    file_id,
                    ocr={"results": ocr_results},
                    transcript={
                        "segments": st.session_state.get("transcript_segments", []),
                        "text": st.session_state.get("transcript", ""),
                    },
                )

                text_frames = sum(
                    1
                    for result in ocr_results
                    if result.get("texts")
                )

                total_detections = sum(
                    len(
                        result.get("texts", [])
                    )
                    for result in ocr_results
                )

                st.success(
                    "✅ OCR analysis completed."
                )

                st.write(
                    f"Frames analyzed: "
                    f"**{len(ocr_results)}**"
                )

                st.write(
                    f"Frames containing text: "
                    f"**{text_frames}**"
                )

                st.write(
                    f"Total text detections: "
                    f"**{total_detections}**"
                )

                st.caption(
                    f"OCR saved to {ocr_path.name}; "
                    f"timeline saved to {timeline_path.name}"
                )

            except Exception as error:

                st.error(
                    f"OCR analysis failed: {error}"
                )

    # ========================================================
    # Display OCR Results
    # ========================================================

    ocr_results = st.session_state.get(
        "ocr_results",
        [],
    )

    if ocr_results:

        st.markdown(
            "#### 📝 Detected Text"
        )

        text_results = [
            result
            for result in ocr_results
            if result.get("texts")
        ]

        if not text_results:

            st.info(
                "No text was detected in the "
                "selected video frames."
            )

        else:

            for result in text_results:

                frame_number = result.get(
                    "frame_number",
                    0,
                )

                timestamp = result.get("timestamp_seconds", 0)

                detections = result.get("texts", [])
                text = "\n".join(
                    str(detection.get("text", ""))
                    for detection in detections
                    if detection.get("text")
                )

                with st.expander(
                    f"🕐 {format_duration(timestamp)} "
                    f"— Frame {frame_number}",
                    expanded=False,
                ):

                    st.write(
                        "**Detected text:**"
                    )

                    st.text(
                        text
                    )

                    if detections:

                        st.write(
                            "**Detections:**"
                        )

                        for detection in detections:

                            detected_text = (
                                detection.get(
                                    "text",
                                    "",
                                )
                            )

                            confidence = (
                                detection.get(
                                    "confidence",
                                    None,
                                )
                            )

                            if confidence is not None:

                                st.write(
                                    f"• {detected_text} "
                                    f"— confidence: "
                                    f"{confidence:.2%}"
                                )

                            else:

                                st.write(
                                    f"• {detected_text}"
                                )

    st.caption("Open 🧠 AI Summary from the sidebar to review the generated brief, key points, and important moments.")

    # ========================================================
    # Timeline Search
    # ========================================================

    video_id = st.session_state.get("video_id")

    if video_id and ocr_results:

        st.divider()
        st.markdown("#### ⏱️ Search OCR and Transcript by Time")

        search_col, window_col = st.columns(2)

        with search_col:

            search_time = st.number_input(
                "Timestamp (seconds)",
                min_value=0.0,
                value=0.0,
                step=1.0,
                key="timeline_search_time",
            )

        with window_col:

            search_window = st.number_input(
                "Search window (seconds)",
                min_value=0.0,
                value=5.0,
                step=1.0,
                key="timeline_search_window",
            )

        if st.button("Search timeline", width="stretch"):

            matches = TimelineService().search_by_time(
                video_id=video_id,
                timestamp_seconds=search_time,
                window_seconds=search_window,
            )

            st.write(
                f"Results around {format_duration(search_time)}"
            )

            ocr_matches = matches["ocr_results"]
            transcript_matches = matches["transcript_segments"]

            if ocr_matches:

                st.write("**On-screen text**")

                for match in ocr_matches:

                    st.write(
                        f"{match['timestamp']} — {match['text']}"
                    )

            if transcript_matches:

                st.write("**Spoken transcript**")

                for segment in transcript_matches:

                    st.write(
                        f"{format_duration(segment['start'])}–"
                        f"{format_duration(segment['end'])}: "
                        f"{segment['text']}"
                    )

            if not ocr_matches and not transcript_matches:

                st.info("No OCR or transcript content was found in this window.")

    # ========================================================
    # Analysis Status
    # ========================================================

    st.divider()

    st.markdown(
        "### 🚀 Analysis Pipeline"
    )

    pipeline_col1, pipeline_col2, pipeline_col3, pipeline_col4 = (
        st.columns(4)
    )

    with pipeline_col1:

        st.success(
            "✅ Video uploaded"
        )

    with pipeline_col2:

        st.success(
            "✅ Metadata extracted"
        )

    with pipeline_col3:

        if frames:

            st.success(
                "✅ Frames extracted"
            )

        else:

            st.info(
                "⏳ Frames pending"
            )

    with pipeline_col4:

        if st.session_state.get(
            "ocr_completed",
            False,
        ):

            st.success(
                "✅ OCR completed"
            )

        else:

            st.info(
                "⏳ OCR pending"
            )
