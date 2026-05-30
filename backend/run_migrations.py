"""Alembic migration runner — entrypoint for the emily-migrate Cloud Run job."""

import subprocess
import sys


def main() -> int:
    """Run alembic upgrade head and return exit code."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd="/app",
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result.returncode
    except FileNotFoundError:
        print("ERROR: alembic not found. Install with: pip install alembic", file=sys.stderr)
        return 1
    except subprocess.TimeoutExpired:
        print("ERROR: migration timed out after 120s", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
