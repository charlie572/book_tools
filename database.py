import os
import sqlite3
from dataclasses import dataclass, fields
from typing import Optional, List, Iterable


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


@dataclass
class Tag:
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
                present BOOLEAN,
                FOREIGN KEY (library) REFERENCES Library(id),
                FOREIGN KEY (book) REFERENCES Book(id)
            )
            """
        )
        self._cursor.execute(
            """
            CREATE TABLE Tag (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
            """
        )
        self._cursor.execute(
            """
            CREATE TABLE BookTag (
                id INTEGER PRIMARY KEY,
                book INTEGER,
                tag INTEGER,
                FOREIGN KEY (book) REFERENCES Book(id),
                FOREIGN KEY (tag) REFERENCES Tag(id)
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
        present: bool,
    ):
        # get ids
        if library.id is None:
            self.get_item(library)
        if book.id is None:
            self.get_item(book)

        # check if row already exists
        self._cursor.execute(
            """
            SELECT * FROM LibraryBook
            WHERE library = ? AND book = ?
            """,
            (library.id, book.id),
        )

        if self._cursor.fetchone() is not None:
            # row already exists, so set present = True
            self._cursor.execute(
                """
                UPDATE LibraryBook 
                SET present = ? 
                WHERE library = ? AND book =?
                """,
                (library.id, book.id, present),
            )
            self._connection.commit()
            return

        # add row
        self._cursor.execute(
            """
            INSERT INTO LibraryBook (library, book, present)
            VALUES (?, ?, ?)
            """,
            (library.id, book.id, present),
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

    def check_book_in_library(
            self, book: Book, library: LibrarySystem
    ) -> Optional[bool]:
        if book.id is None:
            self.get_item(book)
        if library.id is None:
            self.get_item(library)

        self._cursor.execute(
            """
            SELECT present
            FROM LibraryBook
            WHERE book = ? AND library = ?
            """,
            (book.id, library.id),
        )

        query_result = self._cursor.fetchall()
        if len(query_result) == 0:
            return None
        else:
            present, = query_result[0]
            return present

    def add_book_tags(self, book: Book, tags: Iterable[str]):
        if book.id is None:
            self.get_item(book)

        # ignore existing tags
        existing_book_tags = self.get_book_tags(book)
        tags = [tag for tag in tags if tag not in existing_book_tags]

        # add each tag
        for tag in tags:
            # check if tag exists
            self._cursor.execute(
                """
                SELECT id
                FROM Tag
                WHERE name = ?
                """,
                (tag,),
            )
            tag_ids = self._cursor.fetchall()
            if len(tag_ids) == 0:
                # tag doesn't exist, so add it
                self._cursor.execute(
                    """INSERT INTO Tag(name) VALUES (?)""",
                    (tag,),
                )
                tag_id = self._cursor.lastrowid
            else:
                # tag exists
                tag_id, = tag_ids[0]

            # check if tag is already added
            self._cursor.execute(
                """SELECT * FROM BookTag WHERE book = ? AND tag = ?""",
                (book.id, tag_id),
            )
            if len(self._cursor.fetchall()) > 0:
                continue

            # add tag
            self._cursor.execute(
                """INSERT INTO BookTag(book, tag) VALUES (?, ?)""",
                (book.id, tag_id),
            )

        self._connection.commit()

    def get_book_tags(self, book: Book):
        if book.id is None:
            self.get_item(book)

        self._cursor.execute(
            """
            SELECT Tag.name
            FROM Book
            INNER JOIN BookTag ON (Book.id = BookTag.book)
            INNER JOIN Tag ON (BookTag.tag = Tag.id)
            WHERE Book.id = ?
            """,
            (book.id,),
        )

        return [tag_name for (tag_name,) in self._cursor.fetchall()]


def main():
    database = Database("database.db")
    for book in database.get_books():
        print(book, database.get_book_tags(book))


if __name__ == "__main__":
    main()
