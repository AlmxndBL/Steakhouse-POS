import flet as ft
from database.seed import seed_data
from views.login_view import LoginView
from views.admin_dashboard_view import AdminDashboardView
from views.staff_view import StaffView
from views.admin_menu_view import AdminMenuView
from views.admin_table_view import AdminTableView
from views.table_map_view import TableMapView
from views.pos_main_view import PosMainView
from views.stock_view import StockView
from views.reports_view import ReportsView
from views.kds_view import KdsView
from views.audit_log_view import AuditLogView
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

        # RBAC Check for Admin / Back-office Routes
        admin_routes = [
            "/admin", "/admin/staff", "/admin/menus", "/admin/tables",
            "/admin/stock", "/admin/reports", "/admin/audit", "/stock", "/reports", "/settings"
        ]
        if route in admin_routes:
            if user_role not in ["OWNER", "MANAGER"]:
                # Redirect unauthorized users back to tables
                route = "/tables"
                page.route = "/tables"

        if route == "/login":
            page.views.append(LoginView(page))
        elif route == "/admin":
            page.views.append(AdminDashboardView(page))
        elif route == "/admin/staff":
            page.views.append(StaffView(page))
        elif route == "/admin/menus" or route == "/settings":
            page.views.append(AdminMenuView(page))
        elif route == "/admin/tables":
            page.views.append(AdminTableView(page))
        elif route == "/admin/stock" or route == "/stock":
            page.views.append(StockView(page))
        elif route == "/admin/reports" or route == "/reports":
            page.views.append(ReportsView(page))
        elif route == "/admin/audit":
            page.views.append(AuditLogView(page))
        elif route == "/tables":
            page.views.append(TableMapView(page))
        elif route == "/pos":
            page.views.append(PosMainView(page))
        elif route == "/kds":
            page.views.append(KdsView(page))
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
    exports_path = os.path.join(os.getcwd(), "exports")
    os.makedirs(exports_path, exist_ok=True)
    if os.environ.get("DOCKER_ENV"):
        # Web server mode for Docker with exports asset directory for instant file downloads
        ft.run(main, view=ft.AppView.WEB_BROWSER, port=port, host="0.0.0.0", assets_dir=exports_path)
    else:
        # Desktop app mode
        ft.run(main, view=ft.AppView.FLET_APP, port=port, assets_dir=exports_path)
