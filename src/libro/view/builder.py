from typing import TypeVar

import flet as ft

from .tabs import AbstractTab


T = TypeVar("T", bound="AbstractTab")


class TabsBuilder:
    def __init__(self):
        self.tabs: list[tuple[AbstractTab, ft.Tab]] = []

    def build(self, **tabs_kwargs):
        tabs = []
        controls = []
        for tab_content, tab in self.tabs:
            controls.append(ft.Container(
                alignment=ft.Alignment.CENTER,
                content=tab_content,
                padding=ft.Padding.all(20)
            ))
            tabs.append(tab)

        return ft.Tabs(
            length=3,
            expand=True,
            content=ft.Column(
                expand=True,
                controls=[
                    ft.TabBar(tabs=tabs),
                    ft.TabBarView(expand=True, controls=controls)
                ],
            ),
            **tabs_kwargs
        )

    def new_tab(self, tab_cls: type[T], label: str, icon: ft.IconData) -> T:
        tab_obj = tab_cls()
        self.tabs.append((
            tab_obj, ft.Tab(label=label, icon=icon),
        ))
        return tab_obj
