from typing import Callable, Optional

import flet as ft

from ...callbacks import CallbackContext, CallbackMixin
from ...model import BookEntry, BookFilter, Genre
from ...search.engine import BookSearchEngine
from ...storage import (JsonIdNumeralStorage, LibroPaths, LibroStorage,
                        OnObjectsChangedCtx)


class OnSearchChangedCtx(CallbackContext):
    id = "on_search_changed"

    def __init__(self, filters: BookFilter):
        super().__init__()
        self.filters = filters


class OnBookChangedCtx(CallbackContext):
    id = "on_book_changed"

    def __init__(self, book: BookEntry, book_id: int):
        super().__init__()

        self.book = book
        self.book_id = book_id

    def get_book(self) -> BookEntry:
        return self.book

    def get_book_id(self) -> int:
        return self.book_id


class OnBookLendCtx(CallbackContext):
    id = "on_book_lend"

    def __init__(self, book: BookEntry, book_id: int):
        super().__init__()

        self.book = book
        self.book_id = book_id


class OnLendBookRequestedCtx(CallbackContext):
    id = "on_lend_book_requested"

    def __init__(self, book: BookEntry, book_id: int):
        super().__init__()

        self.book = book
        self.book_id = book_id


class OnBookRemoveCtx(CallbackContext):
    id = "on_book_remove"

    def __init__(self, book_id: int):
        super().__init__()
        self.book_id = book_id


class BookRow(ft.Dismissible, CallbackMixin):
    COVER_WIDTH = 80
    COVER_HEIGHT = 120

    def __init__(self, book: BookEntry, book_id: int):
        self.__init_callbacks__([
            OnBookChangedCtx.id,
            OnBookRemoveCtx.id,
            OnBookLendCtx.id
        ])

        self.book = book
        self.book_id = book_id

        self.title = book.title
        self.author = book.author.full_name()
        self.year = book.publish_year
        self.total_pages = book.pages
        self.current_page = book.current_page or 0

        cover_src = LibroPaths.assets() / "placeholder-cover.png"
        if book.cover:
            cover_src = LibroPaths.covers() / book.cover

        cover = ft.Container(
            width=self.COVER_WIDTH,
            height=self.COVER_HEIGHT,
            border_radius=8,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            bgcolor=ft.Colors.BLUE_GREY_700,
            content=ft.Image(
                src=str(cover_src)
            )
        )

        self.page_text = ft.Text(self.get_counter_text())

        self.page_counter_inputs = ft.Row(
            [
                ft.TextButton(
                    content="-5",
                    on_click=self._decrement_page_5,
                ),
                ft.TextButton(
                    content="-1",
                    on_click=self._decrement_page,
                ),
                self.page_text,
                ft.TextButton(
                    content="+1",
                    on_click=self._increment_page,
                ),
                ft.TextButton(
                    content="+5",
                    on_click=self._increment_page_5,
                ),
            ]
        )

        self.lend_button = ft.IconButton(
            icon=ft.Icons.PERSON_ADD,
            tooltip="Lend Book",
            on_click=self._lend_book,
        )

        self.progress_text = ft.Text(
            self.get_progress_text(),
            size=12,
            color=ft.Colors.OUTLINE,
        )
        self.progress_bar = ft.ProgressBar(
            value=self.get_progress(),
            height=8,
            border_radius=4,
            expand=True
        )

        super().__init__(
            content=ft.Row(
                [
                    ft.Container(
                        expand=True,
                        padding=10,
                        content=ft.Column(
                            spacing=8,
                            controls=[
                                ft.Row(
                                    vertical_alignment=ft.CrossAxisAlignment.START,
                                    controls=[
                                        cover,
                                        ft.Column(
                                            expand=True,
                                            spacing=4,
                                            controls=[
                                                ft.Text(
                                                    self.title,
                                                    size=18,
                                                    weight=ft.FontWeight.BOLD,
                                                    max_lines=2,
                                                    overflow=ft.TextOverflow.ELLIPSIS,
                                                ),
                                                ft.Text(
                                                    self.author,
                                                    size=14,
                                                ),
                                                ft.Text(
                                                    str(self.year),
                                                    size=13,
                                                    color=ft.Colors.OUTLINE,
                                                ),
                                            ],
                                        ),
                                        ft.Column(
                                            horizontal_alignment=ft.CrossAxisAlignment.END,
                                            controls=[
                                                self.page_counter_inputs,
                                                self.lend_button
                                            ],
                                        ),
                                    ],
                                ),
                                ft.Row([
                                    self.progress_text,
                                    self.progress_bar,
                                ], expand=True),
                            ],
                        ),
                    )
                ],
                expand=True
            ),
            dismiss_direction=ft.DismissDirection.END_TO_START,
            background=ft.Container(
                bgcolor=ft.Colors.RED,
                alignment=ft.Alignment.CENTER_RIGHT,
                padding=20,
                content=ft.Icon(
                    ft.Icons.DELETE,
                    color=ft.Colors.WHITE,
                ),
            ),
            on_dismiss=self._on_dismiss
        )

    def get_progress(self):
        return self.current_page / self.total_pages

    def get_counter_text(self):
        return f"{self.current_page} of {self.total_pages}"

    def register_on_book_changed(self, fn: Callable[[OnBookChangedCtx], None]):
        self.register_callback(OnBookChangedCtx.id, fn)

    def register_on_book_remove(self, fn: Callable[[OnBookRemoveCtx], None]):
        self.register_callback(OnBookRemoveCtx.id, fn)

    def register_on_book_lend(self, fn: Callable[[OnBookLendCtx], None]):
        self.register_callback(OnBookLendCtx.id, fn)

    def _lend_book(self, e):
        self._run_callbacks(
            OnBookLendCtx(
                self.book,
                self.book_id
            )
        )

    def _on_dismiss(self, e):
        self._run_callbacks(OnBookRemoveCtx(self.book_id))

    def _increment_page(self, e):
        if (self.current_page + 1) <= self.total_pages:
            self.current_page += 1
            self.book.current_page = self.current_page
            self._refresh_progress()

    def _increment_page_5(self, e):
        if (self.current_page + 5) <= self.total_pages:
            self.current_page += 5
            self.book.current_page = self.current_page
            self._refresh_progress()

    def _decrement_page(self, e):
        if (self.current_page - 1) >= 0:
            self.current_page -= 1
            self.book.current_page = self.current_page
            self._refresh_progress()

    def _decrement_page_5(self, e):
        if (self.current_page - 5) >= 0:
            self.current_page -= 5
            self.book.current_page = self.current_page
            self._refresh_progress()

    def _refresh_progress(self):
        self.page_text.value = self.get_counter_text()
        self.progress_text.value = self.get_progress_text()
        self.progress_bar.value = self.get_progress()
        self._run_callbacks(OnBookChangedCtx(self.book, self.book_id))

        self.update()

    def get_progress_text(self):
        return f"{self.get_progress() * 100:.01f}%"


class AdvancedSearchDrawer(ft.NavigationDrawer):
    def __init__(self, on_filters_change):
        self.on_filters_change = on_filters_change

        self.year_min_input = ft.TextField(
            label="Min Year",
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=self._on_filter_change,
        )

        self.year_max_input = ft.TextField(
            label="Max Year",
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=self._on_filter_change,
        )

        self.pages_min_input = ft.TextField(
            label="Min Pages",
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=self._on_filter_change,
        )

        self.pages_max_input = ft.TextField(
            label="Max Pages",
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=self._on_filter_change,
        )

        self.genre_dropdown = ft.Dropdown(
            label="Genre",
            value="Any",
            options=[
                ft.dropdown.Option("Any"),
                *[
                    ft.dropdown.Option(genre.value)
                    for genre in Genre
                ]
            ],
            on_select=self._on_filter_change,
        )

        super().__init__(
            controls=[
                ft.Container(height=16),
                ft.Text(
                    "Advanced Filters",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Divider(),

                self.year_min_input,
                self.year_max_input,

                self.pages_min_input,
                self.pages_max_input,

                self.genre_dropdown,

                ft.ElevatedButton(
                    "Reset Filters",
                    icon=ft.Icons.CLEAR,
                    on_click=self._on_reset,
                ),
            ]
        )

    def _parse_int(self, value):
        try:
            return int(value)
        except:
            return None

    @property
    def year_min(self):
        return self._parse_int(self.year_min_input.value)

    @property
    def year_max(self):
        return self._parse_int(self.year_max_input.value)

    @property
    def pages_min(self):
        return self._parse_int(self.pages_min_input.value)

    @property
    def pages_max(self):
        return self._parse_int(self.pages_max_input.value)

    def _on_filter_change(self, e):
        self.on_filters_change()

    def _on_reset(self, e):
        self.year_min_input.value = ""
        self.year_max_input.value = ""
        self.pages_min_input.value = ""
        self.pages_max_input.value = ""
        self.genre_dropdown.value = "Any"

        self.update()
        self.on_filters_change()


class LibraryTab(ft.Container, CallbackMixin):
    def __init__(self, **container_kwargs):
        self.__init_callbacks__([
            OnSearchChangedCtx.id,
            OnLendBookRequestedCtx.id
        ])

        self.search_no_result_view = ft.Container(
            expand=True,
            alignment=ft.Alignment.CENTER,
            content=ft.Column(
                [
                    ft.Icon(
                        ft.Icons.LOCAL_LIBRARY,
                        size=96,
                        color=ft.Colors.OUTLINE,
                    ),
                    ft.Text(
                        "No books match your search",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text(
                        "Try changing your filters.",
                        color=ft.Colors.OUTLINE,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                expand=True,
                spacing=10,
            ),
        )

        self.search_engine: BookSearchEngine | None = None

        self.book_list_view = ft.ListView(
            expand=True,
            spacing=10
        )

        self.library_content = ft.Container(
            expand=True,
            content=self.book_list_view
        )
        self.search_input = ft.TextField(label="Search Your Library", on_change=self.on_search_change, expand=True)

        self.toggle_button = ft.IconButton(
            icon=ft.Icons.TUNE,
            tooltip="Advanced Filters",
            on_click=self._on_toggle,
        )

        self.advanced_search = AdvancedSearchDrawer(on_filters_change=self.on_search_change)

        self.main_book_view = ft.Column(
            [
                ft.Row([self.search_input, self.toggle_button]),
                self.library_content,
            ],
            alignment=ft.MainAxisAlignment.START,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        self.main_column = ft.Column(
            [
                ft.Row(
                    [
                        self.search_input,
                        self.toggle_button,
                    ]
                ),
                self.library_content,
            ],
            expand=True,
        )

        LibroStorage.get(JsonIdNumeralStorage[BookEntry], BookEntry).register_change_callback(self.on_books_changed)

        super().__init__(content=self.main_column, **container_kwargs)

    def register_search_engine(self, search_engine):
        self.search_engine = search_engine

    def register_lend_callback(self, fn: Callable[[OnLendBookRequestedCtx], None]):
        self.register_callback(OnLendBookRequestedCtx.id, fn)

    def on_books_changed(self, ctx: OnObjectsChangedCtx):
        self.update_books(LibroStorage.get(JsonIdNumeralStorage[BookEntry], BookEntry).objects)

    def on_book_lend(self, ctx: OnBookLendCtx):
        self._run_callbacks(
            OnLendBookRequestedCtx(
                ctx.book,
                ctx.book_id
            )
        )

    def _on_toggle(self, e):
        page = self.page

        # if page:
        #    page.show_drawer(self.advanced_search)

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
        matched_books = self.search_engine.search(filters)

        self.update_books(matched_books)

    def on_book_change(self, ctx: OnBookChangedCtx):
        LibroStorage.get(JsonIdNumeralStorage[BookEntry], BookEntry).update_by_id(ctx.book_id, ctx.book)

    def on_book_remove(self, ctx: OnBookRemoveCtx):
        LibroStorage.get(JsonIdNumeralStorage[BookEntry], BookEntry).remove_by_id(ctx.book_id)

    def update_books(self, books: dict[int, BookEntry]):
        if not books:
            self.library_content.content = self.search_no_result_view
            return

        self.book_list_view.controls = []

        for id, book in books.items():
            book_row = BookRow(book, book_id=id)
            book_row.register_on_book_changed(self.on_book_change)
            book_row.register_on_book_remove(self.on_book_remove)
            book_row.register_on_book_lend(self.on_book_lend)
            self.book_list_view.controls.append(book_row)

        self.library_content.content = self.book_list_view
