from __future__ import annotations

from typing import Any

import streamlit as st

from services.insights_service import VideoInsightsService


def format_timestamp(seconds: float) -> str:
    total = max(0, int(seconds))
    return f"{total // 60:02d}:{total % 60:02d}"


def render_video_insights(
    video_id: str,
    transcript: Any,
    ocr_results: Any,
    video_metadata: dict[str, Any],
) -> None:
    """Render the saved or newly generated intelligence brief for one video."""

    st.divider()
    st.markdown("## 🧠 AI Video Summary")
    st.caption("A structured intelligence brief grounded in the processed video evidence.")

    try:
        service = VideoInsightsService()
    except RuntimeError as error:
        st.info(f"Add GEMINI_API_KEY to enable automatic insights. {error}")
        return

    saved_insights = service.load(video_id)
    has_evidence = bool(transcript or ocr_results)
    auto_generation_key = f"insights_generated_{video_id}"
    should_auto_generate = bool(
        transcript
        and not saved_insights
        and not st.session_state.get(auto_generation_key, False)
    )

    header_col, action_col = st.columns([4, 1])
    with header_col:
        if saved_insights:
            st.caption("Saved analysis is available for this video.")
        elif has_evidence:
            st.caption("Transcript/OCR evidence is ready for an intelligence brief.")
        else:
            st.caption("Complete transcript or OCR processing to unlock automatic insights.")

    with action_col:
        generate = st.button(
            "✨ Generate" if not saved_insights else "↻ Refresh",
            key=f"generate_insights_{video_id}",
            type="primary",
            disabled=not has_evidence,
            width="stretch",
        )

    if should_auto_generate:
        st.caption("Transcript detected — creating the first intelligence brief automatically.")

    if generate or should_auto_generate:
        try:
            with st.spinner("Synthesizing summary, topics, and important moments..."):
                saved_insights = service.generate(
                    video_id=video_id,
                    transcript=transcript,
                    ocr_results=ocr_results,
                    video_metadata=video_metadata,
                )
            st.session_state[auto_generation_key] = True
            st.success("AI video insights generated and saved.")
        except Exception as error:
            if service._is_temporary_model_error(error):
                st.warning(
                    "The AI service is temporarily busy. We retried automatically; "
                    "please use Generate again in a moment."
                )
            else:
                st.error(f"Unable to generate insights: {error}")
            return

    if not saved_insights:
        return

    st.markdown(
        f'<div class="insight-summary-card">{saved_insights.get("short_summary") or saved_insights.get("summary") or "No summary was returned."}</div>',
        unsafe_allow_html=True,
    )

    detailed_summary = saved_insights.get("detailed_summary")
    if detailed_summary:
        with st.expander("Read detailed summary", expanded=False):
            st.write(detailed_summary)

    key_col, topic_col = st.columns([3, 2])
    with key_col:
        st.markdown("### 📌 Key Points")
        for point in saved_insights.get("key_points", []):
            st.markdown(f"<div class='insight-list-item'>✦ {point}</div>", unsafe_allow_html=True)
    with topic_col:
        st.markdown("### 🏷️ Topics & Keywords")
        badges = saved_insights.get("topics", []) + saved_insights.get("keywords", [])
        st.markdown(
            " ".join(f"<span class='insight-tag'>{badge}</span>" for badge in badges),
            unsafe_allow_html=True,
        )

    concepts = saved_insights.get("important_concepts", [])
    if concepts:
        st.markdown("### 💡 Important Concepts")
        for concept in concepts:
            st.markdown(f"<div class='insight-list-item'>◈ {concept}</div>", unsafe_allow_html=True)

    st.markdown("### ⏱️ Important Moments")
    moments = saved_insights.get("important_moments", [])
    if moments:
        for moment in moments:
            time_col, moment_col = st.columns([1, 7])
            with time_col:
                st.markdown(
                    f"<div class='moment-time'>{format_timestamp(moment['timestamp_seconds'])}</div>",
                    unsafe_allow_html=True,
                )
            with moment_col:
                st.markdown(f"**{moment['title']}**")
                if moment.get("description"):
                    st.caption(moment["description"])
    else:
        st.info("No timestamped moments could be grounded in the available evidence.")

    actions = saved_insights.get("action_items", [])
    if actions:
        st.markdown("### ✅ Action Items")
        for action in actions:
            st.markdown(f"<div class='insight-list-item'>☐ {action}</div>", unsafe_allow_html=True)
