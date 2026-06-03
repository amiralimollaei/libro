import flet as ft

from .tabs import *


class MainView(ft.Tabs):
    def __init__(self, **tabs_kwargs):
        self.lib_tab = LibraryTab()
        self.lending_tab = LendingTab()
        self.add_tab = AddTab()

        self.bar = ft.TabBar(
            tabs=[
                ft.Tab(label="Library", icon=ft.Icons.LIBRARY_BOOKS),
                ft.Tab(label="Lending", icon=ft.Icons.OUTBOX),
                ft.Tab(label="Add Book", icon=ft.Icons.ADD_CIRCLE),
            ]
        )

        self.bar_view = ft.TabBarView(
            expand=True,
            controls=[
                ft.Container(
                    alignment=ft.Alignment.CENTER,
                    content=self.lib_tab,
                    padding=ft.Padding(left=20, right=20, top=20, bottom=0)
                ),
                ft.Container(
                    alignment=ft.Alignment.CENTER,
                    content=self.lending_tab,
                    padding=ft.Padding(left=20, right=20, top=20, bottom=0)
                ),
                ft.Container(
                    alignment=ft.Alignment.CENTER,
                    content=self.add_tab,
                    padding=ft.Padding.all(20)
                ),
            ],
        )

        self.lib_tab.register_lend_callback(
            self.on_lend_book_requested
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

    def on_lend_book_requested(self, ctx: OnLendBookRequestedCtx):
        # TODO:
        # 1- show lending dialog
        # 2- create LendingEntry
        # 3- add to lending storage
        ...
