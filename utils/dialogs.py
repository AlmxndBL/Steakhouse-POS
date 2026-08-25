import flet as ft

def open_dialog(page: ft.Page, dialog: ft.AlertDialog):
    """
    Standardized dialog opening across all Flet versions (including Flet 0.86+).
    Safely opens dialog on the page dialog stack.
    """
    if not page:
        return
    try:
        if hasattr(page, "show_dialog"):
            page.show_dialog(dialog)
        elif hasattr(page, "open"):
            page.open(dialog)
        else:
            page.overlay.append(dialog)
            dialog.open = True
            page.update()
    except Exception:
        try:
            page.overlay.append(dialog)
            dialog.open = True
            page.update()
        except Exception:
            pass

def close_dialog(page: ft.Page, dialog: ft.AlertDialog = None):
    """
    Standardized dialog closing across all Flet versions (including Flet 0.86+).
    Safely pops dialog from the page dialog stack.
    """
    if not page:
        return
    try:
        if hasattr(page, "pop_dialog"):
            page.pop_dialog()
        elif hasattr(page, "close") and dialog is not None:
            page.close(dialog)
        elif dialog is not None:
            dialog.open = False
            page.update()
    except Exception:
        if dialog is not None:
            dialog.open = False
            try:
                page.update()
            except Exception:
                pass
