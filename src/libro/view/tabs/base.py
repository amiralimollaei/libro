from abc import ABC, abstractmethod

import flet as ft


class BaseTab(ABC, ft.Container):
    @abstractmethod
    def register(self, page: ft.Page): ...