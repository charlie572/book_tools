import argparse
import csv

from database import Database, Book


def main():
    parser = argparse.ArgumentParser(
        "load_storygraph",
        description="Load storygraph data into the database."
    )
    parser.add_argument(
        "storygraph_export_file",
        type=argparse.FileType("r"),
        help="Exported CSV file from Storygraph."
    )
    parser.add_argument(
        "-d",
        "--database",
        type=str,
        default="database.db",
        help="Path to database to save to."
    )

    args = parser.parse_args()

    database = Database(args.database)

    reader = csv.DictReader(args.storygraph_export_file)
    for row in reader:
        book = Book(
            row["ISBN/UID"] or None,
            row["Title"],
            read=row["Read Count"] != "0",
        )

        if database.get_book(book):
            database.update_book(book)
        else:
            database.add_book(book)

        tags = [tag.strip() for tag in row["Tags"].split(",")]
        database.add_book_tags(book, tags)

    args.storygraph_export_file.close()


if __name__ == "__main__":
    main()
