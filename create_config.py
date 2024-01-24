import json
from configparser import ConfigParser
from datetime import datetime


def main():
    parser = ConfigParser()

    parser.add_section("firefox")
    parser.set("firefox", "executable", "")
    parser.set("firefox", "profile", "")

    with open("config.ini", "w") as f:
        parser.write(f)

    with open("state.json", "w") as f:
        json.dump(
            {"next_backup": datetime.now().timestamp(), "state": "idle"},
            f,
        )


if __name__ == "__main__":
    main()
