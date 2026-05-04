"""Check that all required tool versions meet TVAiPlatform minimums.

Run: python scripts/check_versions.py
"""

from __future__ import annotations

import shutil
import subprocess
import sys

REQUIREMENTS: list[tuple[str, str, str | None]] = [
    # (name, min_version, binary)
    ("Python", "3.12", sys.executable),
    ("Node.js", "22", "node"),
    ("pnpm", "9", "pnpm"),
    ("FFmpeg", "6", "ffmpeg"),
    ("PostgreSQL", "17", "psql"),
    ("Redis", "7", "redis-server"),
]


def _version_tuple(raw: str) -> tuple[int, ...]:
    """Extract leading digits from a version string."""
    parts: list[int] = []
    for ch in raw:
        if ch.isdigit():
            parts.append(int(ch))
            break
    # Try to get major.minor.patch
    nums = ""
    started = False
    for ch in raw:
        if ch.isdigit():
            nums += ch
            started = True
        elif started:
            break
    return tuple(int(x) for x in nums.split(".") if x) if nums else (0,)


def _get_version(binary: str | None, name: str) -> str | None:
    """Return version string for a binary, or None if not found."""
    if binary is None:
        return None
    path = shutil.which(binary)
    if not path:
        return None
    try:
        result = subprocess.run(
            [path, "--version"],
            capture_output=True, text=True, timeout=10,
        )
        output = (result.stdout + result.stderr).strip()
        # PostgreSQL returns version differently
        if binary == "psql":
            if "PostgreSQL" in output:
                return output.split("PostgreSQL")[-1].strip().split()[0]
        return output.split("\n")[0]
    except Exception:
        return None


def main() -> None:
    print("=" * 50)
    print("  TVAiPlatform — Version Check")
    print("=" * 50)

    all_ok = True
    for name, min_ver, binary in REQUIREMENTS:
        version_str = _get_version(binary, name)

        if version_str is None:
            status = f"❌ NOT FOUND (need ≥ {min_ver})"
            all_ok = False
        else:
            actual = _version_tuple(version_str)
            needed = _version_tuple(min_ver)
            if actual >= needed:
                status = f"✅ {version_str}"
            else:
                status = f"⚠️  {version_str} (need ≥ {min_ver})"
                all_ok = False

        print(f"  {name:15s} {status}")

    print("=" * 50)
    if all_ok:
        print("  All version checks passed! ✅")
    else:
        print("  Some checks failed. Please update missing/outdated tools.")
        sys.exit(1)


if __name__ == "__main__":
    main()
