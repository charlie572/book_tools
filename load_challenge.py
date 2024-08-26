import argparse

import requests
from bs4 import BeautifulSoup

from database import Database, Book, Challenge, NotFound


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

    response = requests.get(args.challenge_url)
    soup = BeautifulSoup(response.text, "html.parser")

    title = soup.find("h5")
    challenge_name = title.text

    challenge = Challenge(challenge_name)
    database.add_challenge(challenge)

    for link in soup.find_all("a"):
        if not link.attrs["href"].startswith("/books"):
            continue

        # get title
        lines = [line for line in link.text.split("\n") if line]
        book_title = lines[0]

        # search for book
        book = Book(title=book_title)
        try:
            database.get_item(book)
        except NotFound:
            continue

        # add to challenge
        database.add_book_to_challenge(book, challenge)


if __name__ == "__main__":
    main()
