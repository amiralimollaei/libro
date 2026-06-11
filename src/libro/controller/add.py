import flet as ft

from ..model import BookEntry
from ..storage import JsonIdNumeralStorage, LibroStorage
from ..view.builder import TabsBuilder
from ..view.tabs.add import AddTab, OnAddBookCtx
from .base import AbstractController


class AddBookController(AbstractController):
    """Controller for the Add Book tab.

    Handles book creation, validation, and navigation after a successful add.
    """

    def __init__(self, page: ft.Page, view: AddTab, builder: "TabsBuilder", lib_tab):
        super().__init__(page)
        self.view = view
        self.builder = builder
        self.lib_tab = lib_tab

    # ---- Storage helpers ----

    @staticmethod
    def _book_storage() -> JsonIdNumeralStorage[BookEntry]:
        return LibroStorage.get(JsonIdNumeralStorage[BookEntry], BookEntry)

    # ---- Callback registration ----

    def register_callbacks(self) -> None:
        self.view.register_on_add_book_callback(self.on_add_book)

    # ---- Business logic ----

    def on_add_book(self, e):
        """Handle the 'Save to Library' button click."""
        book = None
        try:
            book = self.view.get_book_object()
        except AttributeError:
            banner = ft.AlertDialog(
                title=ft.Text("Add Book"),
                content=ft.Text("Please fill all the required fields."),
                actions=[
                    ft.TextButton(
                        "Ok",
                        on_click=lambda e: self.page.pop_dialog(),
                    )
                ],
                open=True,
            )
            self.page.show_dialog(banner)
            return

        self._book_storage().add(book)
        self._book_storage().save()

        self.view.reset()

        # Navigate back to Library tab after successful add
        self.builder.select_nav_index(0)
        self.builder.show_library_tab(self.lib_tab)

        # Show snackbar after navigation
        self.page.show_dialog(
            ft.SnackBar(
                content=ft.Text("Book was successfully added to your library."),
                behavior=ft.SnackBarBehavior.FLOATING,
            )
        )