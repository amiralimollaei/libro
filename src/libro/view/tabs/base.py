from abc import ABC, abstractmethod

import flet as ft

from ...callbacks import CallbackMixin


class AbstractTab(ABC, ft.Container, CallbackMixin):
    @abstractmethod
    def register_page(self, page: ft.Page): ...
