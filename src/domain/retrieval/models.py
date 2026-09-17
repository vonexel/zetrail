import json
from domain.document.ids import stable_id
from domain.documents.models import Document
from typing import Any, Annotated, Literal, Protocol
from pydantic import BaseModel, ConfigDict, Field, model_validator


Key = Annotated[str, Field(pattern = r"^[A-Z0-9]{8}$")]


class Model(BaseModel):
    model_config = ConfigDict(extra = "forbid")

class Scope(Model):
    library_id: int = Field(ge = 1)
    collection_keys: list[Key] = Field(default_factory = list, max_length = 100)
    item_keys: list[Key] = Field(default_factory = list, max_length = 1000)
    tags: list[str] = Field(default_factory = list, max_length = 100)
    year_from: int | None = None
    year_to: int | None = None

class RetrievalConfig(Model):
    name: str = "hybrid-v1"
    strategy: Literal["lexical", "dense", "hybrid"] = "hybrid"
    candidate_k: int = Field(default = 40, ge = 1, le = 200)
    rrf_k: int = Field(default = 60, ge = 1)
    min_dense_score: float = Field(default = 0.35, ge = -1, le = 1)
    max_chunks_per_document: int = Field(default = 4, ge = 1, le = 20)
    max_total_tokens: int = Field(default = 8000, ge = 100, le = 32000)
    rerank: bool = False

    @property
    def config_id(self) -> str:
        return stable_id(json.dumps(self.model_dump(), sort_keys = True, separators = (",", ":")))

class ChunkingConfig(Model):
    target_words: int = Field(default = 320, ge = 20, le = 2000)
    overlap_words: int = Field(default = 40, ge = 0)
    version: str = "page-words-v1"

    @model_validator(mode = 'after')
    def valid_overlap(self) -> "ChunkingConfig":
        if self.overlap_words >= self.target_words:
            raise ValueError("Overlap must be smaller than the chunk size")
        return self

    @property
    def config_id(self) -> str:
        return stable_id(json.dumps(self.model_dump(), sort_keys = True))

class Chunk(Model):
    chunck_id: str
    document_version: str
    library_id: int
    item_key: str
    attachment_key: str
    page_from: int = Field(ge = 1)
    page_to: int = Field(ge = 1)
    section: str | None = None
    chunk_index: int
    text: str
    token_count: int
    chunker_config_hash: str
    embedding_model: str
    embedding: list[float] = Field(default_factory = list)

class Hit(Model):
    chunk: Chunk
    title: str
    scores: dict[str, float] = Field(default_factory = dict)

class SearchRequest(Model):
    query: str = Field(min_length = 1, max_length = 4000)
    scope: Scope
    config: RetrievalConfig = Field(default_factory = RetrievalConfig)
    limit: int = Field(default = 10, ge = 1, le = 100)

class SearchResult(Model):
    retrieval_run_id: str
    retrieval_config_id: str
    corpus_version: str
    hits: list[Hit]
    latency_ms: float
    candidate_count: int
    status: Literal["ok", "insufficient_evidence"]