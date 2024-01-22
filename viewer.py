import PySimpleGUI as sg

from database import Database


class FilterTable(sg.Table):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters = [None] * len(self.ColumnHeadings)

    def filter(self, col: int):
        # prompt user for desired value
        column_name = self.ColumnHeadings[col]
        value = sg.popup_get_text(f"Filter {column_name}: ")

        # update table
        table_data = self.Values
        new_table_data = []
        for row in table_data:
            if row[col] == value:
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
        ]
        for library in database.get_libraries():
            present = database.check_book_in_library(book, library)
            _book_data.append("yes" if present else "no")

        book_data.append(_book_data)

    library_names = [library.name for library in database.get_libraries()]

    # create table
    table = FilterTable(
        book_data,
        headings=["Title", "Read"] + library_names,
        enable_click_events=True,
    )

    return table


def main():
    # TODO: subclass Table
    # TODO: display filters
    # TODO: clear filters
    # TODO: add searching for books
    # TODO: add tags to books

    sg.theme("DarkTeal2")

    database = Database("database.db")
    table = create_table(database)

    # main UI
    layout = [
        [table],
    ]
    window = sg.Window(
        "Books",
        layout,
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
