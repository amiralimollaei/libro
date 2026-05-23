import time

import flet as ft

from .storage.paths import LibroPaths
from .model.reading import ReadingInfo
from .model.book import Book
from .storage.json import JsonObjectStorage
from .view.main import MainView


class Libro(MainView):
    def __init__(self):
        super().__init__()

        self.app_page: ft.Page | None = None

        self.books_storage = JsonObjectStorage[Book].from_directory(item_cls=Book, directory=LibroPaths.books())
        self.reading_storage = JsonObjectStorage[ReadingInfo].from_directory(item_cls=ReadingInfo, directory=LibroPaths.books() / "reading")

        self.lib_tab.update_books(self.books_storage.objects)
        self.reading_tab.update_reading_books(self.reading_storage.objects, self.books_storage.objects)

        self.add_tab.register_on_save_fn(self.on_save)
        self.reading_tab.register_on_book_dismissed_fn(self.on_book_dismissed)

    def on_save(self, e):
        assert self.app_page
        
        book = None
        try:
            book = self.add_tab.get_book_object()
        except AttributeError:
            banner = ft.AlertDialog(
                title=ft.Text("Add Book"),
                content=ft.Text("Please fill all the required fields."),
                actions=[
                    ft.TextButton(
                        "Ok",
                        on_click=lambda e: self.app_page.pop_dialog()  # pyright: ignore[reportOptionalMemberAccess]
                    )
                ],
                open=True,
            )
            self.app_page.show_dialog(banner)
            return
        
        assert book
        book.id = int(time.time() * 1000000)

        self.books_storage.add(book)
        self.books_storage.save()

        self.add_tab.reset()

        def add_to_reading_list(e):
            self.add_new_reading_book(book)
            self.app_page.pop_dialog()  # pyright: ignore[reportOptionalMemberAccess]

        banner = ft.AlertDialog(
            title=ft.Text("Add Book"),
            content=ft.Text("Book was successfully added to your library."),
            actions=[
                ft.TextButton(
                    "Dismiss",
                    on_click=lambda e: self.app_page.pop_dialog()  # pyright: ignore[reportOptionalMemberAccess]
                ),
                ft.TextButton(
                    "Add To Reading List",
                    on_click=add_to_reading_list
                )
            ],
            open=True,
        )
        self.app_page.show_dialog(banner)

        self.lib_tab.update_books(self.books_storage.objects)

        self.update()

    def add_new_reading_book(self, book: Book):
        assert book.id
        reading_info = ReadingInfo(book_id=book.id, since_timestamp=time.time())
        self.reading_storage.add(reading_info)
        self.reading_storage.save()

        self.reading_tab.update_reading_books(self.reading_storage.objects, self.books_storage.objects)

        self.update()

    def on_book_dismissed(self, reading_info: ReadingInfo, book: Book):
        print(reading_info, book)

        self.reading_storage.remove(reading_info)
        self.reading_storage.save()

        self.reading_tab.update_reading_books(self.reading_storage.objects, self.books_storage.objects)

        self.update()

    def app(self, page: ft.Page):
        self.app_page = page

        self.app_page.title = "Libro - Your Personal Library"
        self.app_page.vertical_alignment = ft.MainAxisAlignment.CENTER
        self.app_page.padding = ft.Padding.zero()
        self.app_page.add(self)

    def run(self):
        ft.run(self.app, assets_dir=str(LibroPaths.assets().absolute()))


def main():
    LibroPaths.root().mkdir(exist_ok=True)
    Libro().run()
