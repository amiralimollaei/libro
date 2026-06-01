from typing import Callable, Optional

import flet as ft

from ..components import BookTile, AdvancedSearchFiltersRow
from ...callbacks import CallbackMixin, CallbackContext
from ...storage.json import JsonDirectoryStorage, OnObjectsChangedCtx
from ...model.book import Book, BookFilter


class OnSearchChangedCtx(CallbackContext):
    id = "on_search_changed"

    def __init__(self, filters: BookFilter):
        super().__init__()
        self.filters = filters


class LibraryTab(ft.Container, CallbackMixin):
    def __init__(self, **container_kwargs):
        self.__init_callbacks__([
            OnSearchChangedCtx.id
        ])

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

    def register_search_engine(self, search_engine):
        self.search_engine = search_engine

    def register_book_storage(self, storage: JsonDirectoryStorage[Book]):
        self.books_storage = storage
        self.books_storage.register_change_callback(self.on_books_changed)

    def on_books_changed(self, ctx: OnObjectsChangedCtx[Book]):
        self.update_books(ctx.objects)

    def _on_toggle(self, e: ft.Event):
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

    def register_on_search_change_fn(self, on_search_change_fn: Callable[[OnSearchChangedCtx], None]):
        self.register_callback(OnSearchChangedCtx.id, fn=on_search_change_fn)

    def on_search_change(self, e: Optional[ft.Event] = None):
        filters = self.get_book_filter()
        self._run_callbacks(OnSearchChangedCtx(filters))

        match_ids = self.search_engine.search(filters)
        if match_ids:
            matched_books = []
            for book in self.books_storage.objects:
                if book.id in match_ids:
                    matched_books.append(book)
        else:
            matched_books = self.books_storage.objects

        if match_ids:
            self.search_input.error = None
        else:
            self.search_input.error = "Not Found"

        self.update_books(matched_books)

    def update_books(self, books: list[Book]):
        self.books = books

        self.book_list_view.controls = []
        for book in self.books:
            self.book_list_view.controls.append(
                BookTile(book)
            )
