from pathlib import Path
import hashlib


def get_file_extension(filename: str) -> str:
    """Return file extension without dot."""

    return Path(filename).suffix.lower().replace(".", "")


def create_safe_filename(filename: str) -> str:
    """
    Create a safe filename while preserving extension.
    """

    path = Path(filename)

    stem = path.stem

    safe_stem = "".join(
        character
        if character.isalnum() or character in ("-", "_")
        else "_"
        for character in stem
    )

    return f"{safe_stem}{path.suffix.lower()}"


def generate_file_id(filename: str, file_bytes: bytes) -> str:
    """
    Generate deterministic ID based on filename + content.
    """

    content = filename.encode("utf-8") + file_bytes

    return hashlib.sha256(content).hexdigest()[:16]