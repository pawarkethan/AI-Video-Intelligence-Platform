from __future__ import annotations

import csv
import io
import json
from typing import Any


class ExportService:
    """Create portable JSON, CSV, TXT, and lightweight PDF analysis reports."""

    @staticmethod
    def json_bytes(analysis: dict[str, Any]) -> bytes:
        return json.dumps(analysis, ensure_ascii=False, indent=2).encode("utf-8")

    @staticmethod
    def txt_bytes(analysis: dict[str, Any]) -> bytes:
        insights = analysis.get("insights", {})
        lines = ["AI VIDEO INTELLIGENCE REPORT", "", f"Video ID: {analysis.get('video_id', '')}", ""]
        lines.extend(["SUMMARY", insights.get("short_summary", insights.get("summary", "")), ""])
        lines.append("KEY POINTS")
        lines.extend(f"- {point}" for point in insights.get("key_points", []))
        lines.extend(["", "IMPORTANT MOMENTS"])
        lines.extend(f"- {moment.get('timestamp_seconds', 0):.0f}s: {moment.get('title', '')}" for moment in insights.get("important_moments", []))
        return "\n".join(lines).encode("utf-8")

    @staticmethod
    def csv_bytes(analysis: dict[str, Any]) -> bytes:
        output = io.StringIO(newline="")
        writer = csv.DictWriter(output, fieldnames=["timestamp_seconds", "type", "text", "confidence"])
        writer.writeheader()
        for segment in analysis.get("transcript", {}).get("segments", []):
            writer.writerow({"timestamp_seconds": segment.get("start", 0), "type": "transcript", "text": segment.get("text", ""), "confidence": ""})
        for item in analysis.get("ocr", {}).get("results", []):
            writer.writerow({"timestamp_seconds": item.get("timestamp_seconds", 0), "type": "ocr", "text": item.get("text", ""), "confidence": ""})
        for frame in analysis.get("vision", {}).get("frames", []):
            writer.writerow({"timestamp_seconds": frame.get("timestamp_seconds", 0), "type": "vision_people", "text": f"{frame.get('people_count', 0)} person(s)", "confidence": ""})
        return output.getvalue().encode("utf-8")

    @classmethod
    def pdf_bytes(cls, analysis: dict[str, Any]) -> bytes:
        # A standards-compliant, dependency-free text PDF for sharing reports.
        text = cls.txt_bytes(analysis).decode("utf-8", errors="replace")
        lines = [line.encode("latin-1", errors="replace").decode("latin-1")[:100] for line in text.splitlines()]
        stream = "BT /F1 11 Tf 50 790 Td 15 TL " + " ".join(f"({cls._escape(line)}) Tj T*" for line in lines) + " ET"
        objects = [
            "<< /Type /Catalog /Pages 2 0 R >>",
            "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
            f"<< /Length {len(stream.encode('latin-1'))} >>\nstream\n{stream}\nendstream",
            "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        ]
        document = "%PDF-1.4\n"
        offsets = [0]
        for index, object_value in enumerate(objects, 1):
            offsets.append(len(document.encode("latin-1")))
            document += f"{index} 0 obj\n{object_value}\nendobj\n"
        xref = len(document.encode("latin-1"))
        document += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n"
        document += "".join(f"{offset:010d} 00000 n \n" for offset in offsets[1:])
        document += f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF"
        return document.encode("latin-1")

    @staticmethod
    def _escape(value: str) -> str:
        return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
