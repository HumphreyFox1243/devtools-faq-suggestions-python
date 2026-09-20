from contextlib import asynccontextmanager
from typing import AsyncIterator, Literal

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .infrai_gateway import InfraiError, InfraiGateway
from .suggestion_service import FaqSuggestionService


class SuggestRequest(BaseModel):
    typed_text: str = Field(min_length=2, max_length=300)
    limit: int = Field(default=3, ge=1, le=5)


class FaqSuggestion(BaseModel):
    slug: str
    question: str
    answer: str
    area: Literal["build", "release", "diagnostic"]


class SuggestResponse(BaseModel):
    suggestions: list[FaqSuggestion]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    gateway = InfraiGateway.from_environment()
    app.state.gateway = gateway
    app.state.suggestions = FaqSuggestionService(gateway)
    yield
    await gateway.close()


app = FastAPI(title="Developer-tools FAQ suggestions", lifespan=lifespan)


@app.exception_handler(InfraiError)
async def infrai_error_handler(_request: Request, error: InfraiError) -> JSONResponse:
    caller_status = error.status_code if 400 <= error.status_code < 500 else 502
    return JSONResponse(
        status_code=caller_status,
        content={"error": {"code": error.code, "detail": error.detail}},
    )


@app.post("/suggest", response_model=SuggestResponse)
async def suggest_faq(body: SuggestRequest, request: Request) -> SuggestResponse:
    matches = await request.app.state.suggestions.suggest(body.typed_text, body.limit)
    return SuggestResponse(suggestions=[FaqSuggestion.model_validate(item.__dict__) for item in matches])

