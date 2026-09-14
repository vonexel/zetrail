import math


def recall_at_k(ranked: list[str], relevant: set[str], k: int) -> float:                                                # share of all relevant documents found within the top-k of the ranked
    if not relevant:
        return 0.0
    if k <= 0:
        return 0.0
    found = len(set(ranked[:k]) & relevant)
    return found / len(relevant)

def precision_at_k(ranked: list[str], relevant: set[str], k: int) -> float:                                             # share of the top-k ranked documents that are relevant
    if k <= 0:
        return 0.0
    return len(set(ranked[:k]) & relevant) / k

def mrr(ranked: list[str], relevant: set[str]) -> float:                                                                # mean reciprocal rank for a single query
    for rank, doc_id in enumerate(ranked, start = 1):
        if doc_id in relevant:
            return 1.0 / rank
    return 0.0

def ndcg_at_k(ranked: list[str], relevant: set[str]) -> float:                                                          # normalized discounted cumulative gain at k with binary relevance
    if not relevant or k <= 0:
        return 0.0
    dcg = sum(1.0 / math.log2(rank + 1)
    for rank, doc_id in enumerate(ranked[:k], start = 1) if doc_id in relevant)
    ideal_hits = min(len(relevant), k)
    idcg = sum(1.0 / math.log2(rank + 1) for rank in range(1, ideal_hits + 1))
    if idcg == 0.0:
        return 0.0
    return dcg / idcg

def success_at_k(ranked: list[str], relevant: set[str], k: int) -> float:                                               # binary hit indicator
    return 1.0 if set(ranked[:k]) & relevant else 0.0

def percentile(values: list[float], pct: float) -> float:                                                               # nearest-rank percentile of `pct` over an ascending-sorted copy of the values
    if not values:
        return 0.0
    ordered = sorted(values)
    if pct <= 0:
        return ordered[0]
    if pct >= 100:
        return ordered[-1]
    rank = math.ceil(pct / 100 * len(ordered))
    return ordered[max(rank -1, 0)]
