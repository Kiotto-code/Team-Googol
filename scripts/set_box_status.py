#!/usr/bin/env python3
"""Set a box status to True in the SQLite DB used by the project.

Usage:
  python3 scripts/set_box_status.py --box-id 1

This script must be run inside the project's Python environment (virtualenv).
"""
import argparse
import sys

from app.db import SessionLocal
from app import models


def main():
    parser = argparse.ArgumentParser(description="Set a box's status to True")
    parser.add_argument("--box-id", "-b", type=int, required=True, help="ID of the box to update")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        box = db.query(models.Box).filter(models.Box.box_id == args.box_id).first()
        if box is None:
            print(f"No box found with box_id={args.box_id}")
            sys.exit(2)

        old = box.status
        box.status = True
        box.load = False
        db.commit()
        print(f"Updated box_id={args.box_id}: status {old} -> {box.status}")
    except Exception as e:
        db.rollback()
        print("Error updating box status:", e)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
