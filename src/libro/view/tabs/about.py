from functools import partial

import flet as ft

from ...storage import LibroPaths
from .base import AbstractTab


class AboutTab(AbstractTab):
    """
    A simple static tab that displays information about the author and GitHub link.
    """

    def __init__(self, **container_kwargs):
        self.__init_callbacks__([])

        description = ft.Text(
            "Libro is a personal library manager built with Flet.\n\n"
            "Created by AmirAli Mollaei.",
            size=16,
            weight=ft.FontWeight.NORMAL,
            text_align=ft.TextAlign.CENTER,
        )

        # github repo link
        github_button = ft.ElevatedButton(
            "GitHub: amiralimollaei/libro",
            on_click=partial(self._launch_url_action, url="https://github.com/amiralimollaei/libro/"),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.Padding.symmetric(horizontal=16, vertical=8),
            ),
        )

        # website link
        website_button = ft.ElevatedButton(
            "Website: amiralimollaei.github.io",
            on_click=partial(self._launch_url_action, url="https://amiralimollaei.github.io/"),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.Padding.symmetric(horizontal=16, vertical=8),
            ),
        )

        # email
        email_button = ft.ElevatedButton(
            "Email: me.amiralimollaei@gmail.com",
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.Padding.symmetric(horizontal=16, vertical=8),
            ),
        )

        logo_container = ft.Container(
            border_radius=16,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            bgcolor=ft.Colors.BLUE_GREY_700,
            content=ft.Image(
                src=str(LibroPaths.assets() / "icon.png"),
                fit=ft.BoxFit.COVER,
            ),
        )

        super().__init__(
            content=ft.Column(
                controls=[description, github_button, website_button, email_button, logo_container],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=16,
                expand=True,
                scroll=ft.ScrollMode.AUTO
            ),
            **container_kwargs
        )

    async def _launch_url_action(self, e, url: str):
        if hasattr(self.page, "launch_url"):
            await self.page.launch_url(  # pyright: ignore[reportAttributeAccessIssue]
                url,
                web_popup_window_name=ft.UrlTarget.BLANK
            )

    def register_page(self, page: ft.Page):
        pass

    def get_title(self) -> str:
        return "About"

    async def on_focused(self) -> None:
        pass