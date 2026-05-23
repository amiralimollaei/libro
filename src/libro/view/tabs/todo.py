from typing import Any, Callable

import flet as ft

from libro.view.views import BookTile

from ...model.todo import Todo
from ...model.book import Book


TodoEventFn = Callable[[Todo, Book], Any]


class TodoTab(ft.Container):
    def __init__(self, **container_kwargs):
        self.on_todo_dismissed_fn: TodoEventFn | None = None

        self.book_list_view = ft.ListView(expand=True, spacing=0, padding=0)

        self.main_column = ft.Column(
            [
                self.book_list_view,
            ],
            expand=True
        )

        super().__init__(content=self.main_column, **container_kwargs)

    def update_todos(self, todos: list[Todo], books: list[Book]):
        self.book_list_view.controls = []
        for todo in todos:
            book = next(filter(lambda book: book.id == todo.id, books))

            self.book_list_view.controls.append(
                self.todo_view(todo, book)
            )

    def register_on_todo_dismissed_fn(self, fn: TodoEventFn):
        self.on_todo_dismissed_fn = fn

    def on_todo_dismissed(self, todo: Todo, book: Book):
        return self.on_todo_dismissed_fn(todo, book) if self.on_todo_dismissed_fn else None

    def todo_view(self, todo: Todo, book: Book):
        def on_dismiss(e):
            self.book_list_view.controls.remove(dismissable)
            self.on_todo_dismissed(todo, book)

        dismissable = ft.Dismissible(
            dismiss_direction=ft.DismissDirection.HORIZONTAL,
            background=ft.Container(
                ft.Text("Finshed", size=20, color=ft.Colors.WHITE),
                bgcolor=ft.Colors.GREEN,
                alignment=ft.Alignment.CENTER_LEFT,
                padding=ft.Padding.symmetric(horizontal=20)
            ),
            secondary_background=ft.Container(
                ft.Text("Give Up", size=20, color=ft.Colors.WHITE),
                bgcolor=ft.Colors.RED,
                alignment=ft.Alignment.CENTER_RIGHT,
                padding=ft.Padding.symmetric(horizontal=20)
            ),
            on_dismiss=on_dismiss,
            dismiss_thresholds={
                ft.DismissDirection.END_TO_START: 0.2,
                ft.DismissDirection.START_TO_END: 0.2,
            },
            content=BookTile(book, timestamp=todo.time),
        )

        return dismissable
