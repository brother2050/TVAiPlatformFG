"""Initialize database tables for TVAiPlatform.

Run once after PostgreSQL is up:
    python scripts/init_db.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Add project root to path so we can import api.config
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine

from api.config import settings


async def main() -> None:
    """Create all tables defined in the models package."""
    # Import all models so Base.metadata is populated
    from api.models.base import Base
    import api.models.project  # noqa: F401
    import api.models.character  # noqa: F401
    import api.models.script  # noqa: F401
    import api.models.template  # noqa: F401
    import api.models.production  # noqa: F401
    import api.models.summary  # noqa: F401

    url = settings.database.postgres_url
    engine = create_async_engine(url, echo=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await engine.dispose()
    print("✅ All database tables created successfully.")


if __name__ == "__main__":
    asyncio.run(main())
