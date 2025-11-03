"""
Clean the items table.

Usage: run with the project's Python environment to ensure dependencies match.
"""

from __future__ import annotations

from contextlib import suppress

from app.db import SessionLocal
from app import models


def main() -> None:
    db = SessionLocal()
    try:
        total = db.query(models.Item).count()
        if total == 0:
            print("No items to delete.")
            return

        deleted = db.query(models.Item).delete(synchronize_session=False)
        db.commit()
        print(f"Deleted {deleted} item(s).")
    except Exception as e:
        with suppress(Exception):
            db.rollback()
        print(f"Error while cleaning items: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
