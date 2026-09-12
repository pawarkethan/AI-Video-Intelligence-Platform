from __future__ import annotations

import os
from pathlib import Path
from typing import Any


# PaddleX enables oneDNN (MKL-DNN) by default.  PaddlePaddle 3.3 on Windows
# currently cannot execute the OCR v6 model's PIR graph with that backend.
# Keep the portable CPU executor as the default, while allowing deployments
# with a compatible oneDNN build to explicitly override this environment key.
os.environ.setdefault("PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT", "False")


class OCRService:
    """
    OCR service using PaddleOCR.

    This service supports:
    - OCR on a single image
    - OCR on multiple video frames
    - Confidence filtering
    - Bounding-box extraction
    - Combined text generation
    """

    # ========================================================
    # Initialization
    # ========================================================

    def __init__(
        self,
        language: str = "en",
        confidence_threshold: float = 0.50,
    ):
        self.language = language
        self.confidence_threshold = confidence_threshold

        print("=" * 60)
        print("Initializing PaddleOCR")
        print("=" * 60)

        # ----------------------------------------------------
        # Import PaddleOCR
        # ----------------------------------------------------

        try:

            from paddleocr import PaddleOCR

        except ImportError as error:

            raise ImportError(
                "PaddleOCR is not installed.\n"
                "Install it using:\n"
                "pip install paddleocr"
            ) from error

        # ----------------------------------------------------
        # Initialize PaddleOCR
        # ----------------------------------------------------
        #
        # We disable document-specific preprocessing because
        # our main use case is OCR on video frames.
        #
        # Video frames generally do not need:
        # - document orientation classification
        # - document unwarping
        # - text-line orientation classification
        #
        # This also avoids unnecessary model loading.
        # ----------------------------------------------------

        try:

            self.ocr = PaddleOCR(
                lang=self.language,
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
            )

        except Exception as error:

            raise RuntimeError(
                f"Failed to initialize PaddleOCR: {error}"
            ) from error

        print(
            "PaddleOCR initialized successfully."
        )

        print("=" * 60)

    # ========================================================
    # Single Image OCR
    # ========================================================

    def extract_text(
        self,
        image_path: str | Path,
    ) -> list[dict[str, Any]]:
        """
        Extract text from a single image.

        Returns:

        [
            {
                "text": "Hello World",
                "confidence": 0.98,
                "bbox": [...]
            }
        ]
        """

        image_path = Path(image_path)

        # ----------------------------------------------------
        # Validate image
        # ----------------------------------------------------

        if not image_path.exists():

            raise FileNotFoundError(
                f"Image file not found: {image_path}"
            )

        if not image_path.is_file():

            raise ValueError(
                f"Image path is not a file: {image_path}"
            )

        # ----------------------------------------------------
        # Run OCR
        # ----------------------------------------------------

        try:

            results = self.ocr.predict(
                str(image_path)
            )

        except Exception as error:

            raise RuntimeError(
                f"OCR failed for "
                f"{image_path}: {error}"
            ) from error

        # ----------------------------------------------------
        # Parse results
        # ----------------------------------------------------

        return self._parse_results(
            results
        )

    # ========================================================
    # Parse PaddleOCR Results
    # ========================================================

    def _parse_results(
        self,
        results: Any,
    ) -> list[dict[str, Any]]:
        """
        Convert PaddleOCR output into a simple
        application-friendly structure.
        """

        detections: list[
            dict[str, Any]
        ] = []

        if results is None:

            return detections

        # ----------------------------------------------------
        # PaddleOCR 3.x returns an iterable result object.
        # ----------------------------------------------------

        try:

            for result in results:

                # --------------------------------------------
                # Result may expose JSON-style data
                # --------------------------------------------

                data = None

                if hasattr(
                    result,
                    "json",
                ):

                    try:

                        data = result.json

                        if callable(data):

                            data = data()

                    except Exception:

                        data = None

                # --------------------------------------------
                # If JSON data is available
                # --------------------------------------------

                if isinstance(
                    data,
                    dict,
                ):

                    self._extract_from_dict(
                        data,
                        detections,
                    )

                    continue

                # --------------------------------------------
                # Try direct dictionary access
                # --------------------------------------------

                if isinstance(
                    result,
                    dict,
                ):

                    self._extract_from_dict(
                        result,
                        detections,
                    )

                    continue

        except Exception:

            # Some PaddleOCR versions expose
            # result objects differently.
            #
            # We don't want parsing errors to crash
            # the entire application.

            pass

        return detections

    # ========================================================
    # Dictionary Result Parser
    # ========================================================

    def _extract_from_dict(
        self,
        data: dict[str, Any],
        detections: list[dict[str, Any]],
    ) -> None:
        """
        Extract OCR detections from PaddleOCR
        dictionary-style results.
        """

        # PaddleOCR 3.x serializes its result as {"res": {...}}.
        # The actual recognition fields live in that nested dictionary.
        # Older versions expose the fields at the top level, so support both
        # shapes without changing the public service API.
        nested_result = data.get("res")

        if isinstance(nested_result, dict):

            data = nested_result

        # ----------------------------------------------------
        # PaddleOCR commonly uses:
        #
        # rec_texts
        # rec_scores
        # rec_polys / dt_polys
        # ----------------------------------------------------

        texts = data.get(
            "rec_texts",
            [],
        )

        scores = data.get(
            "rec_scores",
            [],
        )

        boxes = data.get(
            "rec_polys",
            data.get(
                "dt_polys",
                [],
            ),
        )

        # ----------------------------------------------------
        # Make sure values are lists
        # ----------------------------------------------------

        if texts is None:

            texts = []

        if scores is None:

            scores = []

        if boxes is None:

            boxes = []

        # ----------------------------------------------------
        # Convert numpy arrays if necessary
        # ----------------------------------------------------

        try:

            texts = list(texts)

        except Exception:

            texts = []

        try:

            scores = list(scores)

        except Exception:

            scores = []

        try:

            boxes = list(boxes)

        except Exception:

            boxes = []

        # ----------------------------------------------------
        # Process detections
        # ----------------------------------------------------

        for index, text in enumerate(
            texts
        ):

            if text is None:

                continue

            text = str(text).strip()

            if not text:

                continue

            # ----------------------------------------------
            # Confidence
            # ----------------------------------------------

            confidence = 0.0

            if index < len(scores):

                try:

                    confidence = float(
                        scores[index]
                    )

                except (
                    TypeError,
                    ValueError,
                ):

                    confidence = 0.0

            # ----------------------------------------------
            # Confidence filtering
            # ----------------------------------------------

            if (
                confidence
                < self.confidence_threshold
            ):

                continue

            # ----------------------------------------------
            # Bounding box
            # ----------------------------------------------

            bbox = None

            if index < len(boxes):

                try:

                    bbox = (
                        boxes[index].tolist()
                        if hasattr(
                            boxes[index],
                            "tolist",
                        )
                        else boxes[index]
                    )

                except Exception:

                    bbox = None

            # ----------------------------------------------
            # Store detection
            # ----------------------------------------------

            detections.append(
                {
                    "text": text,
                    "confidence": round(
                        confidence,
                        4,
                    ),
                    "bbox": bbox,
                }
            )

    # ========================================================
    # OCR Multiple Frames
    # ========================================================

    def process_frames(
        self,
        frame_paths: list[str | Path],
    ) -> list[dict[str, Any]]:
        """
        Run OCR on multiple video frames.

        Returns:

        [
            {
                "frame_index": 0,
                "frame_path": "...",
                "texts": [...]
            }
        ]
        """

        results: list[
            dict[str, Any]
        ] = []

        for index, frame_path in enumerate(
            frame_paths
        ):

            frame_path = Path(
                frame_path
            )

            try:

                detections = (
                    self.extract_text(
                        frame_path
                    )
                )

                results.append(
                    {
                        "frame_index": index,
                        "frame_path": str(
                            frame_path
                        ),
                        "texts": detections,
                    }
                )

            except Exception as error:

                results.append(
                    {
                        "frame_index": index,
                        "frame_path": str(
                            frame_path
                        ),
                        "texts": [],
                        "error": str(error),
                    }
                )

        return results

    # ========================================================
    # Combined Text
    # ========================================================

    def get_combined_text(
        self,
        frame_results: list[
            dict[str, Any]
        ],
    ) -> str:
        """
        Combine OCR text from multiple frames.
        """

        all_text: list[str] = []

        for frame in frame_results:

            texts = frame.get(
                "texts",
                [],
            )

            for item in texts:

                text = item.get(
                    "text",
                    "",
                )

                text = str(
                    text
                ).strip()

                if text:

                    all_text.append(
                        text
                    )

        return "\n".join(
            all_text
        )

    # ========================================================
    # Remove Duplicate Text
    # ========================================================

    def get_unique_text(
        self,
        frame_results: list[
            dict[str, Any]
        ],
    ) -> str:
        """
        Return unique OCR text while preserving order.
        """

        seen: set[str] = set()

        unique_text: list[str] = []

        for frame in frame_results:

            texts = frame.get(
                "texts",
                [],
            )

            for item in texts:

                text = str(
                    item.get(
                        "text",
                        "",
                    )
                ).strip()

                if not text:

                    continue

                normalized = (
                    text.lower()
                )

                if normalized in seen:

                    continue

                seen.add(
                    normalized
                )

                unique_text.append(
                    text
                )

        return "\n".join(
            unique_text
        )

    # ========================================================
    # OCR Summary
    # ========================================================

    def get_summary(
        self,
        frame_results: list[
            dict[str, Any]
        ],
    ) -> dict[str, Any]:
        """
        Generate a summary of OCR processing.
        """

        total_frames = len(
            frame_results
        )

        frames_with_text = 0
        total_detections = 0

        for frame in frame_results:

            texts = frame.get(
                "texts",
                [],
            )

            if texts:

                frames_with_text += 1

                total_detections += len(
                    texts
                )

        return {
            "total_frames": total_frames,
            "frames_with_text": (
                frames_with_text
            ),
            "frames_without_text": (
                total_frames
                - frames_with_text
            ),
            "total_detections": (
                total_detections
            ),
        }
