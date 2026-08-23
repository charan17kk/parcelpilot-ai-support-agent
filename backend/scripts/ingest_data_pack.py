import argparse
import asyncio
import json

from app.config import get_settings
from app.db import async_session_factory
from app.ingestion import IngestionService


async def main(reset: bool) -> None:
    settings = get_settings()
    async with async_session_factory() as db:
        result = await IngestionService(settings).ingest(db, reset=reset)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest the ParcelPilot candidate pack")
    parser.add_argument("--reset", action="store_true", help="Replace previously imported assessment data")
    args = parser.parse_args()
    asyncio.run(main(args.reset))

