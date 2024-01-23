import argparse
import asyncio

import aiohttp
from bs4 import BeautifulSoup

from database import Database, Book


async def process_book(
    book: Book,
    database: Database,
    session: aiohttp.ClientSession,
):
    tags = await get_tags(book, session)

    database.add_book_tags(book, tags)

    book.tags_searched = True
    database.update_book(book)

    print(book.title, tags)

    return tags


async def get_tags(book: Book, session: aiohttp.ClientSession):
    url = "https://app.thestorygraph.com/browse"
    params = {
        "search_term": book.title,
    }

    async with session.get(url=url, params=params) as response:
        content = await response.read()

        soup = BeautifulSoup(content, "html.parser")

        # find tags div
        results = soup.find(
            "div",
            {"class": "search-results-books"}
        )
        book_div = results.find(
            "div",
            {"class": "book-pane"}
        )
        tags_div = book_div.find(
            "div",
            {"class": "book-pane-tag-section"},
        )

        # parse tags text
        tags = tags_div.text.split("\n")
        tags = [tag.strip() for tag in tags]
        tags = [tag for tag in tags if tag != ""]

        return tags


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

    books = database.get_books()

    # don't search for tags twice
    books = [book for book in books if not book.tags_searched]

    async with aiohttp.ClientSession() as session:
        tasks = []
        for book in books:
            task = asyncio.ensure_future(process_book(book, database, session))
            tasks.append(task)

        await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
