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
    return sg.Table(
        book_data,
        headings=["Title", "Read"] + library_names,
    )


def main():
    sg.theme("DarkTeal2")

    database = Database("database.db")
    table = create_table(database)

    # main UI
    layout = [
        [table],
    ]
    window = sg.Window("Books", layout)

    # main loop
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == "Cancel":
            break

    window.close()


if __name__ == "__main__":
    main()
