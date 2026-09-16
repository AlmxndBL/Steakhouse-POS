import flet as ft
import logging

def navigate_to(page: ft.Page, route_path: str):
    """
    Synchronously updates page.route and triggers on_route_change handler.
    Prevents RuntimeWarning: coroutine 'Page.push_route' was never awaited.
    """
    page.route = route_path
    if page.on_route_change:
        page.on_route_change(None)
    try:
        page.update()
    except RuntimeError as err:
        logging.debug("Navigation page update skipped: %s", err)
