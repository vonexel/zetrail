from pydantic import Field
from typing import Annotated, Literal
from domain.retrieval.models import Hit, Key, Model, Scope


class Evidence(Model):
    evidence_id: str
    retrieval_run_id: str
    source: Hit
    span_start: int
    span_end: int
    span_text: str
    value: str | None = None
    normalized_value: str | None = None
    classification: Literal["supporting", "qualifying", "contradicting", "unclear"] = "unclear"
    extractor_version: str = "verbatim-v1"
    confidence: float | None = None
    reviewed: bool = False
    supersedes: str | None = None

class VerifyRequest(Model):
    claim: str = Field(min_length = 1, max_length = 4000)
    scope: Scope

class MatrixRequest(Model):
    library_id: int = Field(ge = 1)
    item_keys: list[Key] = Field(min_length = 1, max_length = 100)
    fields: list[Annotated[str, Field(pattern = r"^[a-zA-Z][a-zA-Z0-9_ \-]{0, 63}$")]] = Field(min_length = 1, max_length = 12)

class ReviewRequest(Model):
    value: str | None = Field(default = None, max_length = 2000)
    classification: Literal["supporting", "qualifying", "contradicting", "unclear"] = "unclear"

class MatrixReviewRequest(ReviewRequest):
    item_key: Key
    field: str = Field(min_length = 1, max_length = 64)

class GenerationRequest(Model):
    query: str = Field(min_length = 1, max_length = 4000)
    scope: Scope