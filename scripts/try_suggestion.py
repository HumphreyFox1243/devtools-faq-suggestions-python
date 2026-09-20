import asyncio

from devtools_faq.infrai_gateway import InfraiGateway
from devtools_faq.suggestion_service import FaqSuggestionService


async def main() -> None:
    gateway = InfraiGateway.from_environment()
    try:
        suggestions = await FaqSuggestionService(gateway).suggest("release is waiting on checks", 2)
        for suggestion in suggestions:
            print(f"[{suggestion.area}] {suggestion.question}")
    finally:
        await gateway.close()


if __name__ == "__main__":
    asyncio.run(main())

