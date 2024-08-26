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
        book_title = "".join(c for c in book_title if c.isalnum() or c.isspace())  # the titles in the database don't have punctuation

        # search for book
        book = Book(title=book_title)
        if not database.get_book(book):
            continue

        # add to challenge
        database.add_book_to_challenge(book, challenge)


if __name__ == "__main__":
    main()
