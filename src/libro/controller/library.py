import time
from typing import Optional

import flet as ft

from ..asyncutils import DelayedTaskScheduler
from ..model import (BookEntry, BookFinishedEvent, BookLentEvent, BookReadEvent,
                     LendingEntry, Person, StatisticalEvent)
from ..search.engine import BookSearchEngine
from ..storage import (JsonFileStorage, JsonIdNumeralStorage, LibroStorage,
                       OnObjectsChangedCtx)
from ..view.dalogs.lending import LendingDialog
from ..view.tabs.library import (LibraryTab, OnBookChangedCtx, OnBookLendCtx,
                                 OnBookRemoveCtx, OnLendBookRequestedCtx,
                                 OnPageReadCtx, OnSearchChangedCtx)
from .base import AbstractController


class LibraryController(AbstractController):
    """Controller for the Library tab.

    Handles book CRUD, page reading events, book lending flow, and search.
    """

    def __init__(self, page: ft.Page, view: LibraryTab, search_engine: BookSearchEngine):
        super().__init__(page)
        self.view = view
        self.search_engine = search_engine
        self._page_event_scheduler = DelayedTaskScheduler()
        self._book_baseline_page: dict[int, int] = {}

    # ---- Storage helpers ----

    @staticmethod
    def _book_storage() -> JsonIdNumeralStorage[BookEntry]:
        return LibroStorage.get(JsonIdNumeralStorage[BookEntry], BookEntry)

    @staticmethod
    def _events_storage() -> JsonIdNumeralStorage[StatisticalEvent]:
        return LibroStorage.get(JsonIdNumeralStorage[StatisticalEvent], StatisticalEvent)

    @staticmethod
    def _lending_storage() -> JsonIdNumeralStorage[LendingEntry]:
        return LibroStorage.get(JsonIdNumeralStorage[LendingEntry], LendingEntry)

    # ---- Callback registration ----

    def register_callbacks(self) -> None:
        # Register view's internal callbacks that the BookRow forwards
        self.view.register_on_book_changed(self.on_book_change)
        self.view.register_on_book_remove(self.on_book_remove)
        self.view.register_on_book_lend(self.on_book_lend)
        self.view.register_on_page_read(self.on_page_read)
        self.view.register_on_search_change_fn(self.on_search_change)

        # Register the lend-book callback (library → lending flow)
        self.view.register_lend_callback(self.on_lend_book_requested)

        # Register storage change listener to auto-refresh view
        self._book_storage().register_change_callback(self.on_books_changed)

    # ---- Business logic ----

    def on_book_change(self, ctx: OnBookChangedCtx):
        """Persist book updates to storage."""
        self._book_storage().update_by_id(ctx.book_id, ctx.book)

    def on_book_remove(self, ctx: OnBookRemoveCtx):
        """Remove a book from storage."""
        self._book_storage().remove_by_id(ctx.book_id)

    def on_book_lend(self, ctx: OnBookLendCtx):
        """Forward a lend request to the handled callback."""
        self.view._run_callbacks(
            OnLendBookRequestedCtx(ctx.book, ctx.book_id)
        )

    def on_lend_book_requested(self, ctx: OnLendBookRequestedCtx):
        """Show lending dialog and create lending entry + BookLentEvent."""
        def on_lending_dialog_submit(dialog: LendingDialog):
            lend_id = self._lending_storage().add(LendingEntry(
                book_id=ctx.book_id,
                borrower=Person(name=dialog.borrower),
                lent_date=time.time(),
                due_date=dialog.due_at.timestamp()  # pyright: ignore[reportOptionalMemberAccess]
            ))
            self._lending_storage().save()

            # Emit BookLentEvent
            event = StatisticalEvent(
                book_id=ctx.book_id,
                timestamp=time.time(),
                book_lent=BookLentEvent(
                    lend_id=lend_id,
                    total_pages=ctx.book.pages,
                ),
            )
            self._events_storage().add(event)
            self._events_storage().save()

        self.page.show_dialog(
            LendingDialog(
                book_title=ctx.book.title,
                on_submit=on_lending_dialog_submit,
            )
        )

    def on_page_read(self, ctx: OnPageReadCtx):
        """Called by BookRow when the user changes the page counter.

        Debounces event emission so that rapid clicks produce a single
        BookReadEvent covering the net change from the first click.
        """
        if ctx.new_page == ctx.old_page:
            return

        # capture the first page value as the baseline for the delta
        if ctx.book_id not in self._book_baseline_page:
            self._book_baseline_page[ctx.book_id] = ctx.old_page

        book_id = ctx.book_id
        total_pages = ctx.total_pages
        baseline = self._book_baseline_page[book_id]

        async def _write_event():
            current_book = self._book_storage().get(book_id)
            if current_book is None:
                return
            pages_read = current_book.current_page or 0

            event = StatisticalEvent(
                book_id=book_id,
                timestamp=time.time(),
                book_read=BookReadEvent(
                    pages_read=pages_read,
                    previous_pages_read=baseline,
                ),
            )
            self._events_storage().add(event)
            self._events_storage().save()

            # reset baseline so the next burst of clicks starts fresh
            self._book_baseline_page.pop(book_id, None)

            # check if book is now finished
            if pages_read >= total_pages:
                self._emit_book_finished_event(book_id, total_pages)

        self._page_event_scheduler.debounce(
            10.0,
            _write_event,
            key=f"page_event_{book_id}",
        )

    def _emit_book_finished_event(self, book_id: int, total_pages: int):
        """Emit a BookFinishedEvent when a book is completed."""
        estimated_reading_rate = 30  # pages per day
        days_to_finish = total_pages / estimated_reading_rate

        event = StatisticalEvent(
            book_id=book_id,
            timestamp=time.time(),
            book_finished=BookFinishedEvent(
                total_pages=total_pages,
                days_to_finish=days_to_finish,
            ),
        )
        self._events_storage().add(event)
        self._events_storage().save()

    def on_search_change(self, ctx: OnSearchChangedCtx):
        """Run search and update the view with matched books."""
        matched_books = self.search_engine.search(ctx.filters)
        self.view.update_books(matched_books)

    def on_books_changed(self, ctx: OnObjectsChangedCtx):
        """Storage change listener — reload books into the view."""
        self.view.update_books(self._book_storage().objects)
        self.view.update()