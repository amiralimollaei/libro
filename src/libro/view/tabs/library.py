from typing import Callable, Optional

import flet as ft

from ..components import BookTile, AdvancedSearchFiltersRow
from ...storage.json import JsonDirectoryStorage, OnObjectsChangedCtx
from ...model.book import Book, BookFilter


class LibraryTab(ft.Container):
    def __init__(self, **container_kwargs):
        self.on_search_change_fn: Optional[Callable] = None

        self.book_list_view = ft.ListView(expand=True, spacing=10)
        self.search_input = ft.TextField(label="Search Your Library", on_change=self.on_search_change, expand=True)

        self.is_advanced_search = False
        self.toggle_button = ft.IconButton(
            icon=ft.Icons.TUNE,
            tooltip="Advanced Filters",
            on_click=self._on_toggle
        )

        self.advanced_search = AdvancedSearchFiltersRow(on_filters_change=self.on_search_change)

        self.main_column = ft.Column(
            [
                ft.Row([self.search_input, self.toggle_button]),
                self.advanced_search,
                self.book_list_view,
            ],
            alignment=ft.MainAxisAlignment.START,
            expand=True
        )

        super().__init__(content=self.main_column, **container_kwargs)

    def register_book_storage(self, storage: JsonDirectoryStorage[Book]):
        self.books_storage = storage

        self.books_storage.register_change_callback(self.on_books_changed)

    def on_books_changed(self, ctx: OnObjectsChangedCtx[Book]):
        self.update_books(ctx.objects)

    def _on_toggle(self, e):
        self.is_advanced_search = not self.is_advanced_search
        self.advanced_search.visible = self.is_advanced_search
        self.toggle_button.icon = ft.Icons.UNFOLD_LESS if self.is_advanced_search else ft.Icons.TUNE
        self.update()

    def get_book_filter(self) -> BookFilter:
        return BookFilter(
            query=self.search_input.value,
            year_min=self.advanced_search.year_min,
            year_max=self.advanced_search.year_max,
            pages_min=self.advanced_search.pages_min,
            pages_max=self.advanced_search.pages_max,
            genre=self.advanced_search.genre_dropdown.value,
            # TODO: add the missing filters to the GUI
            include_title=True,
            include_author=True,
            include_summary=True
        )

    def register_on_search_change_fn(self, on_search_change_fn: Callable):
        self.on_search_change_fn = on_search_change_fn

    def on_search_change(self, e=None):
        if self.on_search_change_fn:
            self.on_search_change_fn()

            self.update()

    def update_books(self, books: list[Book]):
        self.books = books

        self.book_list_view.controls = []
        for book in self.books:
            self.book_list_view.controls.append(
                BookTile(book)
            )
