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
    Shows reading progress, weekly/monthly aggregates, and a bar chart.
    """

    BAR_COLOR = ft.Colors.BLUE_400

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
        book_info_controls = [
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
        ]

        if book.summary:
            book_info_controls.append(
                ft.Text(
                    book.summary,
                    size=12,
                    italic=True,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
            )

        book_info_column = ft.Column(
            spacing=8,
            expand=True,
            controls=book_info_controls,
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

        ## statistics
        
        stats_section = self._build_stats_section()

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
        delete_button = ft.FilledButton(
            "Remove Book",
            icon=ft.Icons.DELETE,
            bgcolor=ft.Colors.RED_400,
            color=ft.Colors.WHITE,
            on_click=self._on_delete_click,
        )

        # main content
        main_content = ft.Column(
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
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
                height=600,
                content=main_content,
            ),
            actions=[
                delete_button,
                ft.FilledButton(
                    "Close",
                    on_click=self._close,
                ),
            ],
        )


    def _build_stats_section(self) -> ft.Column:
        """Build the statistics section with weekly/monthly stats and a bar chart."""
        controls: list[ft.Control] = [
            ft.Divider(),
            ft.Text("Statistics", size=14, weight=ft.FontWeight.BOLD),
        ]

        # weekly/monthly summary
        controls.append(self._build_period_summary_row())

        # monthly comparison
        controls.append(self._build_comparison_row())

        # bar chart (weekly)
        chart = self._build_bar_chart()
        if chart is not None:
            controls.append(ft.Text("Weekly Reading", size=12, weight=ft.FontWeight.BOLD))
            controls.append(chart)
            controls.append(ft.Container(height=4))

        # reading pace
        controls.append(ft.Divider(height=1))
        controls.append(self._build_pace_row())

        return ft.Column(spacing=8, controls=controls)

    def _build_period_summary_row(self) -> ft.Row:
        """Row showing this week's pages and this month's pages + progress."""
        stats = self.statistics

        this_week_text = ft.Text(
            f"This week: {stats.get_this_week_pages_display()}",
            size=12,
        )
        this_month_text = ft.Text(
            f"This month: {stats.get_this_month_pages_display()}",
            size=12,
        )
        month_progress_text = ft.Text(
            f"Monthly Progress: {stats.get_this_month_progress_display()}",
            size=12,
            color=ft.Colors.OUTLINE,
        )

        return ft.Row(
            spacing=16,
            controls=[
                ft.Column(spacing=2, controls=[this_week_text, this_month_text]),
                ft.Column(spacing=2, controls=[month_progress_text]),
            ],
        )

    def _build_comparison_row(self) -> ft.Row:
        """Row showing comparison of this month vs last month."""
        stats = self.statistics
        comparison_text = ft.Text(
            f"vs last month: {stats.get_monthly_comparison_display()}",
            size=12,
            color=ft.Colors.OUTLINE,
        )
        return ft.Row(
            controls=[
                ft.Icon(
                    ft.Icons.TRENDING_UP if stats.this_month_pages and stats.last_month_pages and stats.this_month_pages >= stats.last_month_pages else ft.Icons.TRENDING_DOWN,
                    size=16,
                    color=ft.Colors.GREEN_400 if (stats.this_month_pages or 0) >= (stats.last_month_pages or 0) else ft.Colors.RED_400,
                    visible=stats.this_month_pages is not None and stats.last_month_pages is not None,
                ),
                comparison_text,
            ],
        )

    def _build_bar_chart(self) -> Optional[ft.Column]:
        """
        Build a horizontal bar chart from weekly_history data.
        Each bar uses ProgressBar for natural horizontal expansion.
        """
        history = self.statistics.weekly_history
        if not history:
            return None

        max_pages = max(entry.pages for entry in history)
        if max_pages <= 0:
            return None

        bar_rows: list[ft.Control] = []
        for entry in history:
            fraction = entry.pages / max_pages

            label = ft.Text(entry.label, size=10, width=55, text_align=ft.TextAlign.RIGHT)
            page_count = ft.Text(str(entry.pages), size=10, color=ft.Colors.OUTLINE, width=30)

            # Use a styled ProgressBar as the bar — naturally expands horizontally
            bar = ft.ProgressBar(
                value=fraction,
                height=16,
                border_radius=4,
                expand=True,
                bgcolor=ft.Colors.with_opacity(0.15, self.BAR_COLOR),
                color=self.BAR_COLOR,
            )

            bar_rows.append(
                ft.Row(
                    spacing=6,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[label, bar, page_count],
                )
            )

        return ft.Column(spacing=4, controls=bar_rows)

    def _build_pace_row(self) -> ft.Row:
        """Row showing reading pace (pages per day + days reading)."""
        stats = self.statistics
        return ft.Row(
            spacing=16,
            controls=[
                ft.Column(
                    spacing=2,
                    controls=[
                        ft.Text("Pages per day:", size=12),
                        ft.Text(
                            stats.get_pages_read_per_day_display(),
                            size=12,
                            color=ft.Colors.OUTLINE,
                        ),
                    ],
                ),
                ft.Column(
                    spacing=2,
                    controls=[
                        ft.Text("Days reading:", size=12),
                        ft.Text(
                            stats.get_days_reading_display(),
                            size=12,
                            color=ft.Colors.OUTLINE,
                        ),
                    ],
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