"""
AegisTwin Pipeline Processor

Data normalization and transformation pipeline.

@ai_prompt: Use Pipeline.process() to transform raw data into normalized records.
@context_boundary: aegistwin/modules/pipeline/processor

# AI-GENERATED 2026-01-06
"""

import hashlib
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class TransformationResult:
    """Result of a transformation step."""
    records: list[dict[str, Any]]
    transformations_applied: list[str]
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class Pipeline:
    """
    Data normalization and transformation pipeline.

    Processes raw data through a series of transformation steps
    to produce normalized, schema-compliant records.
    """

    def __init__(self, schema_version: str = "1.0.0"):
        self.schema_version = schema_version
        self._transformers: list[Callable] = []
        self._register_default_transformers()

    def _register_default_transformers(self) -> None:
        """Register default transformation functions."""
        self._transformers = [
            self._normalize_timestamps,
            self._normalize_text,
            self._extract_entities,
            self._compute_hashes,
        ]

    def add_transformer(self, transformer: Callable) -> None:
        """Add a custom transformer to the pipeline."""
        self._transformers.append(transformer)

    def process(
        self,
        records: list[dict[str, Any]],
        source: str = "unknown",
    ) -> TransformationResult:
        """
        Process records through the transformation pipeline.

        Args:
            records: Raw records to process
            source: Data source identifier

        Returns:
            TransformationResult with normalized records
        """
        result = TransformationResult(
            records=records.copy(),
            transformations_applied=[],
            metadata={"source": source, "input_count": len(records)},
        )

        for transformer in self._transformers:
            try:
                result.records = transformer(result.records)
                result.transformations_applied.append(transformer.__name__)
            except Exception as e:
                result.errors.append(f"{transformer.__name__}: {str(e)}")

        result.metadata["output_count"] = len(result.records)
        result.metadata["schema_version"] = self.schema_version

        return result

    def _normalize_timestamps(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Normalize timestamp fields to ISO format."""
        timestamp_fields = ["timestamp", "created_at", "updated_at", "date", "time"]

        for record in records:
            for field_name in timestamp_fields:
                if field_name in record and record[field_name]:
                    record[field_name] = self._parse_timestamp(record[field_name])

        return records

    def _parse_timestamp(self, value: Any) -> str | None:
        """Parse various timestamp formats to ISO string."""
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, str):
            # Already ISO format
            if re.match(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', value):
                return value
            # Try common formats
            formats = [
                "%Y-%m-%d %H:%M:%S",
                "%Y/%m/%d %H:%M:%S",
                "%m/%d/%Y %H:%M:%S",
                "%Y-%m-%d",
            ]
            for fmt in formats:
                try:
                    return datetime.strptime(value, fmt).isoformat()
                except ValueError:
                    continue
        return str(value) if value else None

    def _normalize_text(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Normalize text fields."""
        text_fields = ["content", "text", "message", "body", "subject"]

        for record in records:
            for field_name in text_fields:
                if field_name in record and isinstance(record[field_name], str):
                    # Strip whitespace, normalize newlines
                    text = record[field_name].strip()
                    text = re.sub(r'\r\n', '\n', text)
                    text = re.sub(r'\s+', ' ', text)
                    record[field_name] = text

        return records

    def _extract_entities(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Extract basic entities from text fields."""
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'

        for record in records:
            entities = []
            text_fields = ["content", "text", "message", "body"]

            for field_name in text_fields:
                if field_name in record and isinstance(record[field_name], str):
                    text = record[field_name]

                    # Extract emails
                    for email in re.findall(email_pattern, text):
                        entities.append({"type": "email", "value": email})

                    # Extract URLs
                    for url in re.findall(url_pattern, text):
                        entities.append({"type": "url", "value": url})

            if entities:
                record["_extracted_entities"] = entities

        return records

    def _compute_hashes(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Compute content hashes for deduplication."""
        for record in records:
            # Create hash from key content fields
            hash_content = ""
            for field_name in ["content", "text", "message", "id"]:
                if field_name in record:
                    hash_content += str(record[field_name])

            if hash_content:
                record["_content_hash"] = hashlib.sha256(
                    hash_content.encode()
                ).hexdigest()[:16]

        return records


class PipelineBuilder:
    """Builder for creating custom pipelines."""

    def __init__(self):
        self._pipeline = Pipeline()
        self._pipeline._transformers = []

    def with_timestamp_normalization(self) -> "PipelineBuilder":
        """Add timestamp normalization."""
        self._pipeline._transformers.append(self._pipeline._normalize_timestamps)
        return self

    def with_text_normalization(self) -> "PipelineBuilder":
        """Add text normalization."""
        self._pipeline._transformers.append(self._pipeline._normalize_text)
        return self

    def with_entity_extraction(self) -> "PipelineBuilder":
        """Add entity extraction."""
        self._pipeline._transformers.append(self._pipeline._extract_entities)
        return self

    def with_hashing(self) -> "PipelineBuilder":
        """Add content hashing."""
        self._pipeline._transformers.append(self._pipeline._compute_hashes)
        return self

    def with_custom(self, transformer: Callable) -> "PipelineBuilder":
        """Add custom transformer."""
        self._pipeline._transformers.append(transformer)
        return self

    def build(self) -> Pipeline:
        """Build the pipeline."""
        return self._pipeline
