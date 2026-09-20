import httpx
import pytest

from devtools_faq.infrai_gateway import InfraiError, InfraiGateway


@pytest.mark.asyncio
async def test_rerank_decodes_business_error_before_http_status_handling() -> None:
    def reject(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.headers["Authorization"] == "Bearer test-key"
        return httpx.Response(
            400,
            json={"ok": False, "data": None, "error": {"code": "query_rejected", "message": "Check query."}, "metadata": {}},
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(reject))
    gateway = InfraiGateway("test-key", http_client=client)
    with pytest.raises(InfraiError) as caught:
        await gateway.rerank("release", ["candidate"], 1)

    assert caught.value.code == "query_rejected"
    assert caught.value.status_code == 400
    await gateway.close()
    await client.aclose()
