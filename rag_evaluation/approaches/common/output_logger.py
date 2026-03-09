"""
Standardized output logging for RAG approach results.

Handles serialization of :class:`ApproachOutput` to JSON files in the
outputs directory, with consistent naming conventions and pretty-printing.

Usage:
    >>> from approaches.common.output_logger import OutputLogger
    >>> logger = OutputLogger(outputs_dir="outputs")
    >>> logger.save(approach_output)  # writes outputs/lightrag_2025-02-23T10-30-00.json
"""

from __future__ import annotations

import json
import os
from datetime import datetime

from approaches.common.schemas import ApproachOutput


class OutputLogger:
    """Writes RAG approach results to structured JSON files.

    Each run produces a timestamped JSON file in the outputs directory,
    enabling multiple runs of the same approach to be stored and compared.

    Attributes:
        outputs_dir: Directory where output JSON files are written.
    """

    def __init__(self, outputs_dir: str = "outputs") -> None:
        """Initialize the logger and ensure the output directory exists.

        Args:
            outputs_dir: Path to the output directory. Created if missing.
        """
        self.outputs_dir = outputs_dir
        os.makedirs(self.outputs_dir, exist_ok=True)

    def save(self, output: ApproachOutput, filename: str | None = None) -> str:
        """Serialize and save an ApproachOutput to a JSON file.

        Args:
            output: The complete approach output to save.
            filename: Optional custom filename. If ``None``, a timestamped
                name is generated (e.g., ``lightrag_2025-02-23T10-30-00.json``).

        Returns:
            The full path to the saved JSON file.
        """
        if filename is None:
            safe_ts = output.timestamp.replace(":", "-").replace(" ", "T")
            filename = f"{output.approach}_{safe_ts}.json"

        filepath = os.path.join(self.outputs_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output.to_dict(), f, indent=2, ensure_ascii=False)

        print(f"[OutputLogger] Saved {len(output.results)} results to {filepath}")
        return filepath

    @staticmethod
    def get_timestamp() -> str:
        """Return the current UTC time as an ISO-format string.

        Returns:
            Timestamp string like ``"2025-02-23T10:30:00"``.
        """
        return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")

    @staticmethod
    def load(filepath: str) -> dict:
        """Load a previously saved output file.

        Args:
            filepath: Path to a JSON output file.

        Returns:
            Parsed dictionary from the JSON file.
        """
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
