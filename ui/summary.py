from __future__ import annotations

import streamlit as st

from services.analysis_service import AnalysisService
from services.timeline_service import TimelineService
from ui.insights import render_video_insights


def render_summary() -> None:
    """Render the saved, long-form intelligence brief on its own page."""

    st.markdown("## 🧠 AI Video Summary")
    st.caption("Review the intelligence brief without scrolling through the video-processing tools.")

    video_id = st.session_state.get("video_id")
    if not video_id:
        st.info("Upload a video and generate a transcript or OCR results first.")
        return

    analysis = AnalysisService().load(video_id)
    video_metadata = st.session_state.get("video_metadata") or analysis.get(
        "video", {}
    ).get("metadata", {})
    timeline = TimelineService().load(video_id)
    transcript = st.session_state.get("transcript_segments", []) or timeline.get(
        "transcript_segments", []
    )
    ocr_results = st.session_state.get("ocr_results", []) or timeline.get(
        "ocr_results", []
    )

    render_video_insights(
        video_id=video_id,
        transcript=transcript,
        ocr_results=ocr_results,
        video_metadata=video_metadata,
    )
