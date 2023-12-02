import os
from dataclasses import dataclass
import sqlite3
from typing import Iterable


@dataclass
class Book:
    isbn: str
    title: str


class Database:
    def __init__(self, path: str):
        init = not os.path.exists(path)
        self._connection = sqlite3.connect(path)
        self._cursor = self._connection.cursor()

        if init:
            self._initialise_database()

    def _initialise_database(self):
        self._cursor.execute(
            """
            CREATE TABLE Book (
                isbn TEXT PRIMARY KEY,
                title TEXT
            )
            """
        )
        self._connection.commit()

    def add_book(self, book: Book):
        # check book doesn't already exist
        self._cursor.execute(
            """
            SELECT isbn FROM Book WHERE isbn = ?
            """,
            (book.isbn,)
        )
        if len(self._cursor.fetchall()) > 0:
            return

        # insert book
        self._cursor.execute(
            """
            INSERT INTO Book (isbn, title)
            VALUES (?, ?)
            """,
            (book.isbn, book.title)
        )
        self._connection.commit()

    def get_books(self) -> Iterable[Book]:
        self._cursor.execute(
            """
            SELECT isbn, title FROM Book
            """
        )
        for row in self._cursor:
            yield Book(*row)


def main():
    database = Database("database.db")
    database.add_book(Book("123", "Book 1"))
    database.add_book(Book("456", "Book 2"))
    for book in database.get_books():
        print(book)


if __name__ == "__main__":
    main()
