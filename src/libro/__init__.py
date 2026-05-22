import flet as ft

from .view.main import MainView


def app(page: ft.Page):
    page.title = "Libro - Your Personal Library"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.padding = ft.Padding.zero()

    view = MainView()

    # register functionailty
    view.add_tab.register_on_save(lambda e: print(view.add_tab.get_book_object()))

    page.add(view)


def main():
    ft.run(app)
