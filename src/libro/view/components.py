from typing import Optional

import flet as ft


# views shared by more than one tab

class BookCover(ft.Container):
    """
    Shared book cover component with two modes:

    - overlay_text=None (or empty): renders just the cover image.
    - overlay_text=<string>: renders a Stack with the cover image,
      a dark semi-transparent overlay, and the overlay text centered on top.

    Call set_overlay_text(text) to update the overlay text dynamically.
    """

    def __init__(
        self,
        cover_src: str,
        overlay_text: Optional[str] = None,
        width: int = 80,
        height: int = 120,
        border_radius: int = 8,
    ):
        image_container = ft.Container(
            width=width,
            height=height,
            border_radius=border_radius,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            bgcolor=ft.Colors.BLUE_GREY_700,
            content=ft.Image(
                src=cover_src,
                fit=ft.BoxFit.COVER,
            ),
        )

        if overlay_text:
            self.overlay_text_control = ft.Text(
                overlay_text,
                color=ft.Colors.WHITE,
                weight=ft.FontWeight.BOLD,
            )

            # mode with dark overlay + text
            content = ft.Stack(
                width=width,
                height=height,
                controls=[
                    image_container,
                    ft.Container(
                        width=width,
                        height=height,
                        bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.BLACK),
                    ),
                    ft.Container(
                        width=width,
                        height=height,
                        alignment=ft.Alignment.CENTER,
                        content=self.overlay_text_control,
                    ),
                ],
            )
        else:
            self.overlay_text_control = None
            # plain cover image without overlay
            content = image_container

        super().__init__(
            width=width,
            height=height,
            content=content,
        )

    def set_overlay_text(self, text: str):
        """Update the overlay text in-place (no widget rebuild needed)."""
        if self.overlay_text_control is not None:
            self.overlay_text_control.value = text
            self.update()
