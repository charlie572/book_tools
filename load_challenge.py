import argparse
import urllib
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from database import Database, Book, Challenge, NotFound


def iter_challenge_pages(challenge_id):
    page = 1
    while True:
        url = f"https://app.thestorygraph.com/reading_challenges/{challenge_id}"
        params = {
            "page": page,
            "_": 1724694396276,
        }
        response = requests.get(url, params=params)
        soup = BeautifulSoup(response.text, "html.parser")
        yield soup
        page += 1


def main():
    parser = argparse.ArgumentParser(
        prog="load_challenge",
        description="Load a StoryGraph book challenge.",
    )
    parser.add_argument(
        "challenge_url",
        type=str,
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

    url = urlparse(args.challenge_url)
    challenge_id = url.path.split("/")[-1]

    for soup in iter_challenge_pages(challenge_id):
        title = soup.find("h5")
        challenge_name = title.text

        challenge = Challenge(challenge_name)
        database.add_challenge(challenge)

        book_added = False
        for link in soup.find_all("a"):
            if not link.attrs["href"].startswith("/books"):
                continue

            # get title
            lines = [line for line in link.text.split("\n") if line]
            book_title = lines[0]

            # search for book
            book = Book(title=book_title)
            if not database.get_book(book):
                continue

            # add to challenge
            database.add_book_to_challenge(book, challenge)

            book_added = True

        if not book_added:
            break


if __name__ == "__main__":
    main()
