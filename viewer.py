import argparse
from copy import deepcopy

import PySimpleGUI as sg
from Levenshtein import distance

from database import Database


class FilterTable(sg.Table):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters = [None] * len(self.ColumnHeadings)
        self.original_values = self.Values.copy()

    def filter(self, col: int):
        # prompt user for desired value
        column_name = self.ColumnHeadings[col]
        value = sg.popup_get_text(
            f"Filter {column_name}: ",
            default_text=self.filters[col] or "",
        )

        if value is None:
            return

        # update filters
        self.filters[col] = value
        if self.filters[col] == "":
            # clear filter
            self.filters[col] = None

        self.apply_filters()

    def apply_filters(self):
        new_table_data = []
        for row in self.original_values:
            for column, filtered_value, value in zip(
                self.ColumnHeadings, self.filters, row
            ):
                if filtered_value is None:
                    continue

                if column in ("Tags", "Authors"):
                    # check all filter tags are present
                    row_tags = value.split(", ")
                    filter_tags = filtered_value.split(", ")
                    if len(set(filter_tags).difference(row_tags)) > 0:
                        break
                    else:
                        continue

                if column == "Title":
                    if filtered_value.lower() not in value.lower():
                        break
                    else:
                        continue

                # check filter value is equal to row value
                if value != filtered_value:
                    break
            else:
                new_table_data.append(row)

        self.update(values=new_table_data)

    def process_event(self, event):
        if event[:2] == (0, "+CLICKED+"):
            _, _, (row, col) = event
            if row == -1:
                self.filter(col)


def create_table(database: Database):
    # load from database
    book_data = []
    for book in database.get_books():
        _book_data = [
            book.title,
            "yes" if book.read else "no",
            ", ".join(database.get_book_tags(book)),
            ", ".join(challenge.name for challenge in database.get_book_challenges(book)),
            ", ".join(author.name for author in book.authors)
        ]
        for library in database.get_libraries():
            present = database.check_book_in_library(book, library)

            if present is None:
                value = ""
            elif present:
                value = "yes"
            else:
                value = "no"

            _book_data.append(value)

        for shop in database.get_shops():
            present, price = database.check_book_in_shop(book, shop)
            _book_data.append(price or "")

        book_data.append(_book_data)

    if len(database.get_shops()) > 0:
        book_data.sort(key=lambda x: x[-1] or 0)

    library_names = [library.name for library in database.get_libraries()]
    shop_names = [shop.name for shop in database.get_shops()]

    # create table
    table = FilterTable(
        book_data,
        headings=["Title", "Read", "Tags", "Challenges", "Authors"] + library_names + shop_names,
        enable_click_events=True,
        size=(800, 600)
    )

    return table


def main():
    parser = argparse.ArgumentParser(
        "viewer",
        description="View a database in a window."
    )
    parser.add_argument(
        "database",
        type=str,
        default="database.db",
        help="Path to database view."
    )

    args = parser.parse_args()
    # TODO: wrap text in table

    sg.theme("DarkTeal2")

    database = Database(args.database)
    table = create_table(database)

    # main UI
    layout = [
        [table],
    ]
    window = sg.Window(
        "Books",
        layout,
        size=(800, 600)
    )

    # main loop
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break

        table.process_event(event)

    window.close()


if __name__ == "__main__":
    main()
