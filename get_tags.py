import argparse
import asyncio

import aiohttp
from bs4 import BeautifulSoup

from database import Database, Book


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

    # TODO: don't search for tags twice

    async with aiohttp.ClientSession() as session:
        tasks = []
        for book in books:
            task = asyncio.ensure_future(get_tags(book, session))
            tasks.append(task)

        tags = await asyncio.gather(*tasks)

        # print output
        for tag_list, book in zip(tags, books):
            print(book.title, tag_list)

    # update database
    for tag_list, book in zip(tags, books):
        database.add_book_tags(book, tag_list)


if __name__ == "__main__":
    asyncio.run(main())
