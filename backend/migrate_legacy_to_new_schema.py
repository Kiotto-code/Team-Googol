"""One-off migration utility to copy legacy Lost & Found tables into the new schema."""

from database import (
    CASE_TABLE,
    ITEM_TABLE,
    USER_TABLE,
    BOX_TABLE,
    get_db_connection,
    init_database,
)


def main() -> None:
    init_database()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        counts = {}
        for table in (USER_TABLE, ITEM_TABLE, BOX_TABLE, CASE_TABLE):
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            counts[table] = cursor.fetchone()[0]
    print("Migration complete.")
    for table, count in counts.items():
        print(f"{table}: {count} records")


if __name__ == "__main__":
    main()
