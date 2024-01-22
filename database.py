import os
import sqlite3
from dataclasses import dataclass, fields
from typing import Optional, List


@dataclass
class Book:
    isbn: Optional[str] = None
    title: Optional[str] = None
    id: Optional[int] = None
    read: Optional[bool] = False


@dataclass
class LibrarySystem:
    name: Optional[str] = None
    id: Optional[int] = None


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
        self._cursor.execute(
            """
            CREATE TABLE LibrarySystem (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
            """
        )
        self._cursor.execute(
            """
            CREATE TABLE LibraryBook (
                id INTEGER PRIMARY KEY,
                library INTEGER,
                book INTEGER,
                FOREIGN KEY (library) REFERENCES Library(id),
                FOREIGN KEY (book) REFERENCES Book(id)
            )
            """
        )
        self._connection.commit()

    def add_book(self, book: Book):
        # check book doesn't already exist
        self._cursor.execute(
            """
            SELECT isbn FROM Book WHERE isbn = ? OR title = ?
            """,
            (book.isbn, book.title)
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

    def get_books(self, read=None) -> List[Book]:
        query = "SELECT isbn, title, id FROM Book"
        params = []

        if read is not None:
            query += " WHERE read = ?"
            params.append(read)

        self._cursor.execute(query, tuple(params))
        return [Book(*row) for row in self._cursor.fetchall()]

    def get_item(self, item):
        if isinstance(item, Book):
            table_name = "Book"
        elif isinstance(item, LibrarySystem):
            table_name = "LibrarySystem"
        else:
            raise TypeError

        item_fields = [f.name for f in fields(item)]

        params_query = []
        params = []
        for field in item_fields:
            value = getattr(item, field)
            if value is None:
                continue

            params_query.append(f"{field} = ?")
            params.append(value)

        query = f"""
            SELECT {', '.join(item_fields)} 
            FROM {table_name} 
            WHERE {' AND '.join(params_query)}
        """

        self._cursor.execute(query, params)
        rows = self._cursor.fetchall()

        if len(rows) == 0:
            raise RuntimeError("Item not found.")
        if len(rows) > 1:
            raise RuntimeError("Query satisfies more than one item.")

        row, = rows
        for field, value in zip(item_fields, row):
            setattr(item, field, value)

    def get_items(self):
        # TODO:
        raise NotImplemented

    def check_item_exists(self, item):
        if isinstance(item, Book):
            table_name = "Book"
        elif isinstance(item, LibrarySystem):
            table_name = "LibrarySystem"
        else:
            raise TypeError

        item_fields = [f.name for f in fields(item)]

        params_query = []
        params = []
        for field in item_fields:
            value = getattr(item, field)
            if value is None:
                continue

            params_query.append(f"{field} = ?")
            params.append(value)

        query = f"""
            SELECT {', '.join(item_fields)} 
            FROM {table_name} 
            WHERE {' AND '.join(params_query)}
        """

        self._cursor.execute(query, params)
        rows = self._cursor.fetchall()

        return len(rows) > 0

    def add_library_book(
        self,
        library: LibrarySystem,
        book: Book,
    ):
        # get ids
        if library.id is None:
            self.get_item(library)
        if book.id is None:
            self.get_item(book)

        self._cursor.execute(
            """
            SELECT * FROM LibraryBook
            WHERE library = ? AND book = ?
            """,
            (library.id, book.id),
        )
        if self._cursor.fetchone() is not None:
            return

        self._cursor.execute(
            """
            INSERT INTO LibraryBook (library, book)
            VALUES (?, ?)
            """,
            (library.id, book.id),
        )
        self._connection.commit()

    def add_library_system(self, library: LibrarySystem):
        # check library doesn't already exist
        self._cursor.execute(
            """
            SELECT name FROM LibrarySystem WHERE name = ?
            """,
            (library.name,)
        )
        if len(self._cursor.fetchall()) > 0:
            return

        # add library
        self._cursor.execute(
            """
            INSERT INTO LibrarySystem (name)
            VALUES (?)
            """,
            (library.name,)
        )
        self._connection.commit()

    def get_books_for_library_system(self, library: LibrarySystem):
        if library.id is None:
            self.get_item(library)

        self._cursor.execute(
            """
            SELECT Book.isbn, Book.title, Book.id, Book.read
            FROM LibraryBook
            INNER JOIN Book ON Book.id = LibraryBook.book
            WHERE LibraryBook.library = ?
            """,
            (library.id,),
        )

        return [Book(*row) for row in self._cursor.fetchall()]

    def get_libraries(self):
        self._cursor.execute(
            """
            SELECT id, name FROM LibrarySystem
            """
        )
        return [
            LibrarySystem(name, id_)
            for id_, name in self._cursor.fetchall()
        ]

    def check_book_in_library(self, book: Book, library: LibrarySystem):
        self._cursor.execute(
            """
            SELECT *
            FROM LibraryBook
            WHERE book = ? AND library = ?
            """,
            (book.id, library.id),
        )
        return len(self._cursor.fetchall()) > 0


def main():
    database = Database("database.db")
    library = LibrarySystem("Nottingham City Libraries")
    for book in database.get_books_for_library_system(library):
        print(book)


if __name__ == "__main__":
    main()
