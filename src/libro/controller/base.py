from abc import ABC, abstractmethod

import flet as ft


class AbstractController(ABC):
    """Base class for all controllers in the MVC architecture.

    Controllers handle business logic, storage operations, and dialog flows.
    They register callbacks on their corresponding view tabs.
    """

    def __init__(self, page: ft.Page):
        self.page = page

    @abstractmethod
    def register_callbacks(self) -> None:
        """Wire all callbacks from the view to this controller's methods."""
        ...
