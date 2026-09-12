from __future__ import annotations

import streamlit as st

from services.analysis_service import AnalysisService
from services.export_service import ExportService


def render_exports() -> None:
    st.title("📤 Reports & Export")
    st.caption("Download one portable record of the video analysis in the format your audience needs.")
    video_id = st.session_state.get("video_id")
    if not video_id:
        st.info("Upload a video first.")
        return
    analysis = AnalysisService().load(video_id)
    if len(analysis) <= 1:
        st.info("Process the video first; exports appear once analysis data is available.")
        return
    service = ExportService()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.download_button("Download JSON", service.json_bytes(analysis), f"{video_id}_analysis.json", "application/json", width="stretch")
    with col2:
        st.download_button("Download TXT", service.txt_bytes(analysis), f"{video_id}_report.txt", "text/plain", width="stretch")
    with col3:
        st.download_button("Download CSV", service.csv_bytes(analysis), f"{video_id}_timeline.csv", "text/csv", width="stretch")
    with col4:
        st.download_button("Download PDF", service.pdf_bytes(analysis), f"{video_id}_report.pdf", "application/pdf", width="stretch")
    st.subheader("Master analysis record")
    st.json(analysis)
