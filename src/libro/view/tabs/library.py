from typing import Callable, Optional

import flet as ft


from ..components import BookRow, OnBookChangedCtx, AdvancedSearchFiltersColumn, OnBookRemoveCtx
from ...callbacks import CallbackMixin, CallbackContext
from ...search.engine import BookSearchEngine
from ...storage.json import JsonIdNumeralStorage, OnObjectsChangedCtx
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
        
        self.books_storage: JsonIdNumeralStorage | None = None
        self.search_engine: BookSearchEngine | None = None

        self.book_list_view = ft.ListView(expand=True, spacing=10)
        self.search_input = ft.TextField(label="Search Your Library", on_change=self.on_search_change, expand=True)

        self.is_advanced_search = False
        self.toggle_button = ft.IconButton(
            icon=ft.Icons.TUNE,
            tooltip="Advanced Filters",
            on_click=self._on_toggle
        )

        self.advanced_search = AdvancedSearchFiltersColumn(on_filters_change=self.on_search_change)

        self.advanced_search_container = ft.Container(
            content=self.advanced_search,
            width=0,
            animate=ft.Animation(250, ft.AnimationCurve.EASE_IN_OUT),
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )

        self.main_column = ft.Row(
            [
                ft.Column(
                    [
                        ft.Row([self.search_input, self.toggle_button]),
                        self.book_list_view,
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    scroll=ft.ScrollMode.AUTO,
                    expand=True,
                ),
                self.advanced_search_container
            ],
            vertical_alignment=ft.CrossAxisAlignment.START
        )

        super().__init__(content=self.main_column, **container_kwargs)

    def register_search_engine(self, search_engine):
        self.search_engine = search_engine

    def register_book_storage(self, storage: JsonIdNumeralStorage[Book]):
        self.books_storage = storage
        self.books_storage.register_change_callback(self.on_books_changed)

    def on_books_changed(self, ctx: OnObjectsChangedCtx):
        assert self.books_storage
        self.update_books(self.books_storage.objects)

    def _on_toggle(self, e):
        self.is_advanced_search = not self.is_advanced_search

        self.advanced_search_container.width = (
            320 if self.is_advanced_search else 0
        )

        self.toggle_button.icon = (
            ft.Icons.UNFOLD_LESS
            if self.is_advanced_search
            else ft.Icons.TUNE
        )

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
        
        assert self.search_engine
        assert self.books_storage
        matched_books = self.search_engine.search(filters)
        
        if matched_books:
            self.search_input.error = None
        else:
            self.search_input.error = "Not Found"

        self.update_books(matched_books)

    def on_book_change(self, ctx: OnBookChangedCtx):
        if self.books_storage:
            self.books_storage.update_by_id(ctx.book_id, ctx.book)

    def on_book_remove(self, ctx: OnBookRemoveCtx):
        if self.books_storage:
            self.books_storage.remove_by_id(ctx.book_id)
        
    def update_books(self, books: dict[int, Book]):
        self.book_list_view.controls = []
        for id, book in books.items():
            book_row = BookRow(book, book_id=id)
            book_row.register_on_book_changed(self.on_book_change)
            book_row.register_on_book_remove(self.on_book_remove)
            self.book_list_view.controls.append(book_row)
