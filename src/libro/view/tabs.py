import flet as ft


class AddTab(ft.Container):
    def __init__(self, **container_kwargs):
        self.title_input = ft.TextField(label="Book Title", expand=True)
        self.author_input = ft.TextField(label="Author", expand=True)
        self.pages_input = ft.TextField(label="Pages", keyboard_type=ft.KeyboardType.NUMBER, width=200)
        self.genre_input = ft.Dropdown(
            label="Genre",
            options=[
                ft.dropdown.Option("Fiction"),
                ft.dropdown.Option("Non-Fiction"),
                ft.dropdown.Option("Sci-Fi"),
                ft.dropdown.Option("Mystery"),
                ft.dropdown.Option("Biography"),
            ],
            width=200
        )

        self.main_column = ft.Column(
            [
                ft.Row([
                    self.title_input
                ]),
                ft.Row([
                    self.author_input, self.pages_input, self.genre_input,

                ]),
                ft.ElevatedButton(
                    "Save to Library",
                    icon=ft.icons.Icons.SAVE,
                    on_click=lambda x: None,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
                ),
            ],
            expand=True,
            spacing=20
        )

        super().__init__(content=self.main_column, **container_kwargs)


class LibraryTab(ft.Container):
    def __init__(self, **container_kwargs):
        self.book_list_view = ft.ListView(expand=True, spacing=10, padding=20)

        self.main_column = ft.Column(
            [
                self.book_list_view,
            ],
            expand=True
        )

        super().__init__(content=self.main_column, **container_kwargs)
