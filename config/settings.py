from __future__ import annotations

from pathlib import Path


# ============================================================
# Application
# ============================================================

APP_NAME = "AI Video Intelligence Platform"


# ============================================================
# Project Root
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# Main Data Directory
# ============================================================

DATA_DIR = BASE_DIR / "data"


# ============================================================
# Data Subdirectories
# ============================================================

UPLOAD_DIR = DATA_DIR / "uploads"

FRAME_DIR = DATA_DIR / "frames"

AUDIO_DIR = DATA_DIR / "audio"

TRANSCRIPT_DIR = DATA_DIR / "transcripts"

OCR_DIR = DATA_DIR / "ocr"

OUTPUT_DIR = DATA_DIR / "outputs"

CACHE_DIR = DATA_DIR / "cache"


# ============================================================
# Other Project Directories
# ============================================================

MODELS_DIR = BASE_DIR / "models"

TEMP_DIR = BASE_DIR / "temp"


# ============================================================
# Video Settings
# ============================================================

DEFAULT_FRAME_INTERVAL = 5

MAX_VIDEO_SIZE_MB = 500


SUPPORTED_VIDEO_FORMATS = [
    "mp4",
    "mov",
    "avi",
    "mkv",
    "webm",
    "mpeg",
    "mpg",
]


# ============================================================
# Directory Validation
# ============================================================

def _ensure_directory(directory: Path) -> None:
    """
    Safely create a directory.

    Raises a clear error if a file exists at the
    location where a directory is expected.
    """

    if directory.exists():

        if not directory.is_dir():

            raise RuntimeError(
                "\n"
                "==================================================\n"
                "DIRECTORY CONFIGURATION ERROR\n"
                "==================================================\n"
                f"Expected directory:\n"
                f"{directory}\n\n"
                "A file or invalid filesystem object already "
                "exists at this location.\n\n"
                "Please remove or rename that object and run "
                "the application again.\n"
                "=================================================="
            )

        return

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )


# ============================================================
# Initialize Directories
# ============================================================

def initialize_directories() -> None:
    """
    Create all directories required by the application.
    """

    directories = [
        DATA_DIR,
        UPLOAD_DIR,
        FRAME_DIR,
        AUDIO_DIR,
        TRANSCRIPT_DIR,
        OCR_DIR,
        OUTPUT_DIR,
        CACHE_DIR,
        MODELS_DIR,
        TEMP_DIR,
    ]

    for directory in directories:

        _ensure_directory(
            directory
        )


# ============================================================
# Project Information
# ============================================================

def get_project_info() -> dict:

    return {
        "base_dir": str(BASE_DIR),
        "data_dir": str(DATA_DIR),
        "upload_dir": str(UPLOAD_DIR),
        "frame_dir": str(FRAME_DIR),
        "audio_dir": str(AUDIO_DIR),
        "transcript_dir": str(
            TRANSCRIPT_DIR
        ),
        "ocr_dir": str(OCR_DIR),
        "output_dir": str(
            OUTPUT_DIR
        ),
        "cache_dir": str(
            CACHE_DIR
        ),
        "models_dir": str(
            MODELS_DIR
        ),
        "temp_dir": str(
            TEMP_DIR
        ),
    }
