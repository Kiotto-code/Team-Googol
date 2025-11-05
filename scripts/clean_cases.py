"""
Clean the cases table.

Usage: run with the project's Python environment to ensure dependencies match.
"""

from __future__ import annotations

import os
import sys
from contextlib import suppress

# Ensure project root is on sys.path when run directly
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

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
