import argparse
import asyncio
import os
import re
from typing import Optional, Tuple

import aiohttp
from bs4 import BeautifulSoup
from yarl import URL

from check_libraries.common import check_titles
from database import Book, Database, Shop

shop = Shop("Abe Books")


async def process_book(
    book: Book,
    database: Database,
    session: aiohttp.ClientSession,
) -> Optional[URL]:
    url, price = await get_book(book, session)
    database.add_book_in_shop(shop, book, url is not None, price)
    print(book.title, url, price)
    return url


async def get_book(
    book: Book,
    session: aiohttp.ClientSession,
) -> Tuple[Optional[URL], Optional[float]]:
    """Search AbeBooks for the book

    :return: If the book is found, a URL to the
    search results or the book is returned, and
    the price. Else, (None, None) is returned.
    """
    url = "https://www.abebooks.co.uk/servlet/SearchResults"

    if len(book.authors) == 0:
        # search without author
        search_term = book.title.lower().strip()
        if search_term.startswith("the "):
            search_term = search_term[4:]

        params = {
            "cm_sp": "SearchF-_-home-_-Results",
            "ds": 20,
            "kn": search_term,
            "sts": "t",
        }
    else:
        # search with author
        params = {
            "an": book.authors[0].name,
            "bi": 0,
            "bx": "off",
            "cm_sp": "SearchF-_-Advs-_-Result",
            "ds": 30,
            "kn": book.title,
            "prc": "GBP",
            "recentlyadded": "all",
            "rgn": "ww",
            "rollup": "on",
            "sortby": 17,
            "xdesc": "off",
            "xpod": "off",
        }

    async with session.get(url=url, params=params) as response:
        content = await response.read()

        soup = BeautifulSoup(content, "html.parser")

        # Find the div containing the search results.
        results_div = soup.find("div", {"class": "result-set"})
        if results_div is None:
            return None, None

        # Check if the book is in the search results.
        book_li = results_div.find("li", {"class": "result-item"})
        if book_li is None:
            return None, None

        # Find price.
        price_p = book_li.find("p", {"class": "item-price"})
        if price_p is None:
            return None, None
        price_text = price_p.text.split("£")[-1]
        price = float("".join(c for c in price_text if c.isnumeric() or c == "."))

        # Find shipping.
        shipping_span = book_li.find("span", {"class": "item-shipping"})
        if shipping_span is not None:
            shipping_text = shipping_span.text
            match = re.match(r"£\s*(\d+(\.\d+)?)\s*Shipping", shipping_text)
            if match is not None:
                price += float(match.group(1))

        return response.url, price


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
    database.add_shop(shop)

    if args.clear:
        database.clear_shop_books(shop)

    books = database.get_books()

    if not args.force:
        # only check books that haven't been checked yet
        books = [
            book
            for book in books
            if database.check_book_in_shop(book, shop)[0] is None
        ]

    # If you make too many requests, you get banned, so the number of threads has been limited to 10. I don't know how
    # many more it still works with.
    connector = aiohttp.TCPConnector(limit=10)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []
        for book in books:
            task = asyncio.ensure_future(process_book(book, database, session))
            tasks.append(task)

        await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
