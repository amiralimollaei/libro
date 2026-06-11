from abc import ABC, abstractmethod
from typing import Optional

import flet as ft

from ...callbacks import CallbackMixin


class AbstractTab(ABC, ft.Container, CallbackMixin):
    @abstractmethod
    def register_page(self, page: ft.Page): ...

    @abstractmethod
    def get_title(self) -> str: ...
