import argparse
import os
from configparser import ConfigParser
from multiprocessing.pool import ThreadPool
from threading import current_thread
from typing import Optional, Dict
from urllib.parse import urlencode, quote

from selenium import webdriver
from selenium.webdriver import FirefoxProfile
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.firefox.options import Options
from yarl import URL

from check_libraries.common import check_titles
from database import Book, Database, LibrarySystem

library = LibrarySystem("Nottingham University")

# One webdriver for each thread. Maps thread name to driver.
webdrivers: Dict[str, WebDriver] = {}


def get_book(
    book: Book,
    driver: WebDriver,
) -> Optional[URL]:
    """Search Nottingham University library for the book

    :return: If the book is found, a URL to the
    search results or the book is returned. Else,
    None is returned.
    """

    driver.implicitly_wait(10.0)

    # open page
    url = "https://nusearch.nottingham.ac.uk/primo-explore/search"
    params = {
        "query": f"any,contains,{book.title}",
        "tab": "44notuk_complete",
        "search_scope": "44NOTUK_COMPLETE",
        "vid": "44NOTUK",
        "offset": "0",
        "facet": "rtype,exclude,reviews,lk",
    }
    query_string = "?" + urlencode(params, quote_via=quote, safe=",")
    driver.get(url + query_string)

    # get list of book title elements on the search results page
    search_results_div = driver.find_element(
        by=By.ID,
        value="mainResults",
    )
    book_titles = search_results_div.find_elements(by=By.CLASS_NAME, value="item-title")

    # check titles
    for book_title in book_titles:
        # Check title. Sometimes the title is shown as "title / author", so check for
        # this case as well.
        candidate_titles = [book_title.text] + book_title.text.split("/")
        if all((not check_titles(book.title, t) for t in candidate_titles)):
            continue

        # return url of book
        link = book_title.find_element(by=By.TAG_NAME, value="a")
        return link.get_attribute("href")

    return None


def process_book(
    book: Book,
    database_path: str,
) -> Optional[URL]:
    driver = webdrivers[current_thread().name]
    url = get_book(book, driver)

    database = Database(database_path)
    database.add_library_book(library, book, url is not None)

    print(book.title, url)

    return url


def main():
    root = os.path.dirname(__file__)

    parser = argparse.ArgumentParser(
        prog="check_nottingham_libraries",
        description="Check which books are available in Nottingham libraries.",
    )
    parser.add_argument(
        "-d",
        "--database",
        type=str,
        default=os.path.join(root, "..", "database.db"),
        help="Path to database containing books to check.",
    )
    parser.add_argument(
        "-n",
        "--num-workers",
        type=int,
        default=10,
        help="Number of threads to use.",
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

    # open config file
    config_path = os.path.join(root, "..", "config.ini")
    config_parser = ConfigParser()
    config_parser.read(config_path)

    # webdriver options
    options = Options()
    options.binary = FirefoxBinary(
        config_parser.get("firefox", "executable")
    )
    options.profile = FirefoxProfile(
        config_parser.get("firefox", "profile")
    )
    options.add_argument("--headless")

    # open database
    database = Database(args.database)
    database.add_library_system(library)

    if args.clear:
        database.clear_library_books(library)

    # get books from database
    books = database.get_books()

    if not args.force:
        # only check books that haven't been checked yet
        books = [
            book
            for book in books
            if database.check_book_in_library(book, library) is None
        ]

    # initialise thread pool, and one selenium webdriver for each thread

    def init():
        driver = webdriver.Firefox(options=options)
        webdrivers[current_thread().name] = driver

    pool = ThreadPool(args.num_workers, init)

    # process books
    pool.starmap(
        process_book,
        ((book, args.database) for book in books),
    )


if __name__ == "__main__":
    main()
