import math
import httpx
from typing import Any
from hashlib import sha256


def normalize(vector: list[float]) -> list[float]:
    if not vector or any(not math.isfinite(value) for value in vector):
        raise ValueError("Embedding contains invalid values")
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        raise ValueError("Embedding is a zero vector")
    return [value / norm for value in vector]