import json
from configparser import ConfigParser
from datetime import datetime


def main():
    parser = ConfigParser()

    parser.add_section("firefox")

    # This is the path to the firefox executable. It has to be in /opt. You cannot
    # have firefox installed with snap at the same time.
    parser.set("firefox", "executable", "")

    # you can find this path in the "about:profiles" page in firefox
    parser.set("firefox", "profile", "")

    with open("config.ini", "w") as f:
        parser.write(f)


if __name__ == "__main__":
    main()
