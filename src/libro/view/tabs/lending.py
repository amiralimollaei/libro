import time
from datetime import datetime
from typing import Callable

import flet as ft

from ...callbacks import CallbackContext, CallbackMixin
from ...model import BookEntry, LendingEntry
from ...storage import JsonIdNumeralStorage, LibroPaths, LibroStorage
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


class LendingBookRow(ft.Card, CallbackMixin):
    """A Card-based lending entry with status coloring and action buttons."""
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

        content = ft.Container(
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

        super().__init__(
            elevation=1,
            margin=ft.Margin(0, 2, 0, 2),
            content=content,
        )

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
        # Initialize callbacks for the three lending operations
        self.__init_callbacks__([
            OnLendingReturnCtx.id,
            OnLendingEditDueCtx.id,
            OnLendingRemoveCtx.id,
        ])

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

        super().__init__(
            content=self.main_column,
            **container_kwargs,
        )

    def register_page(self, page: ft.Page):
        return

    def get_title(self) -> str:
        return "Lending"

    # ---- Registration methods for the Controller ----

    def register_on_lending_return(self, fn: Callable[[OnLendingReturnCtx], None]):
        self.register_callback(OnLendingReturnCtx.id, fn)

    def register_on_lending_edit_due(self, fn: Callable[[OnLendingEditDueCtx], None]):
        self.register_callback(OnLendingEditDueCtx.id, fn)

    def register_on_lending_remove(self, fn: Callable[[OnLendingRemoveCtx], None]):
        self.register_callback(OnLendingRemoveCtx.id, fn)

    # ---- update entries ----

    def update_lending_entries(
        self,
        entries: dict[int, LendingEntry],
    ):
        self.lending_list_view.controls = []

        book_storage = LibroStorage.get(JsonIdNumeralStorage[BookEntry], BookEntry)

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

            # Wire callbacks — the registered callbacks on LendingTab are forwarded to each row
            lending_row.register_callback(OnLendingReturnCtx.id, self._run_callbacks)
            lending_row.register_callback(OnLendingEditDueCtx.id, self._run_callbacks)
            lending_row.register_callback(OnLendingRemoveCtx.id, self._run_callbacks)

            self.lending_list_view.controls.append(lending_row)
