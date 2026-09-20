from collections.abc import Sequence

import pytest

from devtools_faq.faq_catalog import FaqEntry
from devtools_faq.suggestion_service import FaqSuggestionService


class RecordingGateway:
    def __init__(self) -> None:
        self.rerank_candidates: list[str] = []

    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        vectors = {
            "release waiting": [1.0, 0.0],
            "pending release": [0.9, 0.1],
            "rollback release": [0.7, 0.3],
            "build cache": [0.0, 1.0],
            "browser trace": [0.1, 0.9],
        }
        return [vectors[text.split("\n", maxsplit=1)[0]] for text in texts]

    async def rerank(self, query: str, candidates: Sequence[str], top_k: int) -> list[int]:
        assert query == "release waiting"
        assert top_k == 1
        self.rerank_candidates = list(candidates)
        return [1]


@pytest.mark.asyncio
async def test_semantic_shortlist_is_reranked_before_returning_a_release_answer() -> None:
    catalog = (
        FaqEntry("pending", "pending release", "pending release", "release"),
        FaqEntry("rollback", "rollback release", "rollback release", "release"),
        FaqEntry("cache", "build cache", "build cache", "build"),
        FaqEntry("trace", "browser trace", "browser trace", "diagnostic"),
    )
    gateway = RecordingGateway()

    result = await FaqSuggestionService(gateway, catalog).suggest("release waiting", limit=1)

    assert [entry.slug for entry in result] == ["rollback"]
    assert gateway.rerank_candidates == ["pending release\npending release", "rollback release\nrollback release", "browser trace\nbrowser trace"]
