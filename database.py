import os
import sqlite3
from dataclasses import dataclass, fields
from typing import Optional, List, Iterable, Tuple
from xml.dom import NotFoundErr


@dataclass
class Book:
    isbn: Optional[str] = None
    title: Optional[str] = None
    id: Optional[int] = None
    read: Optional[bool] = False
    tags_searched: Optional[bool] = False


@dataclass
class LibrarySystem:
    name: Optional[str] = None
    id: Optional[int] = None

@dataclass
class Challenge:
    name: Optional[str] = None
    id: Optional[int] = None

@dataclass
class Shop:
    name: Optional[str] = None
    id: Optional[int] = None


@dataclass
class Tag:
    name: Optional[str] = None
    id: Optional[int] = None


class NotFound(Exception):
    pass


def first(iterable, pred):
    for item in iterable:
        if pred(item):
            return item

    raise RuntimeError("None satisfy predicate.")


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
                read BOOLEAN,
                tags_searched BOOLEAN
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
            CREATE TABLE Shop (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
            """
        )
        self._cursor.execute(
            """
            CREATE TABLE Challenge (
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
            CREATE TABLE ChallengeBook (
                id INTEGER PRIMARY KEY,
                challenge INTEGER,
                book INTEGER,
                FOREIGN KEY (challenge) REFERENCES Challenge(id),
                FOREIGN KEY (book) REFERENCES Book(id)
            )
            """
        )
        self._cursor.execute(
            """
            CREATE TABLE ShopBook (
                id INTEGER PRIMARY KEY,
                shop INTEGER,
                book INTEGER,
                present BOOLEAN,
                price FLOAT,
                FOREIGN KEY (shop) REFERENCES Shop(id),
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

    def add_challenge(self, challenge: Challenge):
        if self.challenge_exists(challenge):
            # set challenge id
            self.get_item(challenge)
            return

        # insert book
        self._cursor.execute(
            """
            INSERT INTO Challenge (name)
            VALUES (?)
            """,
            (challenge.name,)
        )
        self._connection.commit()

        challenge.id = self._cursor.lastrowid

    def add_book(self, book: Book):
        if self.get_book(book):
            return

        # insert book
        self._cursor.execute(
            """
            INSERT INTO Book (isbn, title, read, tags_searched)
            VALUES (?, ?, ?, ?)
            """,
            (book.isbn, book.title, book.read, book.tags_searched)
        )
        self._connection.commit()

    def update_book(self, book: Book):
        # get book id and check if it exists
        if not self.get_book(book):
            raise RuntimeError("Book doesn't exist")

        # update book
        self._cursor.execute(
            """
            UPDATE Book
            SET isbn = ?, title = ?, read = ?, tags_searched = ?
            WHERE id = ?
            """,
            (book.isbn, book.title, book.read, book.tags_searched, book.id),
        )
        self._connection.commit()

    def get_books(self, read=None) -> List[Book]:
        query = "SELECT isbn, title, id, read, tags_searched FROM Book"
        params = []

        if read is not None:
            query += " WHERE read = ?"
            params.append(read)

        self._cursor.execute(query, tuple(params))
        return [Book(*row) for row in self._cursor.fetchall()]

    def get_book(self, book: Book, raise_if_not_found = False):
        fields = ["isbn", "title", "id", "read", "tags_searched"]

        # Query using book id. If not available, use isbn, etc.
        query_params = ["id", "isbn", "title"]  # decreasing order of preference
        try:
            query_param = first(query_params, lambda param: getattr(book, param) is not None)
        except RuntimeError:
            raise RuntimeError("Book parameter doesn't contain any identifiers.")
        query_param_value = getattr(book, query_param)

        query = (
            f"SELECT {', '.join(fields)}\n"
            "FROM Book\n"
            f"WHERE {query_param} = ?"
        )

        self._cursor.execute(query, (query_param_value,))
        rows = self._cursor.fetchall()

        if len(rows) == 0:
            if raise_if_not_found:
                raise NotFound("Item not found.")
            else:
                return False
        if len(rows) > 1:
            raise RuntimeError("Query satisfies more than one item.")

        row, = rows
        for field, value in zip(fields, row):
            setattr(book, field, value)

        return True

    def get_item(self, item, only_check_id = False):
        if isinstance(item, Book):
            return self.get_book(item)

        elif isinstance(item, LibrarySystem):
            table_name = "LibrarySystem"
        elif isinstance(item, Shop):
            table_name = "Shop"
        elif isinstance(item, Challenge):
            table_name = "Challenge"
        else:
            raise TypeError

        if only_check_id:
            item_fields = ["id"]
        else:
            item_fields = [f.name for f in fields(item)]

        params_query = []
        params = []
        for field in item_fields:
            if not hasattr(item, field):
                continue

            value = getattr(item, field)
            if value is None:
                continue


            params_query.append(f"{field} = ?")
            params.append(value)

        query = (
            f"SELECT {', '.join(item_fields)}\n"
            f"FROM {table_name}\n"
            f"WHERE {' AND '.join(params_query)}"
        )

        self._cursor.execute(query, params)
        rows = self._cursor.fetchall()

        if len(rows) == 0:
            raise NotFound("Item not found.")
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
                WHERE library = ? AND book = ?
                """,
                (present, library.id, book.id),
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

    def add_book_to_challenge(
        self,
        book: Book,
        challenge: Challenge,
    ):
        # get ids
        if book.id is None:
            self.get_item(book)
        if challenge.id is None:
            self.get_item(challenge)

        # check if row already exists
        self._cursor.execute(
            """
            SELECT * FROM ChallengeBook
            WHERE challenge = ? AND book = ?
            """,
            (challenge.id, book.id),
        )
        if len(self._cursor.fetchall()) > 0:
            return

        # add row
        self._cursor.execute(
            """
            INSERT INTO ChallengeBook (challenge, book)
            VALUES (?, ?)
            """,
            (challenge.id, book.id),
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

    def add_shop(self, shop: Shop):
        # check library doesn't already exist
        self._cursor.execute(
            """
            SELECT name FROM Shop WHERE name = ?
            """,
            (shop.name,)
        )
        if len(self._cursor.fetchall()) > 0:
            return

        # add library
        self._cursor.execute(
            """
            INSERT INTO Shop (name)
            VALUES (?)
            """,
            (shop.name,)
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

    def get_shops(self):
        self._cursor.execute(
            """
            SELECT id, name FROM Shop
            """
        )
        return [
            Shop(name, id_)
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

    def check_book_in_shop(
        self, book: Book, shop: Shop
    ) -> Tuple[Optional[bool], Optional[float]]:
        if book.id is None:
            self.get_item(book)
        if shop.id is None:
            self.get_item(shop)

        self._cursor.execute(
            """
            SELECT present, price
            FROM ShopBook
            WHERE book = ? AND shop = ?
            """,
            (book.id, shop.id),
        )

        query_result = self._cursor.fetchall()
        if len(query_result) == 0:
            return None, None
        else:
            present, price = query_result[0]
            return present, price

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

    def get_book_challenges(self, book: Book) -> Iterable[Challenge]:
        if book.id is None:
            self.get_item(book)

        self._cursor.execute(
            """
            SELECT Challenge.id, Challenge.name
            FROM Book
            INNER JOIN ChallengeBook ON (Book.id = ChallengeBook.book)
            INNER JOIN Challenge ON (ChallengeBook.challenge = Challenge.id)
            WHERE Book.id = ?
            """,
            (book.id,),
        )

        return [Challenge(name, id_) for (id_, name) in self._cursor.fetchall()]

    def challenge_exists(self, challenge: Challenge) -> bool:
        self._cursor.execute(
            """
            SELECT name FROM Challenge WHERE name = ?
            """,
            (challenge.name,)
        )
        return len(self._cursor.fetchall()) > 0

    def clear_library_books(self, library: LibrarySystem):
        if library.id is None:
            self.get_item(library)

        self._cursor.execute(
            """DELETE FROM LibraryBook WHERE library = ?""",
            (library.id,),
        )

    def clear_shop_books(self, shop: Shop):
        if shop.id is None:
            self.get_item(shop)

        self._cursor.execute(
            """DELETE FROM ShopBook WHERE shop = ?""",
            (shop.id,),
        )

    def add_book_in_shop(self, shop: Shop, book: Book, present: bool, price: Optional[float]):
        # get ids
        if shop.id is None:
            self.get_item(shop)
        if book.id is None:
            self.get_item(book)

        # check if row already exists
        self._cursor.execute(
            """
            SELECT * FROM ShopBook
            WHERE shop = ? AND book = ?
            """,
            (shop.id, book.id),
        )

        if self._cursor.fetchone() is not None:
            # row already exists, so set present = True
            self._cursor.execute(
                """
                UPDATE ShopBook 
                SET present = ?, price = ?
                WHERE shop = ? AND book = ?
                """,
                (present, price, shop.id, book.id),
            )
            self._connection.commit()
            return

        # add row
        self._cursor.execute(
            """
            INSERT INTO ShopBook (shop, book, present, price)
            VALUES (?, ?, ?, ?)
            """,
            (shop.id, book.id, present, price),
        )
        self._connection.commit()


def main():
    database = Database("database.db")
    for book in database.get_books():
        print(book, database.get_book_tags(book))


if __name__ == "__main__":
    main()
