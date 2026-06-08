import os
import time
from datetime import datetime

import flet as ft

from ...callbacks import CallbackContext, CallbackMixin
from ...callbacks.statistics import rebuild_statistics_cache
from ...model import (BookEntry, BookReturnedEvent, LendingEntry,
                      Statistics, StatisticalEvent)
from ...storage import (JsonFileStorage, JsonIdNumeralStorage, LibroPaths,
                        LibroStorage, OnObjectsChangedCtx)
from ..components import BookCover
from .base import AbstractTab


class OnLendingReturnCtx(CallbackContext):
    id = "on_lending_return"

    def __init__(self, lending_id: int, book_id: int, lending_entry: LendingEntry):
        super().__init__()
        self.lending_id = lending_id
        self.book_id = book_id
        self.lending_entry = lending_entry


class OnLendingEditDueCtx(CallbackContext):
    id = "on_lending_edit_due"

    def __init__(self, lending_id: int, lending_entry: LendingEntry):
        super().__init__()
        self.lending_id = lending_id
        self.lending_entry = lending_entry


class OnLendingRemoveCtx(CallbackContext):
    id = "on_lending_remove"

    def __init__(self, lending_id: int, book_id: int):
        super().__init__()
        self.lending_id = lending_id
        self.book_id = book_id


class LendingBookRow(ft.Row, CallbackMixin):
    COVER_WIDTH = 80
    COVER_HEIGHT = 120

    def __init__(
        self,
        book: BookEntry,
        book_id: int,
        lending_entry: LendingEntry,
        lending_id: int,
    ):
        self.__init_callbacks__([
            OnLendingReturnCtx.id,
            OnLendingEditDueCtx.id,
            OnLendingRemoveCtx.id,
        ])

        super().__init__()

        self.book = book
        self.book_id = book_id
        self.lending_entry = lending_entry
        self.lending_id = lending_id

        is_returned = lending_entry.is_returned
        is_overdue = (
            not is_returned
            and lending_entry.due_date < time.time()
        )

        cover_src = str(LibroPaths.assets() / "placeholder-cover.png")
        if book.cover:
            cover_src = str(LibroPaths.covers() / book.cover)

        cover = BookCover(
            cover_src=cover_src,
            width=self.COVER_WIDTH,
            height=self.COVER_HEIGHT,
        )

        due_date = datetime.fromtimestamp(
            lending_entry.due_date
        ).strftime("%Y-%m-%d %H:%M")

        lent_date = datetime.fromtimestamp(
            lending_entry.lent_date
        ).strftime("%Y-%m-%d")

        if is_returned and lending_entry.returned_time:
            returned_date = datetime.fromtimestamp(
                lending_entry.returned_time
            ).strftime("%Y-%m-%d")
            status_text = f"Returned on {returned_date}"
            status_color = ft.Colors.GREEN
            status_icon = ft.Icons.CHECK_CIRCLE
        elif is_overdue:
            status_text = "Overdue"
            status_color = ft.Colors.ERROR
            status_icon = ft.Icons.WARNING
        else:
            status_text = "Borrowed"
            status_color = ft.Colors.PRIMARY
            status_icon = ft.Icons.PERSON

        # action buttons for non-returned books
        action_controls = []
        if not is_returned:
            action_controls.append(
                ft.IconButton(
                    ft.Icons.CHECK_CIRCLE,
                    tooltip="Mark as Returned",
                    icon_color=ft.Colors.GREEN,
                    on_click=self._on_return_click,
                )
            )
            action_controls.append(
                ft.IconButton(
                    ft.Icons.EDIT_CALENDAR,
                    tooltip="Edit Due Date",
                    icon_color=ft.Colors.ORANGE,
                    on_click=self._on_edit_due_click,
                )
            )
            action_controls.append(
                ft.IconButton(
                    ft.Icons.DELETE,
                    tooltip="Remove from Lending",
                    icon_color=ft.Colors.RED,
                    on_click=self._on_remove_click,
                )
            )

        self.controls = [
            ft.Container(
                expand=True,
                padding=10,
                border_radius=8,
                bgcolor=(
                    ft.Colors.ERROR_CONTAINER
                    if is_overdue
                    else None
                ),
                content=ft.Column(
                    spacing=6,
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
                                            book.title,
                                            size=18,
                                            weight=ft.FontWeight.BOLD,
                                            max_lines=2,
                                            overflow=ft.TextOverflow.ELLIPSIS,
                                        ),
                                        ft.Text(
                                            book.author.full_name(),
                                            size=14,
                                        ),
                                        ft.Text(
                                            f"Borrowed by: {lending_entry.borrower.full_name()}",
                                            size=13,
                                        ),
                                        ft.Text(
                                            f"Lent: {lent_date}",
                                            size=12,
                                            color=ft.Colors.OUTLINE,
                                        ),
                                        ft.Text(
                                            f"Due: {due_date}",
                                            size=12,
                                            color=ft.Colors.OUTLINE,
                                        ),
                                    ],
                                ),
                                ft.Column(
                                    horizontal_alignment=ft.CrossAxisAlignment.END,
                                    controls=[
                                        ft.Icon(
                                            status_icon,
                                            color=status_color,
                                        ),
                                        ft.Text(
                                            status_text,
                                            color=status_color,
                                            weight=ft.FontWeight.BOLD,
                                            size=12,
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        ft.Row(
                            alignment=ft.MainAxisAlignment.END,
                            controls=action_controls,
                        ),
                    ],
                ),
            )
        ]

    def _on_return_click(self, e):
        self._run_callbacks(
            OnLendingReturnCtx(self.lending_id, self.book_id, self.lending_entry)
        )

    def _on_edit_due_click(self, e):
        self._run_callbacks(
            OnLendingEditDueCtx(self.lending_id, self.lending_entry)
        )

    def _on_remove_click(self, e):
        self._run_callbacks(
            OnLendingRemoveCtx(self.lending_id, self.book_id)
        )


class LendingTab(AbstractTab):
    def __init__(self, **container_kwargs):
        self.lending_list_view = ft.ListView(
            expand=True,
            spacing=10,
        )

        self.main_column = ft.Column(
            [
                self.lending_list_view,
            ],
            expand=True,
            spacing=10,
        )

        LibroStorage.get(
            JsonIdNumeralStorage[LendingEntry],
            LendingEntry
        ).register_change_callback(self.on_lending_changed)

        super().__init__(
            content=self.main_column,
            **container_kwargs,
        )

    def register_page(self, page: ft.Page):
        return

    @staticmethod
    def _lending_storage() -> JsonIdNumeralStorage[LendingEntry]:
        return LibroStorage.get(JsonIdNumeralStorage[LendingEntry], LendingEntry)

    @staticmethod
    def _book_storage() -> JsonIdNumeralStorage[BookEntry]:
        return LibroStorage.get(JsonIdNumeralStorage[BookEntry], BookEntry)

    @staticmethod
    def _events_storage() -> JsonIdNumeralStorage[StatisticalEvent]:
        return LibroStorage.get(JsonIdNumeralStorage[StatisticalEvent], StatisticalEvent)

    def on_lending_changed(self, ctx: OnObjectsChangedCtx):
        self.update_lending_entries(self._lending_storage().objects)
        self.update()

    def on_lending_return(self, ctx: OnLendingReturnCtx):
        """Mark a lent book as returned and emit BookReturnedEvent."""
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
        """Show a dialog to edit the due date/time of a lending entry."""

        current_due = datetime.fromtimestamp(ctx.lending_entry.due_date)

        date_picker = ft.DatePicker(
            first_date=datetime.today(),
            on_change=None,
            value=current_due,
        )
        time_picker = ft.TimePicker(
            on_change=None,
            value=current_due.time(),
        )

        selected_date = [current_due.date()]
        selected_time = [current_due.time()]

        date_field = ft.TextField(
            label="Due Date",
            read_only=True,
            suffix_icon=ft.Icons.CALENDAR_MONTH,
            value=selected_date[0].isoformat(),
            on_click=lambda e: self.page.show_dialog(date_picker),
        )
        time_field = ft.TextField(
            label="Due Time",
            read_only=True,
            suffix_icon=ft.Icons.ACCESS_TIME,
            value=selected_time[0].strftime("%H:%M"),
            on_click=lambda e: self.page.show_dialog(time_picker),
        )

        def on_date_selected(e):
            d = date_picker.value
            if d:
                selected_date[0] = d.date()
                date_field.value = selected_date[0].isoformat()
                date_field.update()

        def on_time_selected(e):
            t = time_picker.value
            if t:
                selected_time[0] = datetime(
                    year=1, month=1, day=1,
                    hour=t.hour, minute=t.minute,
                ).time()
                time_field.value = selected_time[0].strftime("%H:%M")
                time_field.update()

        date_picker.on_change = on_date_selected
        time_picker.on_change = on_time_selected

        # pre-attach pickers to the page so they render properly
        self.page.overlay.append(date_picker)
        self.page.overlay.append(time_picker)

        def on_submit(e):
            new_due = datetime.combine(selected_date[0], selected_time[0])
            ctx.lending_entry.due_date = new_due.timestamp()
            self._lending_storage().update_by_id(ctx.lending_id, ctx.lending_entry)
            self._lending_storage().save()
            self.page.pop_dialog()

        def on_close(e):
            self.page.overlay.remove(date_picker)
            self.page.overlay.remove(time_picker)
            self.page.pop_dialog()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Edit Due Date"),
            content=ft.Column(
                [
                    ft.Row([date_field, time_field]),
                ],
                tight=True,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=on_close),
                ft.FilledButton("Save", icon=ft.Icons.SAVE, on_click=on_submit),
            ],
        )

        self.page.show_dialog(dialog)

    def on_lending_remove(self, ctx: OnLendingRemoveCtx):
        """Remove a lending entry without firing any statistical events.
        
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

    # ---- update entries ----

    def update_lending_entries(
        self,
        entries: dict[int, LendingEntry],
    ):
        self.lending_list_view.controls = []

        book_storage = self._book_storage()

        for lending_id, lending_entry in entries.items():
            book_id = lending_entry.book_id
            book = book_storage.get(book_id)
            assert book, f"Invalid lending entry, tried to get {book_id=}, but none could be found."
            lending_row = LendingBookRow(
                book=book,
                book_id=book_id,
                lending_entry=lending_entry,
                lending_id=lending_id,
            )

            # Wire callbacks
            lending_row.register_callback(OnLendingReturnCtx.id, self.on_lending_return)
            lending_row.register_callback(OnLendingEditDueCtx.id, self.on_lending_edit_due)
            lending_row.register_callback(OnLendingRemoveCtx.id, self.on_lending_remove)

            self.lending_list_view.controls.append(lending_row)