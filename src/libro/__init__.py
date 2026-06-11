import logging
import os

import flet as ft

from .asyncutils import DelayedTaskScheduler
from .callbacks.statistics import ensure_statistics_cache, register_statistics_callbacks

# Default logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
from .controller import (AddBookController, LendingController,
                          LibraryController, StatisticsController)
from .model import BookEntry, LendingEntry, Statistics, StatisticalEvent
from .search.engine import BookSearchEngine
from .storage import (JsonFileStorage, JsonIdNumeralStorage, LibroPaths,
                      LibroStorage)
from .view.builder import TabsBuilder
from .view.tabs import (AddTab, LendingTab, LibraryTab, StatisticsTab)


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

    def _on_fab_click(self, e):
        """FAB handler — switches to Add Book tab."""
        assert self.app_page

        if hasattr(self, '_builder'):
            self._builder.show_add_book_tab(self.add_tab)

    def show_snackbar(self, content: str):
        assert self.app_page
        self.app_page.show_dialog(
            ft.SnackBar(
                content=ft.Text(content),
                behavior=ft.SnackBarBehavior.FLOATING
            )
        )

    def app(self, page: ft.Page):
        page.window.width = 420
        page.window.height = 800
        page.window.min_width = 360
        page.window.min_height = 480

        page.title = "Libro - Your Personal Library"
        page.vertical_alignment = ft.MainAxisAlignment.CENTER
        page.padding = ft.Padding.zero()

        # Material 3 theming for a native Android feel
        page.theme_mode = ft.ThemeMode.SYSTEM
        page.theme = ft.Theme(
            color_scheme_seed="indigo",
            use_material3=True,
        )
        page.dark_theme = ft.Theme(
            color_scheme_seed="indigo",
            use_material3=True,
        )

        builder = TabsBuilder(page)
        self._builder = builder

        self.lib_tab = builder.new_tab(LibraryTab, label="Library", icon=ft.Icons.LIBRARY_BOOKS)
        self.lending_tab = builder.new_tab(LendingTab, label="Lending", icon=ft.Icons.OUTBOX)
        self.statistics_tab = builder.new_tab(StatisticsTab, label="Statistics", icon=ft.Icons.BAR_CHART)

        # Add Book tab is created but not shown in the nav — accessed via FAB
        self.add_tab = builder.new_hidden_tab(AddTab)

        # ---- Wire up the controllers ----

        # Library controller
        library_controller = LibraryController(
            page=page,
            view=self.lib_tab,
            search_engine=self.book_search_engine,
        )
        library_controller.register_callbacks()

        # Lending controller
        lending_controller = LendingController(
            page=page,
            view=self.lending_tab,
        )
        lending_controller.register_callbacks()

        # Add Book controller
        add_book_controller = AddBookController(
            page=page,
            view=self.add_tab,
            builder=builder,
            lib_tab=self.lib_tab,
        )
        add_book_controller.register_callbacks()

        # Statistics controller
        statistics_controller = StatisticsController(
            page=page,
            view=self.statistics_tab,
        )
        statistics_controller.register_callbacks()

        # ---- Initial data loads ----

        self.lib_tab.update_books(Libro.get_book_storage().objects)
        self.lending_tab.update_lending_entries(Libro.get_lending_storage().objects)

        fab = ft.FloatingActionButton(
            icon=ft.Icons.ADD,
            tooltip="Add a Book",
        )
        builder.set_fab(fab)

        page.add(ft.SafeArea(builder.build(on_fab_click=self._on_fab_click), expand=True))

        self.app_page = page

        # ---- Back / Close button handling ----

        def _navigate_back_or_exit():
            """If hidden tab is showing, go back to Library. Otherwise, show exit dialog."""
            if self._builder.is_showing_hidden_tab():
                self._builder.show_library_tab(self.lib_tab)
                self._builder.select_nav_index(0)
                return

            async def actually_close(e):
                await DelayedTaskScheduler.flush_all()
                await page.window.destroy()

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

        # Android: hardware back button fires on_view_pop
        def on_view_pop(e):
            _navigate_back_or_exit()

        page.on_view_pop = on_view_pop

        # Desktop: window close button (X) fires on_event
        def on_window_close(event: ft.WindowEvent):
            if event.type != ft.WindowEventType.CLOSE:
                return
            _navigate_back_or_exit()

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