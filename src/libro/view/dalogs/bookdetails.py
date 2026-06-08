from typing import Callable, Optional

import flet as ft

from ...callbacks import CallbackContext, CallbackMixin
from ...model.book import BookEntry
from ...model.statistics import BookStatisticsModel
from ...storage.paths import LibroPaths


class DialogClosedCtx(CallbackContext):
    id = "on_dialog_closed"


class OnDeleteBookCtx(CallbackContext):
    id = "on_delete_book"

    def __init__(self, book_id: int):
        super().__init__()
        self.book_id = book_id


class BookDetailsDialog(ft.AlertDialog, CallbackMixin):
    """
    Dialog that displays book details, statistics, and delete option.
    Shows pages read per day, progress per day, and estimated finish date.
    """

    def __init__(self, book: BookEntry, book_id: int, statistics: Optional[BookStatisticsModel] = None):
        self.__init_callbacks__([
            DialogClosedCtx.id,
            OnDeleteBookCtx.id,
        ])

        self.book = book
        self.book_id = book_id
        self.statistics = statistics or BookStatisticsModel(book_id=book_id)

        # book cover image
        cover_src = LibroPaths.assets() / "placeholder-cover.png"
        if book.cover:
            cover_src = LibroPaths.covers() / book.cover

        book_cover = ft.Container(
            width=100,
            height=150,
            border_radius=8,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            bgcolor=ft.Colors.BLUE_GREY_700,
            content=ft.Image(
                src=str(cover_src),
                fit=ft.BoxFit.COVER,
            ),
        )

        # book basic info
        book_info_column = ft.Column(
            spacing=8,
            expand=True,
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
                    f"Published: {book.publish_year}",
                    size=12,
                    color=ft.Colors.OUTLINE,
                ),
                ft.Text(
                    f"Genre: {book.genre.label}",
                    size=12,
                    color=ft.Colors.OUTLINE,
                ),
            ],
        )

        # progress section
        current_page = book.current_page or 0
        progress = current_page / book.pages if book.pages > 0 else 0

        progress_section = ft.Column(
            spacing=8,
            controls=[
                ft.Divider(),
                ft.Text(
                    "Progress",
                    size=14,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Row(
                    [
                        ft.Text(
                            f"{current_page} / {book.pages}",
                            size=12,
                        ),
                        ft.Text(
                            f"{progress * 100:.1f}%",
                            size=12,
                            color=ft.Colors.OUTLINE,
                        ),
                    ],
                    expand=True,
                ),
                ft.ProgressBar(
                    value=progress,
                    height=8,
                    border_radius=4,
                    expand=True,
                ),
            ],
        )

        # statistics section
        stats_section = ft.Column(
            spacing=8,
            controls=[
                ft.Divider(),
                ft.Text(
                    "Statistics",
                    size=14,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Column(
                    spacing=6,
                    controls=[
                        ft.Row(
                            [
                                ft.Text("Pages per day:", size=12),
                                ft.Text(
                                    self.statistics.get_pages_read_per_day_display(),
                                    size=12,
                                    color=ft.Colors.OUTLINE,
                                ),
                            ],
                            expand=True,
                        ),
                        ft.Row(
                            [
                                ft.Text("Progress per day:", size=12),
                                ft.Text(
                                    self.statistics.get_progress_per_day_display(),
                                    size=12,
                                    color=ft.Colors.OUTLINE,
                                ),
                            ],
                            expand=True,
                        ),
                        ft.Row(
                            [
                                ft.Text("Est. finish date:", size=12),
                                ft.Text(
                                    self.statistics.get_estimated_finish_date_display(),
                                    size=12,
                                    color=ft.Colors.OUTLINE,
                                ),
                            ],
                            expand=True,
                        ),
                        ft.Row(
                            [
                                ft.Text("Reading time:", size=12),
                                ft.Text(
                                    self.statistics.get_reading_time_display(),
                                    size=12,
                                    color=ft.Colors.OUTLINE,
                                ),
                            ],
                            expand=True,
                        ),
                        ft.Row(
                            [
                                ft.Text("Days reading:", size=12),
                                ft.Text(
                                    self.statistics.get_days_reading_display(),
                                    size=12,
                                    color=ft.Colors.OUTLINE,
                                ),
                            ],
                            expand=True,
                        ),
                    ],
                ),
            ],
        )

        # delete confirmation dialog
        self.delete_confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Delete Book?"),
            content=ft.Text(
                f"Are you sure you want to remove '{book.title}' from your library?"
            ),
            actions=[
                ft.TextButton(
                    "Cancel",
                    on_click=self._on_delete_cancel,
                ),
                ft.FilledButton(
                    "Delete",
                    on_click=self._on_delete_confirm,
                ),
            ],
        )

        # delete button
        delete_button = ft.ElevatedButton(
            "Remove from Library",
            icon=ft.Icons.DELETE,
            bgcolor=ft.Colors.ERROR,
            color=ft.Colors.WHITE,
            on_click=self._on_delete_click,
        )

        # main content
        main_content = ft.Column(
            spacing=12,
            controls=[
                ft.Row(
                    [
                        book_cover,
                        book_info_column,
                    ],
                    spacing=16,
                    expand=True,
                ),
                progress_section,
                stats_section,
                ft.Divider(),
                delete_button,
            ],
        )

        super().__init__(
            modal=True,
            title=ft.Text(
                "Book Details",
                weight=ft.FontWeight.BOLD,
            ),
            content=ft.Container(
                width=500,
                content=main_content,
            ),
            actions=[
                ft.FilledButton(
                    "Close",
                    on_click=self._close,
                ),
            ],
        )

    def _on_delete_click(self, e):
        """Show the delete confirmation dialog."""
        self.page.show_dialog(self.delete_confirm_dialog)

    def _on_delete_cancel(self, e):
        """Cancel the delete operation."""
        # close the confirm dialog
        self.page.pop_dialog()

    def _on_delete_confirm(self, e):
        """Confirm and execute the delete operation."""
        # close the confirm dialog
        self.page.pop_dialog()
        # close self dialog
        self._close(e)
        self._run_callbacks(OnDeleteBookCtx(self.book_id))

    def _close(self, e):
        self.page.pop_dialog()
        self._run_callbacks(DialogClosedCtx())

    def register_on_delete_book(self, fn: Callable[[OnDeleteBookCtx], None]):
        self.register_callback(OnDeleteBookCtx.id, fn)

    def register_on_dialog_closed(self, fn: Callable[[DialogClosedCtx], None]):
        self.register_callback(DialogClosedCtx.id, fn)
