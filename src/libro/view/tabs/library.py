from typing import Callable, Optional

import flet as ft

from ...asyncutils import DelayedTaskScheduler
from ...callbacks import CallbackContext, CallbackMixin
from ...callbacks.statistics import compute_book_statistics
from ...model import BookEntry, BookFilter
from ...search.engine import BookSearchEngine
from ...storage.paths import LibroPaths
from ..components import BookCover
from ..dalogs.advancedsearch import AdvancedSearchDialog
from ..dalogs.bookdetails import BookDetailsDialog, OnDeleteBookCtx
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


class OnPageReadCtx(CallbackContext):
    """Fired by BookRow when the user changes the page counter."""
    id = "on_page_read"

    def __init__(self, book_id: int, old_page: int, new_page: int, total_pages: int):
        super().__init__()
        self.book_id = book_id
        self.old_page = old_page
        self.new_page = new_page
        self.total_pages = total_pages


class BookRow(ft.Card, CallbackMixin):
    """A Card-based book entry with ripple touch feedback and elevation — Android-native feel."""

    COVER_WIDTH = 80
    COVER_HEIGHT = 120

    def __init__(self, book: BookEntry, book_id: int):
        self.__init_callbacks__([
            OnBookChangedCtx.id,
            OnBookRemoveCtx.id,
            OnBookLendCtx.id,
            OnPageReadCtx.id,
        ])

        self.book = book
        self.book_id = book_id

        self.title = book.title
        self.author = book.author.full_name()
        self.year = book.publish_year
        self.total_pages = book.pages
        self.current_page = book.current_page or 0

        self.cover_src = str(LibroPaths.assets() / "placeholder-cover.png")
        if book.cover:
            self.cover_src = str(LibroPaths.covers() / book.cover)

        self.cover = BookCover(
            cover_src=self.cover_src,
            overlay_text=self.get_counter_text(),
            width=self.COVER_WIDTH,
            height=self.COVER_HEIGHT,
        )
        cover = self.cover

        self.page_counter_text = ft.Text(
            f"{self.current_page}",
            size=16,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
        )

        self.page_slider = ft.Slider(
            min=0,
            max=float(self.total_pages),
            value=float(self.current_page),
            divisions=self.total_pages,
            label="{value}",
            on_change_end=self._on_slider_changed,
            expand=True
        )

        self.page_counter_inputs = ft.Column(
            [
                ft.Row(
                    [
                        ft.IconButton(
                            icon=ft.Icons.REMOVE,
                            icon_size=18,
                            tooltip="Previous Page",
                            on_click=self._decrement_page,
                        ),
                        self.page_counter_text,
                        ft.IconButton(
                            icon=ft.Icons.ADD,
                            icon_size=18,
                            tooltip="Next Page",
                            on_click=self._increment_page,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=2,
                ),
            ],
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        self.lend_button = ft.IconButton(
            icon=ft.Icons.PERSON_ADD,
            tooltip="Lend Book",
            on_click=self._lend_book,
        )

        # Progress bar removed; slider will serve as progress indicator.
        self.progress_text = ft.Text(
            self.get_progress_text(),
            size=12,
            color=ft.Colors.OUTLINE,
        )

        super().__init__(
            expand=True,
            elevation=1,
            margin=ft.Margin(0, 2, 0, 2),
            content=ft.Container(
                padding=10,
                ink=True,
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
                            self.page_slider,
                        ], expand=True),
                    ],
                ),
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

    def register_on_page_read(self, fn: Callable[[OnPageReadCtx], None]):
        self.register_callback(OnPageReadCtx.id, fn)

    async def _on_book_click(self, e):
        """Open the book details dialog when the book row is clicked."""

        # wait for all statistical events to finish before showind the book details dialog
        await DelayedTaskScheduler.flush_all()

        dialog = BookDetailsDialog(
            self.book,
            self.book_id,
            statistics=compute_book_statistics(self.book, self.book_id)
        )
        dialog.register_on_delete_book(self._on_book_delete_confirmed)

        self.page.show_dialog(dialog)

    def _on_book_delete_confirmed(self, ctx):
        """Handle book deletion from the dialog."""
        if isinstance(ctx, OnDeleteBookCtx):
            self._run_callbacks(OnBookRemoveCtx(ctx.book_id))

    def _lend_book(self, e):
        self._run_callbacks(
            OnBookLendCtx(
                self.book,
                self.book_id
            )
        )

    async def _increment_page(self, e):
        if (self.current_page + 1) <= self.total_pages:
            old_page = self.current_page
            self.current_page += 1
            self.book.current_page = self.current_page
            self._run_callbacks(OnPageReadCtx(self.book_id, old_page, self.current_page, self.total_pages))
            self._refresh_progress()

    async def _decrement_page(self, e):
        if (self.current_page - 1) >= 0:
            old_page = self.current_page
            self.current_page -= 1
            self.book.current_page = self.current_page
            self._run_callbacks(OnPageReadCtx(self.book_id, old_page, self.current_page, self.total_pages))
            self._refresh_progress()

    def _on_slider_changed(self, e):
        """Called when the slider value is dragged."""
        new_page = int(round(e.control.value))
        if new_page != self.current_page:
            old_page = self.current_page
            self.current_page = new_page
            self.book.current_page = self.current_page
            self._run_callbacks(OnPageReadCtx(self.book_id, old_page, self.current_page, self.total_pages))
            self._refresh_progress()

    def _refresh_progress(self):
        self.cover.set_overlay_text(self.get_counter_text())
        self.progress_text.value = self.get_progress_text()
        self.page_counter_text.value = str(self.current_page)
        self.page_slider.value = float(self.current_page)
        self._run_callbacks(OnBookChangedCtx(self.book, self.book_id))
        self.update()

    def get_progress_text(self):
        return f"{self.get_progress() * 100:.01f}%"


class LibraryTab(AbstractTab):
    def __init__(self, **container_kwargs):
        self.__init_callbacks__([
            OnSearchChangedCtx.id,
            OnLendBookRequestedCtx.id,
            OnBookChangedCtx.id,
            OnBookRemoveCtx.id,
            OnBookLendCtx.id,
            OnPageReadCtx.id,
        ])

        self.search_engine: BookSearchEngine | None = None

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

        super().__init__(content=self.main_column, **container_kwargs)

    # ---- implement AbstractTab ----
    
    def register_page(self, page: ft.Page):
        return

    def get_title(self) -> str:
        return "Library"
    
    async def on_focused(self) -> None:
        pass

    # ---- Registration methods for the Controller ----

    def register_search_engine(self, search_engine):
        self.search_engine = search_engine

    def register_lend_callback(self, fn: Callable[[OnLendBookRequestedCtx], None]):
        self.register_callback(OnLendBookRequestedCtx.id, fn)

    def register_on_search_change_fn(self, on_search_change_fn: Callable[[OnSearchChangedCtx], None]):
        self.register_callback(OnSearchChangedCtx.id, fn=on_search_change_fn)

    def register_on_book_changed(self, fn: Callable[[OnBookChangedCtx], None]):
        self.register_callback(OnBookChangedCtx.id, fn)

    def register_on_book_remove(self, fn: Callable[[OnBookRemoveCtx], None]):
        self.register_callback(OnBookRemoveCtx.id, fn)

    def register_on_book_lend(self, fn: Callable[[OnBookLendCtx], None]):
        self.register_callback(OnBookLendCtx.id, fn)

    def register_on_page_read(self, fn: Callable[[OnPageReadCtx], None]):
        self.register_callback(OnPageReadCtx.id, fn)

    # ---- View methods ----

    def on_search_change(self, e: Optional[ft.Event] = None):
        """Called when the search input or advanced filters change.

        Fires OnSearchChangedCtx which the controller handles.
        """
        filters = self.get_book_filter()
        self._run_callbacks(OnSearchChangedCtx(filters))

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
            include_title=self.advanced_search_dialog.include_title,
            include_author=self.advanced_search_dialog.include_author,
            include_summary=self.advanced_search_dialog.include_summary,
        )

    def update_books(self, books: dict[int, BookEntry]):
        if not books:
            self.library_content.content = self.search_no_result_view
            return

        self.book_list_view.controls = []

        for id, book in books.items():
            book_row = BookRow(book, book_id=id)
            book_row.register_on_book_changed(self._forward_book_changed)
            book_row.register_on_book_remove(self._forward_book_remove)
            book_row.register_on_book_lend(self._forward_book_lend)
            book_row.register_on_page_read(self._forward_page_read)
            self.book_list_view.controls.append(book_row)

        self.library_content.content = self.book_list_view

    # ---- Forwarding methods: BookRow callbacks → LendingTab callbacks ----

    def _forward_book_changed(self, ctx: OnBookChangedCtx):
        self._run_callbacks(ctx)

    def _forward_book_remove(self, ctx: OnBookRemoveCtx):
        self._run_callbacks(ctx)

    def _forward_book_lend(self, ctx: OnBookLendCtx):
        self._run_callbacks(ctx)

    def _forward_page_read(self, ctx: OnPageReadCtx):
        self._run_callbacks(ctx)
