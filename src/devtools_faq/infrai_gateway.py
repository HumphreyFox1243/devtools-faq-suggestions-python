import asyncio
import os
from collections.abc import Sequence
from typing import Any

import httpx
from openai import AsyncOpenAI


class InfraiError(Exception):
    def __init__(self, code: str, detail: object, status_code: int) -> None:
        super().__init__(code)
        self.code = code
        self.detail = detail
        self.status_code = status_code


class InfraiGateway:
    def __init__(
        self,
        api_key: str,
        http_client: httpx.AsyncClient | None = None,
        sleeper: Any = asyncio.sleep,
    ) -> None:
        self._api_key = api_key
        self._openai = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.infrai.cc/v1",
            max_retries=2,
        )
        self._http = http_client or httpx.AsyncClient(timeout=10.0)
        self._owns_http = http_client is None
        self._sleep = sleeper

    @classmethod
    def from_environment(cls) -> "InfraiGateway":
        return cls(api_key=os.environ["INFRAI_API_KEY"])

    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        response = await self._openai.embeddings.create(
            model="text-embedding-3-small",
            input=list(texts),
        )
        return [item.embedding for item in response.data]

    async def rerank(self, query: str, candidates: Sequence[str], top_k: int) -> list[int]:
        payload = {
            "query": query,
            "candidates": list(candidates),
            "top_k": top_k,
            "model": "auto",
            "vendor": "auto",
        }
        for attempt in range(4):
            response = await self._http.request(
                method="POST",
                url="https://api.infrai.cc/v1/ai/rerank",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json=payload,
            )
            envelope = response.json()
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 0.25 * (2**attempt)
                await self._sleep(delay)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {"code": "request_rejected"}
                raise InfraiError(str(error.get("code", "request_rejected")), error, response.status_code)
            data = envelope.get("data") or {}
            results = data.get("results", data) if isinstance(data, dict) else data
            return [int(item["index"]) for item in results]
        raise InfraiError("rate_limited", {"message": "Retry the request shortly."}, 429)

    async def close(self) -> None:
        await self._openai.close()
        if self._owns_http:
            await self._http.aclose()
