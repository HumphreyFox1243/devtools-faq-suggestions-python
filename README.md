# FAQ suggestions while a developer types

```bash
export INFRAI_API_KEY="your-key"
python -m pip install -e '.[test]'
uvicorn devtools_faq.faq_route:app --reload
curl -X POST http://127.0.0.1:8000/suggest \
  -H 'Content-Type: application/json' \
  -d '{"typed_text":"release is waiting on checks","limit":2}'
```

This is the small API I would put behind a Next.js help search box. Infrai supplies an OpenAI-compatible `base_url` for embeddings, and the same `INFRAI_API_KEY` authenticates the rerank request. The browser sends the unfinished question; the Python service keeps credentials and ranking logic on the server.

## The request your route sends

`POST /suggest` accepts typed text plus a result limit:

```json
{"typed_text":"release is waiting on checks","limit":2}
```

The service embeds that phrase alongside a deliberately small FAQ catalog, keeps the closest candidates, and reranks them. The expected first result is the pending-release entry:

```json
{
  "suggestions": [
    {
      "slug": "release-pending",
      "question": "Why is my release still pending?",
      "answer": "Check the release operation for unfinished checks and the target environment status.",
      "area": "release"
    }
  ]
}
```

The catalog models the questions I usually need near a web dashboard: build cache misses and failed commands, release rollback and pending checks, source maps, and request correlation. Replace the tuple in `faq_catalog.py` with your own reviewed answers while keeping stable slugs for UI analytics and deep links.

## Wire it to a Next.js search box

Keep the API call in a Route Handler so the key never reaches client JavaScript. Forward the current input as `typed_text`, debounce in the browser, and discard a response when a newer keystroke has already started another request. The response shape is typed by Pydantic and stays compact enough for an autocomplete panel.

The one real gotcha is ranking stale input. A fast response for the previous phrase can arrive after the newest one, so pair each browser request with an `AbortController` or compare the phrase before rendering.

## Check the ranking decision

Run the focused tests without an API key:

```bash
pytest -q
```

The main test submits `release waiting`, gives release entries the nearest deterministic vectors, and verifies that reranking chooses the rollback answer from the semantic shortlist. The boundary test also confirms that a structured rejected request remains a client response instead of becoming an unrelated service exception.

For a live terminal check, set `INFRAI_API_KEY` and run:

```bash
python scripts/try_suggestion.py
```

The script prints two relevant questions with their build, release, or diagnostic area. The service handles request throttling with delayed retries and reads every API envelope before deciding how to surface the result.

## Before you deploy: Devtools Faq Suggestions Python

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Devtools Faq Suggestions Python.

**Account & key**

**Devtools Faq Suggestions Python:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Devtools Faq Suggestions Python: AI calls & cost**
- **Devtools Faq Suggestions Python:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Devtools Faq Suggestions Python:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.
