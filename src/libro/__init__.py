import os
import time

import flet as ft

from .storage.paths import LibroPaths
from .model.statistics import Statistics
from .model.reading import ReadingInfo
from .model.book import Book
from .storage.json import JsonDirectoryStorage, JsonFileStorage
from .view.main import MainView


class Libro(MainView):
    def __init__(self):
        super().__init__()

        self.app_page: ft.Page | None = None

        self.books_storage = JsonDirectoryStorage[Book].from_directory(
            item_cls=Book,
            directory=LibroPaths.books()
        )
        self.reading_storage = JsonDirectoryStorage[ReadingInfo].from_directory(
            item_cls=ReadingInfo,
            directory=LibroPaths.reading()
        )
        self.statistics_storage = JsonFileStorage[Statistics].from_directory(
            item_cls=Statistics,
            path=LibroPaths.statistics()
        )

        self.lib_tab.update_books(self.books_storage.objects)
        self.reading_tab.update_reading_books(self.reading_storage.objects, self.books_storage.objects)

        def search_predicate(book: Book, query: str) -> bool:
            matches = False
            matches |= query.lower() in book.title.lower()
            matches |= query.lower() in book.author.full_name().lower()
            matches |= query.lower() in (book.summary or "").lower()
            matches |= query.lower() in (book.cover or "").lower()

            return matches

        self.lib_tab.register_search_predicate(search_predicate)

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
        self.app_page.window.min_width = 1080
        self.app_page.window.min_height = 540

        self.app_page.title = "Libro - Your Personal Library"
        self.app_page.vertical_alignment = ft.MainAxisAlignment.CENTER
        self.app_page.padding = ft.Padding.zero()
        self.app_page.add(self)

    def run(self):
        ft.run(self.app, assets_dir=str(LibroPaths.assets().absolute()))


def main():
    LibroPaths.root().mkdir(exist_ok=True)
    Libro().run()


if __package__ is not None:
    import importlib.resources
    import shutil

    MODULE_PATH = importlib.resources.files(__package__)
    RESOURCES_PATH = str(MODULE_PATH / "assets")

    # If the LibroPaths.RESOURCES folder doesn't exist, We should copy all our default assets
    def copy_if_absent(src: str, dst: str, *, follow_symlinks: bool = True):
        if os.path.exists(dst):
            if os.path.isdir(dst):
                raise FileExistsError(f"directory exists with the same name as destination the file: {dst}")
            return
        shutil.copy2(src, dst, follow_symlinks=follow_symlinks)

    def copy_default_resources():
        os.makedirs(LibroPaths.assets(), exist_ok=True)
        shutil.copytree(RESOURCES_PATH, LibroPaths.assets(), dirs_exist_ok=True, copy_function=copy_if_absent)

    copy_default_resources()


if __name__ == "__main__":
    main()
