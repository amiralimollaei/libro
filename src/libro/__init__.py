import logging
import os
import time

import flet as ft

from .asyncutils import DelayedTaskScheduler
from .callbacks.statistics import ensure_statistics_cache, on_reading_event_added, register_statistics_callbacks

# Default logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
from .model import BookEntry, BookLentEvent, BookReturnedEvent, LendingEntry, Person, Statistics, StatisticalEvent
from .search.engine import BookSearchEngine
from .storage import (JsonFileStorage, JsonIdNumeralStorage, LibroPaths,
                      LibroStorage)
from .view.builder import TabsBuilder
from .view.dalogs.lending import LendingDialog
from .view.tabs import (AddTab, LendingTab, LibraryTab,
                        OnLendBookRequestedCtx, StatisticsTab)


class Libro:
    def __init__(self):
        self.app_page: ft.Page | None = None

        LibroStorage.new(
            storage_cls=JsonIdNumeralStorage[BookEntry],
            item_cls=BookEntry,
            path=LibroPaths.books()
        )

        LibroStorage.new(
            storage_cls=JsonIdNumeralStorage[LendingEntry],
            item_cls=LendingEntry,
            path=LibroPaths.lending()
        )

        LibroStorage.new(
            storage_cls=JsonFileStorage[Statistics],
            item_cls=Statistics,
            path=LibroPaths.statistics()
        )

        LibroStorage.new(
            storage_cls=JsonIdNumeralStorage[StatisticalEvent],
            item_cls=StatisticalEvent,
            path=LibroPaths.events()
        )

        self.book_search_engine = BookSearchEngine()

        # register statistics event listeners and ensure cache is up-to-date
        register_statistics_callbacks()
        ensure_statistics_cache()

    def on_lend_book_requested(self, ctx: OnLendBookRequestedCtx):
        assert self.app_page

        def on_lending_dialog_submit(dialog: LendingDialog):
            lending_storage = self.get_lending_storage()
            lend_id = lending_storage.add(LendingEntry(
                book_id=ctx.book_id,
                borrower=Person(name=dialog.borrower),
                lent_date=time.time(),
                due_date=dialog.due_at.timestamp()  # pyright: ignore[reportOptionalMemberAccess]
            ))
            lending_storage.save()
            
            # Emit BookLentEvent
            event = StatisticalEvent(
                book_id=ctx.book_id,
                timestamp=time.time(),
                book_lent=BookLentEvent(
                    lend_id=lend_id,
                    total_pages=ctx.book.pages
                )
            )
            self.get_reading_events_storage().add(event)
            self.get_reading_events_storage().save()

        self.app_page.show_dialog(
            LendingDialog(
                book_title=ctx.book.title,
                on_submit=on_lending_dialog_submit
            )
        )

    def return_book(self, lending_id: int, book_id: int):
        """Mark a lent book as returned and emit BookReturnedEvent."""
        lending_storage = self.get_lending_storage()
        lending_entry = lending_storage.get(lending_id)
        
        if lending_entry is None:
            return
        
        # Calculate overdue_time if applicable
        current_time = time.time()
        overdue_time = None
        if current_time > lending_entry.due_date:
            overdue_time = current_time - lending_entry.due_date  # seconds overdue
        
        # Update the lending entry with returned time
        lending_entry.returned_time = current_time
        lending_storage.update_by_id(lending_id, lending_entry)
        lending_storage.save()
        
        # Emit BookReturnedEvent
        event = StatisticalEvent(
            book_id=book_id,
            timestamp=current_time,
            book_returned=BookReturnedEvent(
                lend_id=lending_id,
                overdue_time=overdue_time
            )
        )
        self.get_reading_events_storage().add(event)
        self.get_reading_events_storage().save()

    @staticmethod
    def get_book_storage() -> JsonIdNumeralStorage[BookEntry]:
        return LibroStorage.get(JsonIdNumeralStorage[BookEntry], BookEntry)

    @staticmethod
    def get_lending_storage() -> JsonIdNumeralStorage[LendingEntry]:
        return LibroStorage.get(JsonIdNumeralStorage[LendingEntry], LendingEntry)

    @staticmethod
    def get_reading_events_storage() -> JsonIdNumeralStorage[StatisticalEvent]:
        return LibroStorage.get(JsonIdNumeralStorage[StatisticalEvent], StatisticalEvent)

    @staticmethod
    def get_statistics_storage() -> JsonFileStorage[Statistics]:
        return LibroStorage.get(JsonFileStorage[Statistics], Statistics)

    def on_add_book(self, e):
        assert self.app_page

        book = None
        try:
            book = self.add_tab.get_book_object()
        except AttributeError:
            banner = ft.AlertDialog(
                title=ft.Text("Add Book"),
                content=ft.Text("Please fill all the required fields."),
                actions=[
                    ft.TextButton(
                        "Ok",
                        on_click=lambda e: self.app_page.pop_dialog()  # pyright: ignore[reportOptionalMemberAccess]
                    )
                ],
                open=True,
            )
            self.app_page.show_dialog(banner)
            return

        book_storage = Libro.get_book_storage()
        book_storage.add(book)
        book_storage.save()

        self.add_tab.reset()

        self.app_page.show_dialog(dialog=ft.AlertDialog(
            title=ft.Text("Add Book"),
            content=ft.Text("Book was successfully added to your library."),
            actions=[
                ft.TextButton(
                    "Ok",
                    on_click=lambda e: self.app_page.pop_dialog()  # pyright: ignore[reportOptionalMemberAccess]
                )
            ],
            open=True,
        ))

    def app(self, page: ft.Page):
        page.window.min_width = 480
        page.window.min_height = 480

        page.title = "Libro - Your Personal Library"
        page.vertical_alignment = ft.MainAxisAlignment.CENTER
        page.padding = ft.Padding.zero()

        builder = TabsBuilder()

        self.lib_tab = builder.new_tab(LibraryTab, label="Library", icon=ft.Icons.LIBRARY_BOOKS)
        self.lending_tab = builder.new_tab(LendingTab, label="Lending", icon=ft.Icons.OUTBOX)
        self.statistics_tab = builder.new_tab(StatisticsTab, label="Statistics", icon=ft.Icons.BAR_CHART)
        self.add_tab = builder.new_tab(AddTab, label="Add Book", icon=ft.Icons.ADD_CIRCLE)

        self.lib_tab.register_lend_callback(self.on_lend_book_requested)
        self.lib_tab.register_search_engine(self.book_search_engine)
        self.lib_tab.update_books(Libro.get_book_storage().objects)

        self.lending_tab.update_lending_entries(Libro.get_lending_storage().objects)

        self.add_tab.register_on_add_book_callback(self.on_add_book)

        page.add(ft.SafeArea(builder.build(), expand=True))

        self.statistics_tab._refresh_data()

        self.app_page = page

        # exit confirmation dialog
        def on_window_close(event: ft.WindowEvent):
            async def actually_close(e):
                await DelayedTaskScheduler.flush_all()
                await page.window.destroy()

            if event.type != ft.WindowEventType.CLOSE:
                return
            dlg = ft.AlertDialog(
                title=ft.Text("Exit"),
                content=ft.Text("Are you sure you want to exit Libro?"),
                actions=[
                    ft.TextButton(
                        "Cancel",
                        on_click=lambda e: page.pop_dialog()
                    ),
                    ft.TextButton(
                        "Exit",
                        on_click=actually_close
                    ),
                ],
            )
            page.show_dialog(dlg)

        page.window.prevent_close = True
        page.window.on_event = on_window_close

    def run(self):
        ft.run(self.app, assets_dir=str(LibroPaths.assets().absolute()))


def main():
    LibroPaths.root().mkdir(exist_ok=True)
    Libro().run()


if __package__ is not None:
    import importlib.resources
    import shutil

    MODULE_PATH = importlib.resources.files(__package__)
    RESOURCES_PATH = str(MODULE_PATH / "assets")

    # If the LibroPaths.RESOURCES folder doesn't exist, We should copy all our default assets
    def copy_if_absent(src: str, dst: str, *, follow_symlinks: bool = True):
        if os.path.exists(dst):
            if os.path.isdir(dst):
                raise FileExistsError(f"directory exists with the same name as destination the file: {dst}")
            return
        shutil.copy2(src, dst, follow_symlinks=follow_symlinks)

    def copy_default_resources():
        os.makedirs(LibroPaths.assets(), exist_ok=True)
        shutil.copytree(RESOURCES_PATH, LibroPaths.assets(), dirs_exist_ok=True, copy_function=copy_if_absent)

    copy_default_resources()


if __name__ == "__main__":
    main()
