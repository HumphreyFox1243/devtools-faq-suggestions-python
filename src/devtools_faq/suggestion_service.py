import math
from dataclasses import dataclass
from typing import Protocol, Sequence

from .faq_catalog import FAQ_ENTRIES, FaqEntry


class SuggestionGateway(Protocol):
    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """Return one embedding per input text."""

    async def rerank(self, query: str, candidates: Sequence[str], top_k: int) -> list[int]:
        """Return candidate indexes in relevance order."""


@dataclass(frozen=True)
class SuggestedFaq:
    slug: str
    question: str
    answer: str
    area: str


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    return dot / (left_norm * right_norm) if left_norm and right_norm else 0.0


class FaqSuggestionService:
    def __init__(self, gateway: SuggestionGateway, catalog: Sequence[FaqEntry] = FAQ_ENTRIES) -> None:
        self._gateway = gateway
        self._catalog = tuple(catalog)

    async def suggest(self, typed_text: str, limit: int) -> list[SuggestedFaq]:
        texts = [typed_text, *(entry.search_text for entry in self._catalog)]
        embeddings = await self._gateway.embed(texts)
        query_embedding, entry_embeddings = embeddings[0], embeddings[1:]
        shortlist_size = min(len(self._catalog), max(limit * 3, limit))
        scored = sorted(
            zip(self._catalog, entry_embeddings, strict=True),
            key=lambda pair: cosine_similarity(query_embedding, pair[1]),
            reverse=True,
        )
        shortlist = [entry for entry, _ in scored[:shortlist_size]]
        order = await self._gateway.rerank(
            query=typed_text,
            candidates=[entry.search_text for entry in shortlist],
            top_k=limit,
        )
        return [SuggestedFaq(**shortlist[index].__dict__) for index in order]
