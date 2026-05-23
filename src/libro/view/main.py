import flet as ft

from .tabs import *


class MainView(ft.Tabs):
    def __init__(self, **tabs_kwargs):
        self.lib_tab = LibraryTab()
        self.todo_tab = TodoTab()
        self.add_tab = AddTab()

        self.bar = ft.TabBar(
            tabs=[
                ft.Tab(label="Library", icon=ft.icons.Icons.LIBRARY_BOOKS),
                ft.Tab(label="Todo List", icon=ft.icons.Icons.BOOKMARK),
                ft.Tab(label="Add Book", icon=ft.icons.Icons.ADD_CIRCLE),
            ]
        )

        self.bar_view = ft.TabBarView(
            expand=True,
            controls=[
                ft.Container(
                    alignment=ft.Alignment.CENTER,
                    content=self.lib_tab,
                    padding=ft.Padding.symmetric(horizontal=10)
                ),
                ft.Container(
                    alignment=ft.Alignment.CENTER,
                    content=self.todo_tab,
                    padding=ft.Padding.symmetric(horizontal=10)
                ),
                ft.Container(
                    alignment=ft.Alignment.CENTER,
                    content=self.add_tab,
                    padding=ft.Padding.all(20)
                ),
            ],
        )

        super().__init__(
            length=3,
            expand=True,
            content=ft.Column(
                expand=True,
                controls=[
                    self.bar,
                    self.bar_view
                ],
            ),
            **tabs_kwargs
        )
