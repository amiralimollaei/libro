import flet as ft

from .view.main import MainView


def app(page: ft.Page):
    page.title = "Libro - Your Personal Library"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.padding = ft.Padding.zero()

    page.add(MainView())


def main():
    ft.run(app)
