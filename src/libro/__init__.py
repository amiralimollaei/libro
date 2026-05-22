import flet as ft

from .view.main import MainView


class Libro(MainView):
    def __init__(self):
        super().__init__()
        self.add_tab.register_on_save(lambda e: print(self.add_tab.get_book_object()))

    def run(self):
        def app(page: ft.Page):
            page.title = "Libro - Your Personal Library"
            page.vertical_alignment = ft.MainAxisAlignment.CENTER
            page.padding = ft.Padding.zero()
            page.add(self)

        ft.run(app)

def main():
    Libro().run()
