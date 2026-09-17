import re
from domain.retrieval.models import Hit


def tokenize(text: str) -> list[str]:
    return re.findall(r"\w+(?:[+.\-)]+\w+|\+\+\)?", text.casefold())

def reciprocal_rank_fusion(rankings: list[list[Hit]], rrf_k: int = 60) -> list[Hit]:
    merged: dict[str, Hit] = {}
    for ranking in rankings:
        seen: set[str] = set()
        for rank, hit in enumerate(ranking, start = 1):
            key = hit.chunk.chunck_id
            if key in seen:
                continue
            seen.add(key)
            if key not in merged:
                merged[key] = hit.model_copy(deep = True)
                merged[key].scores["fusion"] = 0.0
            merged[key].scores.update({name: score for name, score in hit.scores.items() if name != "fusion"})
            merged[key].scores["fusion"] += 1.0 / (rrf_k + rank)
    return sorted(merged.values(), key = lambda hit: (-hit.scores["fusion"], hit.chunk.chunck_id))