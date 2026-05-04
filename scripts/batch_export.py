"""Batch export project videos.

Usage:
    python scripts/batch_export.py [--project-id UUID] [--output-dir DIR]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from api.config import settings


async def export_project(
    session_factory: async_sessionmaker,
    project_id: str,
    output_dir: Path,
) -> None:
    """Export all episodes of a project as MP4 files."""
    from api.models.project import Episode, Project

    async with session_factory() as session:
        project = await session.get(Project, project_id)
        if project is None:
            print(f"  ⚠️  Project {project_id} not found, skipping")
            return

        result = await session.execute(
            select(Episode)
            .where(Episode.project_id == project_id)
            .order_by(Episode.episode_number)
        )
        episodes = result.scalars().all()

        if not episodes:
            print(f"  ⚠️  No episodes for project '{project.title}'")
            return

        project_dir = output_dir / project.title.replace(" ", "_")
        project_dir.mkdir(parents=True, exist_ok=True)

        for ep in episodes:
            # Check if composite exists in production_tasks
            from api.models.production import ProductionTask

            task_result = await session.execute(
                select(ProductionTask)
                .where(
                    ProductionTask.episode_id == ep.id,
                    ProductionTask.stage == "composite",
                    ProductionTask.status == "completed",
                )
            )
            task = task_result.scalar_one_or_none()

            if task is None:
                print(f"  ⚠️  Episode {ep.episode_number}: no completed composite, skipping")
                continue

            src = task.assets.get("output_path") if task.assets else None
            if not src:
                print(f"  ⚠️  Episode {ep.episode_number}: no output path in assets")
                continue

            src_path = Path(src)
            if not src_path.exists():
                print(f"  ⚠️  Episode {ep.episode_number}: file not found: {src}")
                continue

            dest = project_dir / f"EP{ep.episode_number:03d}.mp4"
            dest.write_bytes(src_path.read_bytes())
            print(f"  ✓ Episode {ep.episode_number} → {dest}")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Batch export project videos")
    parser.add_argument("--project-id", help="Export a single project (UUID)")
    parser.add_argument("--output-dir", default="./outputs/exports", help="Output directory")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    url = settings.database.postgres_url
    engine = create_async_engine(url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    from api.models.project import Project

    async with session_factory() as session:
        if args.project_id:
            project_ids = [args.project_id]
        else:
            result = await session.execute(
                select(Project.id).where(Project.status == "completed")
            )
            project_ids = [row[0] for row in result.all()]

    if not project_ids:
        print("No completed projects to export.")
        await engine.dispose()
        return

    print(f"Exporting {len(project_ids)} project(s) to {output_dir} …\n")

    for pid in project_ids:
        await export_project(session_factory, pid, output_dir)

    await engine.dispose()
    print(f"\n✅ Batch export complete. Output: {output_dir}")


if __name__ == "__main__":
    asyncio.run(main())
