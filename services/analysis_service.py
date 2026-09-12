from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config.settings import OUTPUT_DIR


class AnalysisService:
    """Own the master, portable analysis record for one video."""

    def get_directory(self, video_id: str) -> Path:
        directory = OUTPUT_DIR / video_id
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def get_path(self, video_id: str) -> Path:
        return self.get_directory(video_id) / "analysis.json"

    def load(self, video_id: str) -> dict[str, Any]:
        path = self.get_path(video_id)
        if not path.exists():
            return {"video_id": video_id}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"video_id": video_id}

    def update(self, video_id: str, **components: Any) -> dict[str, Any]:
        analysis = self.load(video_id)
        analysis.update({key: value for key, value in components.items() if value is not None})
        analysis["video_id"] = video_id
        analysis["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._write(self.get_path(video_id), analysis)
        return analysis

    def save_component(self, video_id: str, name: str, value: Any) -> Path:
        path = self.get_directory(video_id) / f"{name}.json"
        self._write(path, value)
        return path

    @staticmethod
    def _write(path: Path, value: Any) -> None:
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(path)
