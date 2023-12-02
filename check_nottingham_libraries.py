import argparse
import asyncio

import aiohttp
from bs4 import BeautifulSoup
from Levenshtein import distance

from database import Book, Database


async def get_book(book: Book, session: aiohttp.ClientSession):
    url = f"https://emlib.ent.sirsidynix.net.uk/client/en_GB/nottcity/search/results"
    params = {
        "qu": book.title[:20].replace(" ", "+")
    }
    async with session.get(url=url, params=params) as response:
        content = await response.read()

        soup = BeautifulSoup(content, "html.parser")

        results_div = soup.find("div", {"id": "results_wrapper"})
        if results_div is None:
            return None
        results_div = results_div.find("div", {"class": "results_every_four"})
        for book_div in results_div.findChildren("div", recursive=False):
            title_div = book_div.find("div", {"class": "displayDetailLink"})
            title = title_div.text
            if distance(title, book.title) < 5:
                return response.url


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

    async with aiohttp.ClientSession() as session:
        tasks = []
        for book in database.get_books()[:10]:
            task = asyncio.ensure_future(get_book(book, session))
            tasks.append(task)

        books = await asyncio.gather(*tasks)
        print(books)


if __name__ == "__main__":
    asyncio.run(main())
