import streamlit as st


def load_global_theme():
    st.markdown(
        """
        <style>

        .stApp {
            background:
                radial-gradient(
                    circle at top right,
                    #172554 0%,
                    #0f172a 35%,
                    #020617 100%
                );

            color: #f8fafc;
        }

        .hero-section {
            padding: 40px 20px;
            text-align: center;
            margin-bottom: 30px;
        }

        .hero-badge {
            display: inline-block;
            padding: 7px 16px;
            border-radius: 999px;

            background: rgba(59, 130, 246, 0.15);
            border: 1px solid rgba(96, 165, 250, 0.35);

            color: #60a5fa;
            font-size: 13px;
            font-weight: 700;

            margin-bottom: 18px;
        }

        .hero-section h1 {
            font-size: 48px;
            font-weight: 800;

            background: linear-gradient(
                90deg,
                #60a5fa,
                #a78bfa,
                #22d3ee
            );

            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;

            margin-bottom: 10px;
        }

        .hero-description {
            color: #94a3b8;
            font-size: 19px;
            max-width: 800px;
            margin: auto;
        }

        .feature-card {
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid rgba(148, 163, 184, 0.15);

            border-radius: 18px;
            padding: 25px;

            min-height: 210px;

            transition: 0.2s ease;
        }

        .feature-card:hover {
            border-color: rgba(96, 165, 250, 0.5);
            transform: translateY(-3px);
        }

        .feature-icon {
            font-size: 38px;
            margin-bottom: 12px;
        }

        .feature-card h3 {
            color: #f8fafc;
        }

        .feature-card p {
            color: #94a3b8;
            line-height: 1.6;
        }

        .pipeline-card {
            text-align: center;

            padding: 20px 10px;

            background: rgba(15, 23, 42, 0.75);
            border: 1px solid rgba(148, 163, 184, 0.12);

            border-radius: 16px;
        }

        .pipeline-icon {
            font-size: 30px;
            margin-bottom: 8px;
        }

        .pipeline-card strong {
            display: block;
            color: #f8fafc;
            margin-bottom: 5px;
        }

        .pipeline-card small {
            color: #94a3b8;
        }

        .domain-card {
            text-align: center;

            padding: 18px 8px;

            background: rgba(15, 23, 42, 0.7);

            border: 1px solid rgba(148, 163, 184, 0.12);

            border-radius: 14px;

            color: #e2e8f0;
        }

        .domain-card div {
            font-size: 28px;
            margin-bottom: 7px;
        }

        .getting-started {
            padding: 30px;

            border-radius: 20px;

            background:
                linear-gradient(
                    135deg,
                    rgba(37, 99, 235, 0.12),
                    rgba(124, 58, 237, 0.12)
                );

            border: 1px solid rgba(96, 165, 250, 0.2);

            margin-top: 20px;
        }

        .getting-started h2 {
            color: #f8fafc;
        }

        .getting-started p,
        .getting-started li {
            color: #cbd5e1;
            line-height: 1.8;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )


def render_app_header():
    st.markdown(
        """
        <div style="
            padding: 10px 0 20px 0;
            border-bottom: 1px solid rgba(148,163,184,0.12);
            margin-bottom: 20px;
        ">
            <div style="
                font-size: 15px;
                color: #64748b;
                font-weight: 600;
            ">
                AI VIDEO INTELLIGENCE PLATFORM
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )