from datetime import datetime

import flet as ft

from libro.storage.paths import LibroPaths

from ..model.book import Book


# views shared by most tabs

class BookTile(ft.ListTile):
    def __init__(self, book: Book, timestamp: float | None = None):
        time_fmt = None
        if timestamp:
            time_fmt = datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y, %H:%M:%S")

        leading = None
        if book.cover and (book_cover_path:=LibroPaths.covers() / book.cover).exists():
            leading = ft.Image(str(book_cover_path.absolute()))

        super().__init__(
            leading=leading,
            title=ft.Text(book.title),
            subtitle=ft.Text(book.author.full_name() + (f"\nSince {time_fmt}" if time_fmt else ""), max_lines=2),
            is_three_line=True
        )
