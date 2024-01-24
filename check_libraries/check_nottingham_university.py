import os
from configparser import ConfigParser
from typing import Optional
from urllib.parse import urlencode, quote

import aiohttp
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver import FirefoxProfile
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.firefox.options import Options
from yarl import URL

from database import Book


def get_book_nottingham_university(
    book: Book,
) -> Optional[URL]:
    """Search Nottingham University library for the book

    :return: If the book is found, a URL to the
    search results or the book is returned. Else,
    None is returned.
    """
    # url = "https://nusearch.nottingham.ac.uk/primo-explore/search"
    # params = {
    #     "query": f"any,contains,{book.title}",
    #     # "tab": "44notuk_complete",
    #     # "search_scope": "44NOTUK_COMPLETE",
    #     # "vid": "44NOTUK",
    #     # "offset": "0",
    #     # "facet": "rtype,exclude,reviews,lk",
    # }

    # guest_api_url = "https://nusearch.nottingham.ac.uk/primo/v1/jwt/44NOTUK"

    root = os.path.dirname(__file__)
    config_path = os.path.join(root, "..", "config.ini")

    parser = ConfigParser()
    parser.read(config_path)

    # instantiate driver
    options = Options()
    options.binary = FirefoxBinary(parser.get("firefox", "executable"))
    options.profile = FirefoxProfile(parser.get("firefox", "profile"))
    # options.add_argument("--headless")
    driver = webdriver.Firefox(options=options)

    driver.implicitly_wait(10.0)

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

    search_results_div = driver.find_element(
        by=By.ID,
        value="mainResults",
    )
    book_titles = search_results_div.find_elements(by=By.CLASS_NAME, value="item-title")
    print(book_titles)
    for book_title in book_titles:
        print(book_title, book_title.text)



def main():
    book = Book(title="Cannery Row")
    get_book_nottingham_university(book)


if __name__ == "__main__":
    main()
