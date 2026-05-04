"""Seed built-in JSON templates from api/json_templates/ into the database.

Idempotent — existing templates (matched by slug) are skipped.
"""

from __future__ import annotations

import asyncio
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from api.config import settings

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "api" / "json_templates"


async def main() -> None:
    from api.models.template import JSONTemplate

    url = settings.database.postgres_url
    engine = create_async_engine(url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    json_files = sorted(TEMPLATES_DIR.glob("*.json"))
    if not json_files:
        print(f"⚠️  No JSON templates found in {TEMPLATES_DIR}")
        await engine.dispose()
        return

    created, skipped = 0, 0

    async with session_factory() as session:
        for fp in json_files:
            data = json.loads(fp.read_text(encoding="utf-8"))
            slug = data.get("slug", fp.stem)

            # Check if already exists
            existing = await session.execute(
                select(JSONTemplate).where(JSONTemplate.slug == slug)
            )
            if existing.scalar_one_or_none() is not None:
                skipped += 1
                print(f"  – Skipped (exists): {slug}")
                continue

            now = datetime.now(timezone.utc)
            tpl = JSONTemplate(
                id=str(uuid.uuid4()),
                name=data.get("name", fp.stem),
                slug=slug,
                category=data.get("category", "script"),
                description=data.get("description", ""),
                schema=data.get("schema", {}),
                example=data.get("example", {}),
                system_prompt_suffix=data.get("system_prompt_suffix", ""),
                version=data.get("version", 1),
                is_builtin=True,
                created_at=now,
                updated_at=now,
            )
            session.add(tpl)
            created += 1
            print(f"  ✓ Created: {slug}")

        await session.commit()

    await engine.dispose()
    print(f"\n✅ Done. Created: {created}, Skipped: {skipped}")


if __name__ == "__main__":
    asyncio.run(main())
