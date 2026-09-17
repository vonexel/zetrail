import math
import httpx
from typing import Any
from hashlib import sha256
from zetrail.settings import Settings
from domain.retrieval.ranking import tokenize
from sentence_transformers import CrossEncoder, SentenceTransformer


def normalize(vector: list[float]) -> list[float]:
    if not vector or any(not math.isfinite(value) for value in vector):
        raise ValueError("Embedding contains invalid values")
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        raise ValueError("Embedding is a zero vector")
    return [value / norm for value in vector]
                                                                                                                        # todo: add support of another local providers or even local fine-tuned models
class OllamaEmbedder:
    def __init__(self, settings: Settings):
        self.url = settings.ollama_url.rstrip("/")
        self.model = settings.embedding_model
        response = httpx.get(f"{self.url}/api/tags", timeout = 15, trust_env = False)
        response.raise_for_status()
        match = next((entry for entry in response.json()["models"] if entry["name"] in {self.model, f"{self.model}:latest"}), None)
        if not match:
            raise ValueError("Embedding model is not installed in Ollama")
        self.model_id = f"ollama:{self.model}@{match['digest']}"

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), 32):
            response = httpx.post(f"{self.url}/api/embed",
                                  json = {"model": self.model, "input": texts[start:start + 32], "truncate": False,},
                                  timeout = 180, trust_env = False)
            response.raise_for_status()
            batch = response.json()["embeddings"]
            if len(batch) != len(texts[start:start + 32]):
                raise ValueError("Embedding count mismatch")
            vectors.extend(normalize(vector) for vector in batch)
            if vectors and len({len(vector) for vector in vectors}) != 1:
                raise ValueError("Embedding dimensions changed")
            return vectors

class SentenceTransformerEmbedder:
    def __init__(self, settings: Settings):
        self.model: Any = SentenceTransformer(settings.embedding_model, local_files_only = True)
        self.model_id = f"sentence-transformers:{settings.embedding_model}@{settings.embedding_revision}"

    def embed(self, texts: list[str]) -> list[list[float]]:
        return self.model.encode(texts, normalize_embeddings = True, show_progress_bar = False).tolist()

class CrossEncoderReranker:
    def __init__(self, path: str):
        self.model: Any = CrossEncoder(path, local_files_only = True)
        self.model_id = path

    def score(self, query: str, passages: list[str]) -> list[float]:
        return self.model.predict([(query, passage) for passage in passages]).tolist()

class FixtureEmbedder:                                                                                                  # test embedder
    model_id = "fixtire-hash-v1"

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = []
        for text in texts:
            vector = [0.0] * 256
            for word in tokenize(text):
                vector[int.from_bytes(sha256(word.encode()).digest()[:4]) % 256] += 1.0
                vectors.append(normalize(vector))
        return vectors