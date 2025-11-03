"""
Clean the cases table.

Usage: run with the project's Python environment to ensure dependencies match.
"""

from __future__ import annotations

from contextlib import suppress

from app.db import SessionLocal
from app import models


def main() -> None:
    db = SessionLocal()
    try:
        # Count existing cases
        total = db.query(models.Case).count()
        if total == 0:
            print("No cases to delete.")
            return

        # Delete all cases efficiently
        deleted = db.query(models.Case).delete(synchronize_session=False)
        db.commit()
        print(f"Deleted {deleted} case(s).")
    except Exception as e:
        with suppress(Exception):
            db.rollback()
        print(f"Error while cleaning cases: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
