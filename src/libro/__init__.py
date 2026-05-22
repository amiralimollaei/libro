import flet as ft

from .storage.paths import LibroPaths
from .model.book import Book
from .storage.json import JsonObjectStorage
from .view.main import MainView


class Libro(MainView):
    def __init__(self):
        super().__init__()

        self.books_storage = JsonObjectStorage[Book].from_directory(item_cls=Book, directory=LibroPaths.books())
        self.lib_tab.update_books(self.books_storage.objects)

        self.add_tab.register_on_save(lambda x: self.add_new_book(self.add_tab.get_book_object()))

    def add_new_book(self, book: Book):
        self.books_storage.add(book)
        self.books_storage.save()

        self.lib_tab.update_books(self.books_storage.objects)
        self.add_tab.reset()
        self.update()

    def run(self):
        def app(page: ft.Page):
            page.title = "Libro - Your Personal Library"
            page.vertical_alignment = ft.MainAxisAlignment.CENTER
            page.padding = ft.Padding.zero()
            page.add(self)

        ft.run(app)


def main():
    LibroPaths.root().mkdir(exist_ok=True)
    Libro().run()
