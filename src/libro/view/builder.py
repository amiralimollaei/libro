from typing import TypeVar

import flet as ft

from .tabs import AbstractTab

T = TypeVar("T", bound="AbstractTab")


class TabsBuilder:
    """Builds a NavigationBar-based layout suitable for mobile & Android."""

    def __init__(self, page: ft.Page):
        self.page = page

        self.tabs: list[tuple[AbstractTab, ft.NavigationBarDestination]] = []
        self._content_body: ft.Container | None = None
        self._nav_bar: ft.NavigationBar | None = None

    def build(self, **tabs_kwargs):
        self.page.clean()
        
        if not self.tabs:
            return ft.Container(expand=True)

        self._content_body = ft.Container(
            alignment=ft.Alignment.CENTER,
            content=self.tabs[0][0],
            padding=ft.Padding(20, 20, 20, 0),
            expand=True,
        )

        self._nav_bar = ft.NavigationBar(
            destinations=[d for _, d in self.tabs],
            on_change=self._on_navigation,
            selected_index=0,
        )

        return ft.Column(
            expand=True,
            controls=[self._content_body, self._nav_bar],
            **tabs_kwargs,
        )

    def _on_navigation(self):
        nav = self._nav_bar
        if nav is None:
            return
        idx = nav.selected_index
        if 0 <= idx < len(self.tabs) and self._content_body is not None:
            tab = self.tabs[idx][0]
            self._content_body.content = tab
            self._content_body.update()

    def new_tab(self, tab_cls: type[T], label: str, icon: ft.IconData) -> T:
        tab_obj = tab_cls()
        self.page.add(tab_obj)
        tab_obj.register_page(self.page)

        destination = ft.NavigationBarDestination(label=label, icon=icon)
        self.tabs.append((tab_obj, destination))
        return tab_obj
