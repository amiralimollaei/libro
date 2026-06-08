import time
from typing import Callable, Optional

import flet as ft

from ...asyncutils import DelayedTaskScheduler
from ...callbacks import CallbackContext, CallbackMixin
from ...model import (BookEntry, BookFilter, BookFinishedEvent, BookReadEvent,
                      StatisticalEvent)
from ...search.engine import BookSearchEngine
from ...storage import (JsonIdNumeralStorage, LibroPaths, LibroStorage,
                        OnObjectsChangedCtx)
from ..dalogs.advancedsearch import AdvancedSearchDialog
from ..dalogs.bookdetails import BookDetailsDialog
from .base import AbstractTab


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


class BookRow(ft.Container, CallbackMixin):
    COVER_WIDTH = 80
    COVER_HEIGHT = 120

    def __init__(self, book: BookEntry, book_id: int):
        self.__init_callbacks__([
            OnBookChangedCtx.id,
            OnBookRemoveCtx.id,
            OnBookLendCtx.id
        ])

        self.scheduler = DelayedTaskScheduler()

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

        self.page_text = ft.Text(
            self.get_counter_text(),
            color=ft.Colors.WHITE,
            weight=ft.FontWeight.BOLD,
        )

        cover = ft.Stack(
            width=self.COVER_WIDTH,
            height=self.COVER_HEIGHT,
            controls=[
                ft.Container(
                    width=self.COVER_WIDTH,
                    height=self.COVER_HEIGHT,
                    border_radius=8,
                    clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                    bgcolor=ft.Colors.BLUE_GREY_700,
                    content=ft.Image(
                        src=str(cover_src),
                        fit=ft.BoxFit.COVER,
                    ),
                ),
                ft.Container(
                    width=self.COVER_WIDTH,
                    height=self.COVER_HEIGHT,
                    bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.BLACK),
                ),
                ft.Container(
                    width=self.COVER_WIDTH,
                    height=self.COVER_HEIGHT,
                    alignment=ft.Alignment.CENTER,
                    content=self.page_text
                ),
            ],
        )

        self.page_counter_inputs = ft.Column(
            [
                ft.Row(
                    [
                        ft.ElevatedButton(
                            content="-5",
                            on_click=self._decrement_page_5,
                            style=ft.ButtonStyle(
                                padding=0,
                            ),
                            width=40,
                            height=30,
                        ),
                        ft.ElevatedButton(
                            content="-1",
                            on_click=self._decrement_page,
                            style=ft.ButtonStyle(
                                padding=0,
                            ),
                            width=40,
                            height=30,
                        ),
                    ],
                    spacing=5
                ),
                ft.Row(
                    [
                        ft.ElevatedButton(
                            content="+5",
                            on_click=self._increment_page_5,
                            style=ft.ButtonStyle(
                                padding=0,
                            ),
                            width=40,
                            height=30,
                        ),
                        ft.ElevatedButton(
                            content="+1",
                            on_click=self._increment_page,
                            style=ft.ButtonStyle(
                                padding=0,
                            ),
                            width=40,
                            height=30,
                        ),
                    ],
                    spacing=5
                )
            ],
            spacing=5
        )

        self.lend_button = ft.TextButton(
            content="Lend",
            tooltip="Lend Book",
            icon=ft.Icons.PERSON_ADD,
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
            expand=True,
            padding=10,
            on_click=self._on_book_click,
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
                                alignment=ft.MainAxisAlignment.END,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    self.lend_button,
                                    self.page_counter_inputs,
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

    def _on_book_click(self, e):
        """Open the book details dialog when the book row is clicked."""
        from ...callbacks.statistics import compute_book_statistics

        stats = compute_book_statistics(self.book, self.book_id)
        dialog = BookDetailsDialog(self.book, self.book_id, statistics=stats)
        dialog.register_on_delete_book(self._on_book_delete_confirmed)

        self.page.show_dialog(dialog)

    def _on_book_delete_confirmed(self, ctx):
        """Handle book deletion from the dialog."""
        from libro.view.dalogs.bookdetails import OnDeleteBookCtx
        if isinstance(ctx, OnDeleteBookCtx):
            # trigger the deletion through the library tab's on_book_remove handler
            # this will callback be registered when the book row is created in update_books
            self._run_callbacks(OnBookRemoveCtx(ctx.book_id))

    def _lend_book(self, e):
        self._run_callbacks(
            OnBookLendCtx(
                self.book,
                self.book_id
            )
        )

    def _emit_page_read_event(self, old_page: int, new_page: int):
        """Emit a BookReadEvent to the reading events storage.

        Stores absolute page values so that delta can be computed
        later as pages_read - previous_pages_read.
        """
        if new_page != old_page:
            event = StatisticalEvent(
                book_id=self.book_id,
                timestamp=time.time(),
                book_read=BookReadEvent(
                    pages_read=new_page,        # absolute current page
                    previous_pages_read=old_page  # absolute previous page
                )
            )
            events_storage = LibroStorage.get(JsonIdNumeralStorage[StatisticalEvent], StatisticalEvent)
            events_storage.add(event)
            events_storage.save()
            self._refresh_book_data()

            # check if book is now finished
            if new_page >= self.total_pages:
                self._emit_book_finished_event()

    def _refresh_book_data(self):
        """Persist the current book state to the book storage."""
        book_storage = LibroStorage.get(JsonIdNumeralStorage[BookEntry], BookEntry)
        book_storage.update_by_id(self.book_id, self.book)

    def _emit_book_finished_event(self):
        """Emit a BookFinishedEvent when book is completed."""
        # Calculate days_to_finish from total pages and estimated reading rate
        # Assuming average reading rate of 30 pages per day
        estimated_reading_rate = 30  # pages per day
        days_to_finish = self.total_pages / estimated_reading_rate

        event = StatisticalEvent(
            book_id=self.book_id,
            timestamp=time.time(),
            book_finished=BookFinishedEvent(
                total_pages=self.total_pages,
                days_to_finish=days_to_finish
            )
        )
        events_storage = LibroStorage.get(JsonIdNumeralStorage[StatisticalEvent], StatisticalEvent)
        events_storage.add(event)
        events_storage.save()

    async def _increment_page(self, e):
        if (self.current_page + 1) <= self.total_pages:
            old_page = self.current_page
            self.current_page += 1
            self.book.current_page = self.current_page
            self._emit_page_read_event(old_page, self.current_page)
            self._refresh_progress()

    async def _increment_page_5(self, e):
        if (self.current_page + 5) <= self.total_pages:
            old_page = self.current_page
            self.current_page += 5
            self.book.current_page = self.current_page
            self._emit_page_read_event(old_page, self.current_page)
            self._refresh_progress()

    async def _decrement_page(self, e):
        if (self.current_page - 1) >= 0:
            old_page = self.current_page
            self.current_page -= 1
            self.book.current_page = self.current_page
            self._emit_page_read_event(old_page, self.current_page)
            self._refresh_progress()

    async def _decrement_page_5(self, e):
        if (self.current_page - 5) >= 0:
            old_page = self.current_page
            self.current_page -= 5
            self.book.current_page = self.current_page
            self._emit_page_read_event(old_page, self.current_page)
            self._refresh_progress()

    def _refresh_progress(self):
        self.page_text.value = self.get_counter_text()
        self.progress_text.value = self.get_progress_text()
        self.progress_bar.value = self.get_progress()
        self._run_callbacks(OnBookChangedCtx(self.book, self.book_id))

        self.update()

    def get_progress_text(self):
        return f"{self.get_progress() * 100:.01f}%"


class LibraryTab(AbstractTab):
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
            on_click=self._on_advanced_search,
        )

        self.advanced_search_dialog = AdvancedSearchDialog(self.on_search_change)

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

    def register_page(self, page: ft.Page):
        return

    def register_search_engine(self, search_engine):
        self.search_engine = search_engine

    def register_lend_callback(self, fn: Callable[[OnLendBookRequestedCtx], None]):
        self.register_callback(OnLendBookRequestedCtx.id, fn)

    def on_books_changed(self, ctx: OnObjectsChangedCtx):
        self.update_books(LibroStorage.get(JsonIdNumeralStorage[BookEntry], BookEntry).objects)

        self.update()

    def on_book_lend(self, ctx: OnBookLendCtx):
        self._run_callbacks(
            OnLendBookRequestedCtx(
                ctx.book,
                ctx.book_id
            )
        )

    async def _on_advanced_search(self, e):
        page = self.page

        if page:
            page.show_dialog(self.advanced_search_dialog)

    def get_book_filter(self) -> BookFilter:
        return BookFilter(
            query=self.search_input.value,
            year_min=self.advanced_search_dialog.year_min,
            year_max=self.advanced_search_dialog.year_max,
            pages_min=self.advanced_search_dialog.pages_min,
            pages_max=self.advanced_search_dialog.pages_max,
            genre=self.advanced_search_dialog.genre_dropdown.value,
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
