import PySimpleGUI as sg

from database import Database


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
    table = sg.Table(
        book_data,
        headings=["Title", "Read"] + library_names,
        enable_click_events=True,
    )

    return table


def filter_table(table: sg.Table, col: int):
    # prompt user for desired value
    column_name = table.ColumnHeadings[col]
    value = sg.popup_get_text(f"Filter {column_name}: ")

    # update table
    table_data = table.Values
    new_table_data = []
    for row in table_data:
        if row[col] == value:
            new_table_data.append(row)

    table.update(values=new_table_data)


def main():
    # TODO: add filtering columns
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
        if event == sg.WIN_CLOSED or event == "Cancel":
            break
        elif event[:2] == (0, "+CLICKED+"):
            _, _, (row, col) = event
            if row == -1:
                filter_table(table, col)

    window.close()


if __name__ == "__main__":
    main()
