from typing import Callable, Optional, TypeVar

import flet as ft

from .tabs import AbstractTab

T = TypeVar("T", bound="AbstractTab")


class TabsBuilder:
    """Builds an Android-style layout with AppBar, content body, FAB, and bottom NavigationBar.

    --- View (MVC) ---
    Exposes a clean public API so the Controller never needs to access private members.
    """

    def __init__(self, page: ft.Page):
        self.page = page

        self.tabs: list[tuple[AbstractTab, ft.NavigationBarDestination]] = []
        self._content_switcher: ft.AnimatedSwitcher | None = None
        self._nav_bar: ft.NavigationBar | None = None
        self._app_bar: ft.AppBar | None = None
        self._fab: Optional[ft.FloatingActionButton] = None

        self._current_tab_index = 0
        self._showing_hidden_tab: bool = False

    # ── Public API for the Controller ──────────────────────────────────

    def set_fab(self, fab: ft.FloatingActionButton):
        """Set a FAB that appears on the Library tab."""
        self._fab = fab

    def show_add_book_tab(self, add_tab: AbstractTab):
        """Switch content to the Add Book form, hide the FAB, update title."""
        if self._content_switcher is not None:
            self._content_switcher.content = add_tab
            self._content_switcher.update()
        if self._fab is not None:
            self._fab.visible = False
            self._fab.update()
        self._set_app_bar_title("Add a Book")
        self._showing_hidden_tab = True

    def is_showing_hidden_tab(self) -> bool:
        """Check if a hidden tab (e.g. Add Book) is currently displayed."""
        return self._showing_hidden_tab

    def show_library_tab(self, library_tab: AbstractTab):
        """Switch content back to the Library tab, show the FAB, update title."""
        if self._content_switcher is not None:
            self._content_switcher.content = library_tab
            self._content_switcher.update()
        if self._fab is not None:
            self._fab.visible = True
            self._fab.update()
        self._set_app_bar_title(library_tab.get_title())
        self._showing_hidden_tab = False

    def select_nav_index(self, index: int):
        """Programmatically select a navigation bar item."""
        if self._nav_bar is not None:
            self._nav_bar.selected_index = index
            self._nav_bar.update()

    # ── Private helpers ────────────────────────────────────────────────

    def _set_app_bar_title(self, title: str):
        if self._app_bar is not None:
            self._app_bar.title = title
            self._app_bar.update()

    def _update_fab_visibility(self, tab_index: int):
        """Show FAB only on the Library tab (index 0)."""
        if self._fab is not None:
            self._fab.visible = (tab_index == 0)
            self._fab.update()

    def build(self, on_fab_click: Callable | None = None, **tabs_kwargs):
        """Construct the full page layout.

        Args:
            on_fab_click: Callback invoked when the FAB is tapped.
        """
        self.page.clean()

        if not self.tabs:
            return ft.Container(expand=True)

        first_tab = self.tabs[0][0]

        # Content body — uses AnimatedSwitcher for smooth tab transitions.
        # clip_behavior=HARD_EDGE ensures content inside isn't clipped/intercepted by the switcher.
        self._content_switcher = ft.AnimatedSwitcher(
            content=first_tab,
            transition=ft.AnimatedSwitcherTransition.FADE,
            duration=200,
            reverse_duration=200,
            switch_in_curve=ft.AnimationCurve.EASE_IN_OUT,
            switch_out_curve=ft.AnimationCurve.EASE_IN_OUT,
            expand=True,
            # clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )

        # Wrap the switcher with proper padding
        content_container = ft.Container(
            alignment=ft.Alignment.TOP_CENTER,
            content=self._content_switcher,
            padding=ft.Padding(16, 8, 16, 8),
            expand=True,
        )

        # Navigation bar at the bottom
        self._nav_bar = ft.NavigationBar(
            destinations=[d for _, d in self.tabs],
            on_change=self._on_navigation,
            selected_index=0,
            animation_duration=200,
        )

        # AppBar — Material 3 centered title, subtle surface tint
        self._app_bar = ft.AppBar(
            title=first_tab.get_title(),
            center_title=True,
            bgcolor=ft.Colors.PRIMARY_CONTAINER,
            elevation=0,
        )

        # Main column (AppBar + content + nav)
        main_column = ft.Column(
            expand=True,
            spacing=0,
            controls=[
                self._app_bar,
                content_container,
                self._nav_bar,
            ],
        )

        # Build the FAB if one was set — place it as an overlay on the main_column.
        # The Container wrapping the FAB is sized to JUST fit the FAB (56dp square),
        # and positioned at BOTTOM_RIGHT so it doesn't block the rest of the UI.
        if self._fab is not None:
            self._fab.visible = True
            self._fab.on_click = on_fab_click

            return ft.Stack(
                expand=True,
                controls=[
                    main_column,
                    ft.Container(
                        # Only expand enough to hold the FAB, not the full screen
                        width=56,
                        height=56,
                        content=self._fab,
                        alignment=ft.Alignment.CENTER,
                        # Position at bottom-right above the nav bar
                        right=16,
                        bottom=96,
                    ),
                ],
            )

        return main_column

    def _on_navigation(self):
        nav = self._nav_bar
        if nav is None:
            return
        idx = nav.selected_index

        if 0 <= idx < len(self.tabs) and self._content_switcher is not None:
            tab = self.tabs[idx][0]
            self._content_switcher.content = tab
            self._content_switcher.update()

            # Update AppBar title
            if self._app_bar is not None:
                self._app_bar.title = tab.get_title()
                self._app_bar.update()

            # Show/hide FAB (only on Library tab = index 0)
            self._update_fab_visibility(idx)

            self._current_tab_index = idx

    def new_hidden_tab(self, tab_cls: type[T]) -> T:
        """Create a tab that is registered with the page but not shown in navigation bar.

        Useful for tabs accessed via FAB or other non-navigation means.
        """
        tab_obj = tab_cls()
        self.page.add(tab_obj)
        tab_obj.register_page(self.page)
        return tab_obj

    def new_tab(self, tab_cls: type[T], label: str, icon: ft.IconData) -> T:
        tab_obj = tab_cls()
        self.page.add(tab_obj)
        tab_obj.register_page(self.page)

        destination = ft.NavigationBarDestination(label=label, icon=icon)
        self.tabs.append((tab_obj, destination))
        return tab_obj
