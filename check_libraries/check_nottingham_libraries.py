import argparse
import asyncio
import os
from typing import Optional

import aiohttp
from bs4 import BeautifulSoup
from yarl import URL

from check_libraries.common import check_titles
from database import Book, Database, LibrarySystem

library = LibrarySystem("Nottingham City Libraries")


def find_book_in_search_results(results_div, book_title):
    results_div = results_div.find(
        "div",
        {
            "class": "results_every_four"
        }
    )
    for book_div in results_div.findChildren("div", recursive=False):
        title_div = book_div.find("div", {"class": "displayDetailLink"})
        title = title_div.text
        if check_titles(title, book_title):
            return title_div

    return None


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

    url = f"https://emlib.ent.sirsidynix.net.uk/client/en_GB/nottcity/search/results"
    params = {
        "qu": search_term
    }
    async with session.get(url=url, params=params) as response:
        content = await response.read()

        soup = BeautifulSoup(content, "html.parser")

        # If there is only one search result, we are redirected to the page for
        # the book, instead of a search results page. Check the page title to
        # see if this has happened.
        title = soup.find("title").text
        if not title.startswith("Search Results"):
            return response.url

        # Find the div containing the search results.
        results_div = soup.find("div", {"id": "results_wrapper"})
        if results_div is None:
            return None

        # Check if the book is in the search results.
        if find_book_in_search_results(results_div, book.title):
            return response.url

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
