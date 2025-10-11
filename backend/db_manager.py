#!/usr/bin/env python3
"""Database management CLI tool for the Lost & Found system."""

import argparse
from database import (
    delete_item,
    init_database,
    list_cases,
    list_items,
    release_expired_cases,
)


def list_items_cli():
    items = list_items()
    if not items:
        print("No items found.")
        return

    print("Items:\n" + "-" * 60)
    for item in items:
        print(f"ID: {item['item_id']}")
        print(f"Description: {item['description']}")
        print(f"Image URL: {item['image_url']}")
        print(f"Finder User ID: {item['finder_user_id']}")
        print(f"Finder Image URL: {item['finder_img_url']}")
        print(f"Created: {item['created_at']}")
        print("-" * 60)


def list_cases_cli():
    cases = list_cases()
    if not cases:
        print("No cases found.")
        return

    print("Cases:\n" + "-" * 60)
    for case in cases:
        print(f"Case ID: {case['found_id']}")
        print(f"Box ID: {case['box_id']}")
        print(f"Item ID: {case['item_id']}")
        print(f"Status: {case['status']}")
        print(f"Receiver ID: {case['reciver_id']}")
        print(f"Close At: {case['case_close_at']}")
        print(f"Created At: {case['created_at']}")
        print("-" * 60)


def delete_item_cli(item_id: int):
    if delete_item(item_id):
        print(f"Deleted item {item_id}")
    else:
        print(f"Item {item_id} not found")


def main():
    parser = argparse.ArgumentParser(description="Lost & Found Database Management Tool")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    subparsers.add_parser("list-items", help="List all items")
    subparsers.add_parser("list-cases", help="List all cases")
    subparsers.add_parser("release-expired", help="Release expired case claims")

    delete_parser = subparsers.add_parser("delete-item", help="Delete an item by ID")
    delete_parser.add_argument("item_id", type=int)

    subparsers.add_parser("init", help="Initialise database schema")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    if args.command == "list-items":
        list_items_cli()
    elif args.command == "list-cases":
        list_cases_cli()
    elif args.command == "release-expired":
        count = release_expired_cases()
        print(f"Released {count} expired claims")
    elif args.command == "delete-item":
        delete_item_cli(args.item_id)
    elif args.command == "init":
        init_database()
        print("Database initialised.")


if __name__ == "__main__":
    main()
