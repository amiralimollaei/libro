from datetime import datetime

import flet as ft

from ..model.book import Book


# views shared by most tabs

class BookTile(ft.ListTile):
    def __init__(self, book: Book, timestamp: float | None = None):
        time_fmt = None
        if timestamp:
            time_fmt = datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y, %H:%M:%S")
        super().__init__(
            title=ft.Text(book.title),
            subtitle=ft.Text(book.author.full_name() + (f"\n{time_fmt}" if time_fmt else ""), max_lines=2),
            is_three_line=True
        )
