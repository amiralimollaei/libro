import flet as ft

from ..model import Statistics
from ..storage import JsonFileStorage, LibroStorage, OnObjectsChangedCtx
from ..view.tabs.statistics import StatisticsTab
from .base import AbstractController


class StatisticsController(AbstractController):
    """Controller for the Statistics tab.

    Handles auto-refresh of statistics data when the cache changes.
    """

    def __init__(self, page: ft.Page, view: StatisticsTab):
        super().__init__(page)
        self.view = view

    # ---- Callback registration ----

    def register_callbacks(self) -> None:
        stats_storage: JsonFileStorage[Statistics] = LibroStorage.get(
            JsonFileStorage[Statistics], Statistics
        )
        stats_storage.register_change_callback(self._on_stats_changed)

    # ---- Business logic ----

    def _on_stats_changed(self, ctx: OnObjectsChangedCtx):
        """Storage change listener — refresh statistics display."""
        self.view.refresh_data()