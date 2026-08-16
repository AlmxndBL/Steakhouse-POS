import flet as ft
from database.seed import seed_data
from views.login_view import LoginView
from views.table_map_view import TableMapView
from views.pos_main_view import PosMainView
from views.stock_view import StockView
from views.reports_view import ReportsView
from utils.navigation import navigate_to

def main(page: ft.Page):
    # Initialize Database & Seed default data
    seed_data()

    page.title = "Steakhouse POS - ระบบจัดการร้านสเต๊กและคลังวัตถุดิบ"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.spacing = 0

    def route_change(e):
        page.views.clear()
        
        route = page.route
        user_id = page.session.store.get("user_id")
        user_role = page.session.store.get("user_role")

        # Require login for protected routes
        if not user_id and route != "/login":
            route = "/login"
            page.route = "/login"

        # RBAC Check
        if route in ["/stock", "/reports"]:
            if user_role not in ["OWNER", "MANAGER"]:
                # Redirect unauthorized users back to tables
                route = "/tables"
                page.route = "/tables"

        if route == "/login":
            page.views.append(LoginView(page))
        elif route == "/tables":
            page.views.append(TableMapView(page))
        elif route == "/pos":
            page.views.append(PosMainView(page))
        elif route == "/kds":
            from views.kds_view import KdsView
            page.views.append(KdsView(page))
        elif route == "/stock":
            page.views.append(StockView(page))
        elif route == "/reports":
            page.views.append(ReportsView(page))
        else:
            page.views.append(LoginView(page))

        try:
            page.update()
        except Exception:
            pass

    def view_pop(e):
        if len(page.views) > 1:
            page.views.pop()
            top_view = page.views[-1]
            navigate_to(page, top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop

    # Initial route navigation
    navigate_to(page, "/login")

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    if os.environ.get("DOCKER_ENV"):
        # Web server mode for Docker
        ft.run(main, view=ft.AppView.WEB_BROWSER, port=port, host="0.0.0.0")
    else:
        # Desktop app mode
        ft.run(main, view=ft.AppView.FLET_APP, port=port)
