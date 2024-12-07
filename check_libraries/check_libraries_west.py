import argparse
import asyncio
import os
from typing import Optional

import aiohttp
from bs4 import BeautifulSoup
from yarl import URL

from check_libraries.common import check_titles
from database import Book, Database, LibrarySystem

library = LibrarySystem("Libraries West")


async def process_book(
    book: Book,
    database: Database,
    session: aiohttp.ClientSession,
) -> Optional[URL]:
    url = await get_book(book, session)
    database.add_library_book(library, book, url is not None)
    print(book.title, url)
    return url


async def get_book(
    book: Book,
    session: aiohttp.ClientSession,
) -> Optional[URL]:
    """Search Nottingham Libraries for the book

    :return: If the book is found, a URL to the
    search results or the book is returned. Else,
    None is returned.
    """
    search_term = book.title.lower().strip()
    if search_term.startswith("the "):
        search_term = search_term[4:]

    url = f"https://www.librarieswest.org.uk/search"
    params = {
        "p_pid": "searchResult_WAR_arenaportlet",
        "p_p_lifecycle": "1",
        "p_p_state": "normal",
        "p_r_p_arena_urn:arena_facet_queries": "",
        "p_r_p_arena_urn:arena_search_query": search_term,
        "p_r_p_arena_urn:arena_search_type": "solr",
        "p_r_p_arena_urn:arena_sort_advice": "field=Relevance&direction=Descending",
    }
    async with session.get(url=url, params=params) as response:
        content = await response.read()

        soup = BeautifulSoup(content, "html.parser")

        book_divs = soup.find_all("div", {"class": "arena-record"})
        for book_div in book_divs:
            title_div = book_div.find("div", {"class": "arena-record-title"})
            title = title_div.text.split("/")[0].strip()
            if check_titles(title, book.title):
                link = title_div.contents[1]
                return link.attrs["href"]

        return None


async def main():
    parser = argparse.ArgumentParser(
        prog="check_nottingham_libraries",
        description="Check which books are available in Nottingham libraries.",
    )
    parser.add_argument(
        "-d",
        "--database",
        type=str,
        default=os.path.join(os.path.dirname(__file__), "..", "database.db"),
        help="Path to database containing books to check.",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Search for all books, even if they have been searched before.",
    )
    parser.add_argument(
        "-c",
        "--clear",
        action="store_true",
        help="Clear database of entries for this library before starting.",
    )

    args = parser.parse_args()

    database = Database(args.database)
    database.add_library_system(library)

    if args.clear:
        database.clear_library_books(library)

    books = database.get_books()

    if not args.force:
        # only check books that haven't been checked yet
        books = [
            book
            for book in books
            if database.check_book_in_library(book, library) is None
        ]

    async with aiohttp.ClientSession() as session:
        tasks = []
        for book in books:
            task = asyncio.ensure_future(process_book(book, database, session))
            tasks.append(task)

        await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
