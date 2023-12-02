import os
from dataclasses import dataclass
import sqlite3
from typing import Iterable, Optional


@dataclass
class Book:
    isbn: str
    title: str
    id: Optional[int] = None
    read: bool = False


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
                id INTEGER PRIMARY KEY,
                isbn TEXT,
                title TEXT,
                read BOOLEAN
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
            INSERT INTO Book (isbn, title, read)
            VALUES (?, ?, ?)
            """,
            (book.isbn, book.title, book.read)
        )
        self._connection.commit()

    def get_books(self, read=None) -> Iterable[Book]:
        query = "SELECT isbn, title, id FROM Book"
        params = tuple()

        if read is not None:
            query += " WHERE read = ?"
            params = *params, read

        self._cursor.execute(query, params)
        for row in self._cursor:
            yield Book(*row)


def main():
    database = Database("database.db")
    for book in database.get_books(read=True):
        print(book)


if __name__ == "__main__":
    main()
