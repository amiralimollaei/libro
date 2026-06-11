import os
import time
from datetime import datetime

import flet as ft

from ..callbacks.statistics import rebuild_statistics_cache
from ..model import (BookEntry, BookReturnedEvent, LendingEntry,
                     StatisticalEvent, Statistics)
from ..storage import (JsonFileStorage, JsonIdNumeralStorage, LibroStorage,
                       OnObjectsChangedCtx)
from ..view.tabs.lending import (LendingTab, OnLendingEditDueCtx,
                                 OnLendingRemoveCtx, OnLendingReturnCtx)
from .base import AbstractController


class LendingController(AbstractController):
    """Controller for the Lending tab.

    Handles book return, due date editing, lending entry removal,
    and auto-refresh on storage changes.
    """

    def __init__(self, page: ft.Page, view: LendingTab):
        super().__init__(page)
        self.view = view

    # ---- Storage helpers ----

    @staticmethod
    def _lending_storage() -> JsonIdNumeralStorage[LendingEntry]:
        return LibroStorage.get(JsonIdNumeralStorage[LendingEntry], LendingEntry)

    @staticmethod
    def _book_storage() -> JsonIdNumeralStorage[BookEntry]:
        return LibroStorage.get(JsonIdNumeralStorage[BookEntry], BookEntry)

    @staticmethod
    def _events_storage() -> JsonIdNumeralStorage[StatisticalEvent]:
        return LibroStorage.get(JsonIdNumeralStorage[StatisticalEvent], StatisticalEvent)

    # ---- Callback registration ----

    def register_callbacks(self) -> None:
        self.view.register_on_lending_return(self.on_lending_return)
        self.view.register_on_lending_edit_due(self.on_lending_edit_due)
        self.view.register_on_lending_remove(self.on_lending_remove)

        # Register storage change listener to auto-refresh view
        self._lending_storage().register_change_callback(self.on_lending_changed)

    # ---- Business logic ----

    def on_lending_return(self, ctx: OnLendingReturnCtx):
        """
        Mark a lent book as returned and emit BookReturnedEvent.
        """

        lending_storage = self._lending_storage()
        entry = lending_storage.get(ctx.lending_id)
        if entry is None:
            return

        current_time = time.time()
        overdue_time = None
        if current_time > entry.due_date:
            overdue_time = current_time - entry.due_date

        entry.returned_time = current_time
        lending_storage.update_by_id(ctx.lending_id, entry)
        lending_storage.save()

        event = StatisticalEvent(
            book_id=ctx.book_id,
            timestamp=current_time,
            book_returned=BookReturnedEvent(
                lend_id=ctx.lending_id,
                overdue_time=overdue_time,
            ),
        )
        self._events_storage().add(event)
        self._events_storage().save()

    def on_lending_edit_due(self, ctx: OnLendingEditDueCtx):
        """
        Show a dialog to edit the due date/time of a lending entry.
        """

        # Use extracted dialog component
        from ..view.dalogs.editdatetime import EditDateTimeDialog

        current_due = datetime.fromtimestamp(ctx.lending_entry.due_date)

        def on_submit(new_due: datetime) -> None:
            ctx.lending_entry.due_date = new_due.timestamp()
            self._lending_storage().update_by_id(ctx.lending_id, ctx.lending_entry)
            self._lending_storage().save()

        # Show the dialog; it handles its own overlay management
        dialog = EditDateTimeDialog(current_due=current_due, on_submit=on_submit)
        self.page.show_dialog(dialog)

    def on_lending_remove(self, ctx: OnLendingRemoveCtx):
        """
        Remove a lending entry and remove its corresponding statistical events.

        Scans and removes any StatisticalEvents referencing this lend_id,
        then deletes the lending entry and rebuilds the statistics cache.
        """

        def do_remove(e):
            self.page.pop_dialog()

            # Remove any events referencing this lend_id
            events_storage = self._events_storage()
            events_to_remove: list[int] = []
            for ev_id, ev in events_storage.objects.items():
                if ev.book_lent is not None and ev.book_lent.lend_id == ctx.lending_id:
                    events_to_remove.append(ev_id)
                elif ev.book_returned is not None and ev.book_returned.lend_id == ctx.lending_id:
                    events_to_remove.append(ev_id)

            for ev_id in events_to_remove:
                # Direct deletion to avoid cancel-callback interference
                del events_storage.objects[ev_id]
                os.remove(events_storage.directory / f"{ev_id}.json")

            events_storage._notify_changed()
            events_storage.save()

            # Remove the lending entry
            self._lending_storage().remove_by_id(ctx.lending_id)
            self._lending_storage().save()

            # Rebuild statistics cache so it no longer reflects this lending
            stats_storage = LibroStorage.get(JsonFileStorage[Statistics], Statistics)
            rebuilt = rebuild_statistics_cache()
            stats_storage.update(rebuilt)
            stats_storage.save()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Remove Lending Entry"),
            content=ft.Text(
                "Are you sure you want to remove this lending entry? "
                "This will also remove any associated statistics and cannot be undone."
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.page.pop_dialog()),
                ft.FilledButton(
                    "Remove",
                    icon=ft.Icons.DELETE,
                    on_click=do_remove,
                    style=ft.ButtonStyle(color=ft.Colors.RED),
                ),
            ],
        )

        self.page.show_dialog(dialog)

    def on_lending_changed(self, ctx: OnObjectsChangedCtx):
        """
        reload lending entries when the lending storage notifies us about a change.
        """

        self.view.update_lending_entries(self._lending_storage().objects)
        self.view.update()
