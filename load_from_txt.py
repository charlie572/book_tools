import argparse
import csv

from isbnlib import isbn_from_words, meta

from database import Database, Book


def main():
    parser = argparse.ArgumentParser(
        "load_from_txt",
        description="Load storygraph data into the database."
    )
    parser.add_argument(
        "txt_file",
        type=argparse.FileType("r"),
        help="txt file with a book title on each line"
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

    for title in args.txt_file.readlines():
        if not title:
            continue

        isbn = isbn_from_words(title)
        metadata = meta(isbn)

        book = Book(
            isbn,
            metadata["Title"],
            read=False,
        )

        if database.book_exists(book):
            database.update_book(book)
        else:
            database.add_book(book)

    args.txt_file.close()


if __name__ == "__main__":
    main()
