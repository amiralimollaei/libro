import os

import flet as ft

from .model import BookEntry, LendingEntry, Statistics
from .search.engine import BookSearchEngine
from .storage import (JsonFileStorage, JsonIdNumeralStorage, LibroPaths,
                      LibroStorage)
from .view.main import MainView


class Libro(MainView):
    def __init__(self):
        self.app_page: ft.Page | None = None

        LibroStorage.new(
            storage_cls=JsonIdNumeralStorage[BookEntry],
            item_cls=BookEntry,
            path=LibroPaths.books()
        )

        LibroStorage.new(
            storage_cls=JsonIdNumeralStorage[LendingEntry],
            item_cls=LendingEntry,
            path=LibroPaths.lending()
        )

        LibroStorage.new(
            storage_cls=JsonFileStorage[Statistics],
            item_cls=Statistics,
            path=LibroPaths.statistics()
        )

        self.book_search_engine = BookSearchEngine()

        super().__init__()

        self.lib_tab.register_search_engine(self.book_search_engine)
        self.lib_tab.update_books(Libro.get_book_storage().objects)
        self.add_tab.register_on_add_book_fn(self.on_add_book)

    @staticmethod
    def get_book_storage() -> JsonIdNumeralStorage[BookEntry]:
        return LibroStorage.get(JsonIdNumeralStorage[BookEntry], BookEntry)

    def on_add_book(self, e):
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

        book_storage = Libro.get_book_storage()
        book_storage.add(book)
        book_storage.save()

        self.add_tab.reset()

        self.app_page.show_dialog(dialog=ft.AlertDialog(
            title=ft.Text("Add Book"),
            content=ft.Text("Book was successfully added to your library."),
            actions=[
                ft.TextButton(
                    "Ok",
                    on_click=lambda e: self.app_page.pop_dialog()  # pyright: ignore[reportOptionalMemberAccess]
                )
            ],
            open=True,
        ))

        self.update()

    def app(self, page: ft.Page):
        page.window.min_width = 1080
        page.window.min_height = 720

        page.title = "Libro - Your Personal Library"
        page.vertical_alignment = ft.MainAxisAlignment.CENTER
        page.padding = ft.Padding.zero()
        page.add(ft.SafeArea(self, expand=True))

        self.app_page = page

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
