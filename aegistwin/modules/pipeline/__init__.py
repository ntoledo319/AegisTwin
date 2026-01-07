"""
AegisTwin Pipeline Module

Data normalization and transformation pipeline.

@ai_prompt: Use Pipeline to process ingested data through transformation stages.
@context_boundary: aegistwin/modules/pipeline
"""

from aegistwin.modules.pipeline.processor import (
    Pipeline,
    PipelineBuilder,
    TransformationResult,
)

__all__ = ["Pipeline", "PipelineBuilder", "TransformationResult"]
