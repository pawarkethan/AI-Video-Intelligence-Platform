from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from config.settings import OUTPUT_DIR, TRANSCRIPT_DIR
from services.education_service import EducationService


def render_education() -> None:
    st.title("🎓 Education Intelligence")
    st.caption("Turn a processed lecture or training video into notes, flashcards, and a self-check quiz.")
    video_id = st.session_state.get("video_id")
    if not video_id:
        st.info("Upload and process a video first.")
        return

    insights_path = OUTPUT_DIR / "insights" / f"{video_id}_insights.json"
    transcript_path = TRANSCRIPT_DIR / f"{video_id}.json"
    try:
        insights = json.loads(insights_path.read_text(encoding="utf-8"))
        transcript = json.loads(transcript_path.read_text(encoding="utf-8")).get("text", "")
    except (OSError, json.JSONDecodeError):
        st.info("Generate the transcript and AI Video Summary before creating learning materials.")
        return

    count_col, difficulty_col = st.columns(2)
    with count_col:
        count = st.slider("Quiz questions", min_value=3, max_value=15, value=5)
    with difficulty_col:
        difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"], index=1)

    saved = EducationService.load(video_id)
    if st.button("✨ Create learning pack", type="primary"):
        try:
            with st.spinner("Creating notes, flashcards, and quiz..."):
                saved = EducationService().generate(video_id, insights, transcript, count, difficulty)
            st.success("Learning pack created.")
        except Exception as error:
            st.error(f"Could not create learning pack: {error}")
            return

    if not saved:
        return
    st.subheader("📚 Lecture Notes")
    for section in saved.get("lecture_notes", []):
        with st.expander(section.get("heading", "Topic"), expanded=True):
            for point in section.get("points", []):
                st.markdown(f"- {point}")
    st.subheader("🎴 Flashcards")
    for card in saved.get("flashcards", []):
        with st.expander(card.get("front", "Question")):
            st.write(card.get("back", ""))
    st.subheader("📝 Quiz")
    for number, item in enumerate(saved.get("quiz", []), 1):
        answer = st.radio(f"{number}. {item.get('question', '')}", item.get("options", []), key=f"quiz_{video_id}_{number}")
        if st.button(f"Check answer {number}", key=f"check_{video_id}_{number}"):
            if answer == item.get("answer"):
                st.success("Correct!")
            else:
                st.error(f"Correct answer: {item.get('answer', '')}")
            st.caption(item.get("explanation", ""))
