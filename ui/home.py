from __future__ import annotations

import textwrap

import streamlit as st


# ============================================================
# HTML helper
# ============================================================

def render_html(html: str) -> None:
    """
    Render a layout fragment without sending it through Markdown.

    ``st.markdown`` parses leading indentation as a Markdown code block.
    Since the page markup contains nested, indented elements, that caused
    the browser to show the literal ``<div>`` tags instead of the UI.
    """
    st.html(textwrap.dedent(html).strip())


# ============================================================
# Home Page
# ============================================================

def render_home() -> None:
    """Render the AI Video Intelligence Platform dashboard."""

    # ========================================================
    # Hero Section
    # ========================================================

    render_html(
        """
        <div class="hero-section">

            <div class="hero-icon">
                🎥
            </div>

            <div class="hero-badge">
                🎥 &nbsp; MULTIMODAL AI PLATFORM
            </div>

            <h1 class="hero-title">
                AI Video Intelligence Platform
            </h1>

            <p class="hero-description">
                Understand videos using Computer Vision,
                Speech AI, OCR, and Large Language Models.
            </p>

        </div>
        """
    )

    # ========================================================
    # What Can This Platform Do?
    # ========================================================

    st.markdown(
        "## 🚀 What can this platform do?"
    )

    render_html(
        """
        <div class="features-grid">

            <!-- Video Understanding -->

            <div class="feature-card">

                <div class="feature-icon">
                    🎥
                </div>

                <h3>
                    Video Understanding
                </h3>

                <p>
                    Analyze video frames to detect objects,
                    people, activities, and important events.
                </p>

            </div>


            <!-- Speech Intelligence -->

            <div class="feature-card">

                <div class="feature-icon">
                    🎙️
                </div>

                <h3>
                    Speech Intelligence
                </h3>

                <p>
                    Transcribe spoken content, generate captions,
                    detect languages, and analyze conversations.
                </p>

            </div>


            <!-- AI Reasoning -->

            <div class="feature-card">

                <div class="feature-icon">
                    🧠
                </div>

                <h3>
                    AI Reasoning
                </h3>

                <p>
                    Use Large Language Models to summarize videos
                    and answer natural-language questions.
                </p>

            </div>


            <!-- OCR Intelligence -->

            <div class="feature-card">

                <div class="feature-icon">
                    📝
                </div>

                <h3>
                    OCR Intelligence
                </h3>

                <p>
                    Extract and understand text appearing inside
                    video frames using Optical Character Recognition.
                </p>

            </div>


            <!-- Education Intelligence -->

            <div class="feature-card">

                <div class="feature-icon">
                    🎓
                </div>

                <h3>
                    Education Intelligence
                </h3>

                <p>
                    Convert lectures into notes, summaries,
                    quizzes, and automatically generated MCQs.
                </p>

            </div>

        </div>
        """
    )

    # ========================================================
    # Multimodal Processing Pipeline
    # ========================================================

    st.markdown("---")

    st.markdown(
        "## ⚙️ Multimodal Processing Pipeline"
    )

    st.write(
        "The platform combines multiple AI technologies "
        "to understand every part of a video."
    )

    render_html(
        """
        <div class="pipeline-grid">

            <!-- Step 1 -->

            <div class="pipeline-card">

                <div class="pipeline-number">
                    01
                </div>

                <h4>
                    🎥 Video
                </h4>

                <p>
                    Frames, objects, people, activities
                </p>

            </div>


            <!-- Step 2 -->

            <div class="pipeline-card">

                <div class="pipeline-number">
                    02
                </div>

                <h4>
                    🎙️ Audio
                </h4>

                <p>
                    Speech, captions, speakers
                </p>

            </div>


            <!-- Step 3 -->

            <div class="pipeline-card">

                <div class="pipeline-number">
                    03
                </div>

                <h4>
                    📝 Text
                </h4>

                <p>
                    OCR, transcripts, metadata
                </p>

            </div>


            <!-- Step 4 -->

            <div class="pipeline-card">

                <div class="pipeline-number">
                    04
                </div>

                <h4>
                    🧠 AI
                </h4>

                <p>
                    Reasoning, summaries, Q&A
                </p>

            </div>

        </div>
        """
    )

    # ========================================================
    # AI Technology Stack
    # ========================================================

    st.markdown("---")

    render_html(
        """
        <div class="technology-section">

            <h2>
                🧩 AI Technology Stack
            </h2>

            <p>
                <span class="tech-item">Computer Vision</span>
                <span class="tech-separator">•</span>

                <span class="tech-item">Speech AI</span>
                <span class="tech-separator">•</span>

                <span class="tech-item">OCR</span>
                <span class="tech-separator">•</span>

                <span class="tech-item">LLMs</span>
                <span class="tech-separator">•</span>

                <span class="tech-item">Multimodal AI</span>
            </p>

        </div>
        """
    )

    with st.expander("Inspect the technologies used in this project"):
        st.dataframe(
            [
                {"Technology": "Streamlit", "Used for": "Web interface, navigation, widgets, and session state"},
                {"Technology": "OpenCV", "Used for": "Video metadata, frame extraction, people detection, and scene changes"},
                {"Technology": "FFmpeg", "Used for": "Audio-stream inspection and WAV audio extraction"},
                {"Technology": "Faster-Whisper", "Used for": "Timestamped speech-to-text transcription"},
                {"Technology": "PaddleOCR", "Used for": "On-screen text detection in extracted frames"},
                {"Technology": "Google Gemini", "Used for": "Evidence-grounded summaries, Q&A, and education content"},
            ],
            hide_index=True,
            width="stretch",
        )

    # ========================================================
    # Supported Intelligence Domains
    # ========================================================

    st.markdown("---")

    st.markdown(
        "## 🌐 Supported Intelligence Domains"
    )

    render_html(
        """
        <div class="domains-grid">

            <!-- Education -->

            <div class="domain-card">

                <div class="domain-icon">
                    🎓
                </div>

                <h4>
                    Education
                </h4>

                <p>
                    Lecture analysis, notes, quizzes and MCQs.
                </p>

            </div>


            <!-- Meetings -->

            <div class="domain-card">

                <div class="domain-icon">
                    🏢
                </div>

                <h4>
                    Meetings
                </h4>

                <p>
                    Transcripts, summaries and action items.
                </p>

            </div>


            <!-- Sports -->

            <div class="domain-card">

                <div class="domain-icon">
                    🏟️
                </div>

                <h4>
                    Sports
                </h4>

                <p>
                    Events, players and important moments.
                </p>

            </div>


            <!-- Retail -->

            <div class="domain-card">

                <div class="domain-icon">
                    🛍️
                </div>

                <h4>
                    Retail
                </h4>

                <p>
                    Customer activity and store intelligence.
                </p>

            </div>


            <!-- Surveillance -->

            <div class="domain-card">

                <div class="domain-icon">
                    🔐
                </div>

                <h4>
                    Surveillance
                </h4>

                <p>
                    Activity and event detection.
                </p>

            </div>

        </div>
        """
    )

    # ========================================================
    # Footer
    # ========================================================

    st.markdown("---")

    render_html(
        """
        <div class="platform-footer">

            <p>
                🎥 <strong>AI Video Intelligence Platform</strong>
            </p>

            <span>
                Computer Vision
                &nbsp;•&nbsp;
                Speech AI
                &nbsp;•&nbsp;
                OCR
                &nbsp;•&nbsp;
                LLMs
                &nbsp;•&nbsp;
                Multimodal AI
            </span>

        </div>
        """
    )
