import argparse
import asyncio
from typing import Optional

import aiohttp
from bs4 import BeautifulSoup
from Levenshtein import distance
from yarl import URL

from database import Book, Database, LibrarySystem

library = LibrarySystem("Nottingham City Libraries")


async def add_book_to_database(
    book: Book, database: Database, session: aiohttp.ClientSession
):
    url = await get_book(book, session)
    if url is None:
        return None

    database.add_library_book(library, book)
    return url


def check_titles(title_1, title_2):
    return distance(title_1.lower(), title_2.lower()) < 10


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


async def get_book(
    book: Book,
    session: aiohttp.ClientSession,
) -> Optional[URL]:
    """Search Nottingham Libraries for the book

    :return: If the book is found, a URL to the
    search results or the book is returned. Else,
    None is returned.
    """
    url = f"https://emlib.ent.sirsidynix.net.uk/client/en_GB/nottcity/search/results"
    params = {
        "qu": book.title
    }
    async with session.get(url=url, params=params) as response:
        content = await response.read()

        with open(book.title + ".html", "w") as f:
            f.write(content.decode())

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
        default="database.db",
        help="Path to database containing books to check.",
    )

    args = parser.parse_args()

    database = Database(args.database)
    database.add_library_system(library)

    async with aiohttp.ClientSession() as session:
        tasks = []
        books = database.get_books()[:10]
        for book in books:
            task = asyncio.ensure_future(get_book(book, session))
            tasks.append(task)

        urls = await asyncio.gather(*tasks)
        for url, book in zip(urls, books):
            print(book.title, url)


if __name__ == "__main__":
    asyncio.run(main())