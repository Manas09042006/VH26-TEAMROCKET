import json
from datetime import datetime

import customtkinter as ctk
import httpx

from admin.websocket_client import AdminWebSocketClient


# ============================================================
# THEME
# ============================================================

BG_COLOR = "#080B12"
SIDEBAR_COLOR = "#0D111A"
CARD_COLOR = "#121824"
CARD_HOVER = "#182131"

ACCENT = "#00C2FF"
ACCENT_DARK = "#087EA4"

TEXT_PRIMARY = "#F4F7FB"
TEXT_SECONDARY = "#8D99AA"
TEXT_MUTED = "#5F6B7A"

SUCCESS = "#27D17F"
WARNING = "#FFB020"
DANGER = "#FF4D67"
PURPLE = "#9B7CFF"

BORDER = "#202938"


# ============================================================
# DASHBOARD WINDOW
# ============================================================

class DashboardWindow:

    def __init__(self, parent, username):

        self.parent = parent
        self.username = username

        # Backend
        self.backend_url = "http://127.0.0.1:8000"

        # Current page
        self.current_page = "Dashboard"

        # Local data
        self.employee_status = {}
        self.activity_events = []
        self.security_events = []

        # UI containers
        self.pages = {}
        self.nav_buttons = {}

        # ----------------------------------------------------
        # WINDOW
        # ----------------------------------------------------

        self.parent.title(
            "LeakGuard | Security Administration"
        )

        self.parent.geometry(
            "1280x760"
        )

        self.parent.minsize(
            900,
            600
        )

        self.parent.configure(
            fg_color=BG_COLOR
        )

        self.parent.protocol(
            "WM_DELETE_WINDOW",
            self.close_dashboard
        )

        # ----------------------------------------------------
        # ROOT GRID
        # ----------------------------------------------------

        self.parent.grid_rowconfigure(
            0,
            weight=1
        )

        self.parent.grid_columnconfigure(
            0,
            weight=0
        )

        self.parent.grid_columnconfigure(
            1,
            weight=1
        )

        # ----------------------------------------------------
        # SIDEBAR
        # ----------------------------------------------------

        self.create_sidebar()

        # ----------------------------------------------------
        # MAIN CONTAINER
        # ----------------------------------------------------

        self.main_container = ctk.CTkFrame(
            self.parent,
            fg_color=BG_COLOR,
            corner_radius=0
        )

        self.main_container.grid(
            row=0,
            column=1,
            sticky="nsew"
        )

        self.main_container.grid_rowconfigure(
            1,
            weight=1
        )

        self.main_container.grid_columnconfigure(
            0,
            weight=1
        )

        # ----------------------------------------------------
        # TOPBAR
        # ----------------------------------------------------

        self.create_topbar()

        # ----------------------------------------------------
        # CONTENT CONTAINER
        # ----------------------------------------------------

        self.content_container = ctk.CTkFrame(
            self.main_container,
            fg_color=BG_COLOR,
            corner_radius=0
        )

        self.content_container.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=20,
            pady=(0, 20)
        )

        self.content_container.grid_rowconfigure(
            0,
            weight=1
        )

        self.content_container.grid_columnconfigure(
            0,
            weight=1
        )

        # ----------------------------------------------------
        # CREATE ALL PAGES
        # ----------------------------------------------------

        self.create_dashboard_page()
        self.create_employees_page()
        self.create_logs_page()
        self.create_security_page()
        self.create_reports_page()
        self.create_settings_page()

        # ----------------------------------------------------
        # SHOW DASHBOARD
        # ----------------------------------------------------

        self.show_page(
            "Dashboard"
        )

        # ----------------------------------------------------
        # WEBSOCKET
        # ----------------------------------------------------

        self.websocket_client = AdminWebSocketClient(
            self.handle_websocket_message
        )

        self.websocket_client.start()

        # ----------------------------------------------------
        # LOAD EXISTING BACKEND DATA
        # ----------------------------------------------------

        self.load_employees()
        self.load_logs()

        # ----------------------------------------------------
        # PERIODIC BACKEND REFRESH
        # ----------------------------------------------------

        self.refresh_backend_data()

        # ----------------------------------------------------
        # CLOCK
        # ----------------------------------------------------

        self.update_clock()

    # ========================================================
    # SIDEBAR
    # ========================================================

    def create_sidebar(self):

        self.sidebar = ctk.CTkFrame(
            self.parent,
            width=230,
            fg_color=SIDEBAR_COLOR,
            corner_radius=0
        )

        self.sidebar.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        self.sidebar.grid_propagate(
            False
        )

        # ----------------------------------------------------
        # LOGO
        # ----------------------------------------------------

        logo_frame = ctk.CTkFrame(
            self.sidebar,
            fg_color="transparent"
        )

        logo_frame.pack(
            fill="x",
            padx=20,
            pady=(25, 30)
        )

        ctk.CTkLabel(
            logo_frame,
            text="LEAKGUARD",
            font=ctk.CTkFont(
                size=22,
                weight="bold"
            ),
            text_color=TEXT_PRIMARY
        ).pack(
            anchor="w"
        )

        ctk.CTkLabel(
            logo_frame,
            text="SECURITY ADMINISTRATION",
            font=ctk.CTkFont(
                size=9,
                weight="bold"
            ),
            text_color=ACCENT
        ).pack(
            anchor="w",
            pady=(3, 0)
        )

        # ----------------------------------------------------
        # NAVIGATION
        # ----------------------------------------------------

        nav_items = [
            ("Dashboard", "⌂"),
            ("Employees", "◉"),
            ("Activity Logs", "≡"),
            ("Security Events", "⚠"),
            ("Reports", "▤"),
            ("Settings", "⚙"),
        ]

        for name, icon in nav_items:

            button = ctk.CTkButton(
                self.sidebar,
                text=f"  {icon}    {name}",
                height=45,
                anchor="w",
                corner_radius=8,
                fg_color="transparent",
                hover_color=CARD_HOVER,
                text_color=TEXT_SECONDARY,
                font=ctk.CTkFont(
                    size=13,
                    weight="bold"
                ),
                command=lambda n=name: self.show_page(n)
            )

            button.pack(
                fill="x",
                padx=12,
                pady=3
            )

            self.nav_buttons[name] = button

        # ----------------------------------------------------
        # SYSTEM STATUS
        # ----------------------------------------------------

        status_frame = ctk.CTkFrame(
            self.sidebar,
            fg_color=CARD_COLOR,
            corner_radius=10
        )

        status_frame.pack(
            side="bottom",
            fill="x",
            padx=15,
            pady=18
        )

        ctk.CTkLabel(
            status_frame,
            text="SYSTEM STATUS",
            font=ctk.CTkFont(
                size=9,
                weight="bold"
            ),
            text_color=TEXT_MUTED
        ).pack(
            anchor="w",
            padx=12,
            pady=(10, 2)
        )

        status_row = ctk.CTkFrame(
            status_frame,
            fg_color="transparent"
        )

        status_row.pack(
            fill="x",
            padx=12,
            pady=(0, 10)
        )

        self.system_dot = ctk.CTkLabel(
            status_row,
            text="●",
            font=ctk.CTkFont(
                size=13
            ),
            text_color=SUCCESS
        )

        self.system_dot.pack(
            side="left"
        )

        self.system_status = ctk.CTkLabel(
            status_row,
            text="Backend Connected",
            font=ctk.CTkFont(
                size=11
            ),
            text_color=TEXT_PRIMARY
        )

        self.system_status.pack(
            side="left",
            padx=6
        )

    # ========================================================
    # TOPBAR
    # ========================================================

    def create_topbar(self):

        topbar = ctk.CTkFrame(
            self.main_container,
            height=70,
            fg_color=BG_COLOR,
            corner_radius=0
        )

        topbar.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=20
        )

        topbar.grid_columnconfigure(
            0,
            weight=1
        )

        self.page_title = ctk.CTkLabel(
            topbar,
            text="Dashboard",
            font=ctk.CTkFont(
                size=24,
                weight="bold"
            ),
            text_color=TEXT_PRIMARY
        )

        self.page_title.grid(
            row=0,
            column=0,
            sticky="w",
            pady=20
        )

        right = ctk.CTkFrame(
            topbar,
            fg_color="transparent"
        )

        right.grid(
            row=0,
            column=1,
            sticky="e"
        )

        self.live_label = ctk.CTkLabel(
            right,
            text="● LIVE",
            font=ctk.CTkFont(
                size=11,
                weight="bold"
            ),
            text_color=SUCCESS
        )

        self.live_label.pack(
            side="left",
            padx=20
        )

        self.clock_label = ctk.CTkLabel(
            right,
            text="",
            font=ctk.CTkFont(
                size=11
            ),
            text_color=TEXT_SECONDARY
        )

        self.clock_label.pack(
            side="left"
        )

        ctk.CTkLabel(
            right,
            text=f"  {self.username}",
            font=ctk.CTkFont(
                size=11,
                weight="bold"
            ),
            text_color=TEXT_PRIMARY
        ).pack(
            side="left",
            padx=(20, 0)
        )

    # ========================================================
    # PAGE CREATOR
    # ========================================================

    def create_page(self):

        page = ctk.CTkFrame(
            self.content_container,
            fg_color=BG_COLOR,
            corner_radius=0
        )

        page.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        page.grid_rowconfigure(
            0,
            weight=1
        )

        page.grid_columnconfigure(
            0,
            weight=1
        )

        return page

    # ========================================================
    # DASHBOARD PAGE
    # ========================================================

    def create_dashboard_page(self):

        page = self.create_page()

        self.pages["Dashboard"] = page

        page.grid_columnconfigure(
            (0, 1, 2, 3),
            weight=1
        )

        page.grid_rowconfigure(
            2,
            weight=1
        )

        # ----------------------------------------------------
        # WELCOME
        # ----------------------------------------------------

        welcome = ctk.CTkFrame(
            page,
            fg_color=CARD_COLOR,
            corner_radius=12
        )

        welcome.grid(
            row=0,
            column=0,
            columnspan=4,
            sticky="ew",
            pady=(0, 15)
        )

        ctk.CTkLabel(
            welcome,
            text=f"Welcome back, {self.username}",
            font=ctk.CTkFont(
                size=21,
                weight="bold"
            ),
            text_color=TEXT_PRIMARY
        ).pack(
            anchor="w",
            padx=20,
            pady=(18, 2)
        )

        ctk.CTkLabel(
            welcome,
            text=(
                "Monitor employee agents and LeakGuard security activity."
            ),
            font=ctk.CTkFont(
                size=11
            ),
            text_color=TEXT_SECONDARY
        ).pack(
            anchor="w",
            padx=20,
            pady=(0, 18)
        )

        # ----------------------------------------------------
        # STAT CARDS
        # ----------------------------------------------------

        self.total_employees_value = self.create_stat_card(
            page,
            1,
            0,
            "TOTAL EMPLOYEES",
            "0",
            ACCENT
        )

        self.online_value = self.create_stat_card(
            page,
            1,
            1,
            "ONLINE",
            "0",
            SUCCESS
        )

        self.offline_value = self.create_stat_card(
            page,
            1,
            2,
            "OFFLINE",
            "0",
            WARNING
        )

        self.security_value = self.create_stat_card(
            page,
            1,
            3,
            "SECURITY EVENTS",
            "0",
            DANGER
        )

        # ----------------------------------------------------
        # RECENT ACTIVITY
        # ----------------------------------------------------

        activity_card = ctk.CTkFrame(
            page,
            fg_color=CARD_COLOR,
            corner_radius=12
        )

        activity_card.grid(
            row=2,
            column=0,
            columnspan=2,
            sticky="nsew",
            padx=(0, 8),
            pady=(15, 0)
        )

        ctk.CTkLabel(
            activity_card,
            text="RECENT ACTIVITY",
            font=ctk.CTkFont(
                size=12,
                weight="bold"
            ),
            text_color=TEXT_PRIMARY
        ).pack(
            anchor="w",
            padx=18,
            pady=(15, 10)
        )

        self.dashboard_activity = ctk.CTkTextbox(
            activity_card,
            fg_color="transparent",
            text_color=TEXT_SECONDARY,
            font=ctk.CTkFont(
                size=11
            ),
            border_width=0
        )

        self.dashboard_activity.pack(
            fill="both",
            expand=True,
            padx=12,
            pady=(0, 12)
        )

        self.dashboard_activity.configure(
            state="disabled"
        )

        # ----------------------------------------------------
        # SECURITY MONITOR
        # ----------------------------------------------------

        security_card = ctk.CTkFrame(
            page,
            fg_color=CARD_COLOR,
            corner_radius=12
        )

        security_card.grid(
            row=2,
            column=2,
            columnspan=2,
            sticky="nsew",
            padx=(8, 0),
            pady=(15, 0)
        )

        ctk.CTkLabel(
            security_card,
            text="SECURITY MONITOR",
            font=ctk.CTkFont(
                size=12,
                weight="bold"
            ),
            text_color=TEXT_PRIMARY
        ).pack(
            anchor="w",
            padx=18,
            pady=(15, 10)
        )

        self.dashboard_security = ctk.CTkTextbox(
            security_card,
            fg_color="transparent",
            text_color=TEXT_SECONDARY,
            font=ctk.CTkFont(
                size=11
            ),
            border_width=0
        )

        self.dashboard_security.pack(
            fill="both",
            expand=True,
            padx=12,
            pady=(0, 12)
        )

        self.dashboard_security.configure(
            state="disabled"
        )

    # ========================================================
    # STAT CARD
    # ========================================================

    def create_stat_card(
        self,
        parent,
        row,
        column,
        title,
        value,
        accent
    ):

        card = ctk.CTkFrame(
            parent,
            fg_color=CARD_COLOR,
            corner_radius=12
        )

        card.grid(
            row=row,
            column=column,
            sticky="ew",
            padx=5
        )

        ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(
                size=9,
                weight="bold"
            ),
            text_color=TEXT_MUTED
        ).pack(
            anchor="w",
            padx=15,
            pady=(14, 3)
        )

        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=ctk.CTkFont(
                size=25,
                weight="bold"
            ),
            text_color=accent
        )

        value_label.pack(
            anchor="w",
            padx=15,
            pady=(0, 14)
        )

        return value_label

    # ========================================================
    # EMPLOYEES PAGE
    # ========================================================

    def create_employees_page(self):

        page = self.create_page()

        self.pages["Employees"] = page

        page.grid_columnconfigure(
            0,
            weight=1
        )

        page.grid_rowconfigure(
            1,
            weight=1
        )

        # ----------------------------------------------------
        # HEADER
        # ----------------------------------------------------

        header = ctk.CTkFrame(
            page,
            fg_color=CARD_COLOR,
            corner_radius=12
        )

        header.grid(
            row=0,
            column=0,
            sticky="ew",
            pady=(0, 15)
        )

        ctk.CTkLabel(
            header,
            text="Employee Monitoring",
            font=ctk.CTkFont(
                size=18,
                weight="bold"
            ),
            text_color=TEXT_PRIMARY
        ).pack(
            anchor="w",
            padx=20,
            pady=(16, 2)
        )

        ctk.CTkLabel(
            header,
            text=(
                "Live status of registered LeakGuard agents."
            ),
            font=ctk.CTkFont(
                size=11
            ),
            text_color=TEXT_SECONDARY
        ).pack(
            anchor="w",
            padx=20,
            pady=(0, 16)
        )

        # ----------------------------------------------------
        # TABLE CARD
        # ----------------------------------------------------

        table = ctk.CTkFrame(
            page,
            fg_color=CARD_COLOR,
            corner_radius=12
        )

        table.grid(
            row=1,
            column=0,
            sticky="nsew"
        )

        for column, weight in enumerate(
            [2, 2, 2, 1, 1, 1]
        ):

            table.grid_columnconfigure(
                column,
                weight=weight
            )

        self.employee_table = ctk.CTkFrame(
            table,
            fg_color="transparent"
        )

        self.employee_table.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=15
        )

        self.refresh_employee_view()

    # ========================================================
    # ACTIVITY LOG PAGE
    # ========================================================

    def create_logs_page(self):

        page = self.create_page()

        self.pages["Activity Logs"] = page

        page.grid_columnconfigure(
            0,
            weight=1
        )

        page.grid_rowconfigure(
            1,
            weight=1
        )

        ctk.CTkLabel(
            page,
            text="Activity Logs",
            font=ctk.CTkFont(
                size=20,
                weight="bold"
            ),
            text_color=TEXT_PRIMARY
        ).grid(
            row=0,
            column=0,
            sticky="w",
            pady=(0, 12)
        )

        card = ctk.CTkFrame(
            page,
            fg_color=CARD_COLOR,
            corner_radius=12
        )

        card.grid(
            row=1,
            column=0,
            sticky="nsew"
        )

        self.logs_text = ctk.CTkTextbox(
            card,
            fg_color="transparent",
            text_color=TEXT_SECONDARY,
            font=ctk.CTkFont(
                size=11
            ),
            border_width=0
        )

        self.logs_text.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=15
        )

        self.logs_text.configure(
            state="disabled"
        )

    # ========================================================
    # SECURITY EVENTS PAGE
    # ========================================================

    def create_security_page(self):

        page = self.create_page()

        self.pages["Security Events"] = page

        page.grid_columnconfigure(
            0,
            weight=1
        )

        page.grid_rowconfigure(
            1,
            weight=1
        )

        ctk.CTkLabel(
            page,
            text="Security Events",
            font=ctk.CTkFont(
                size=20,
                weight="bold"
            ),
            text_color=TEXT_PRIMARY
        ).grid(
            row=0,
            column=0,
            sticky="w",
            pady=(0, 12)
        )

        card = ctk.CTkFrame(
            page,
            fg_color=CARD_COLOR,
            corner_radius=12
        )

        card.grid(
            row=1,
            column=0,
            sticky="nsew"
        )

        self.security_text = ctk.CTkTextbox(
            card,
            fg_color="transparent",
            text_color=TEXT_SECONDARY,
            font=ctk.CTkFont(
                size=11
            ),
            border_width=0
        )

        self.security_text.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=15
        )

        self.security_text.configure(
            state="disabled"
        )

    # ========================================================
    # REPORTS PAGE
    # ========================================================

    def create_reports_page(self):

        page = self.create_page()

        self.pages["Reports"] = page

        page.grid_columnconfigure(
            (0, 1, 2),
            weight=1
        )

        page.grid_rowconfigure(
            2,
            weight=1
        )

        ctk.CTkLabel(
            page,
            text="Security Reports",
            font=ctk.CTkFont(
                size=20,
                weight="bold"
            ),
            text_color=TEXT_PRIMARY
        ).grid(
            row=0,
            column=0,
            columnspan=3,
            sticky="w",
            pady=(0, 15)
        )

        self.report_total = self.create_report_card(
            page,
            1,
            0,
            "TOTAL EVENTS",
            "0"
        )

        self.report_security = self.create_report_card(
            page,
            1,
            1,
            "SECURITY EVENTS",
            "0"
        )

        self.report_activity = self.create_report_card(
            page,
            1,
            2,
            "ACTIVITY EVENTS",
            "0"
        )

        report_card = ctk.CTkFrame(
            page,
            fg_color=CARD_COLOR,
            corner_radius=12
        )

        report_card.grid(
            row=2,
            column=0,
            columnspan=3,
            sticky="nsew",
            pady=(15, 0)
        )

        ctk.CTkLabel(
            report_card,
            text="Report Center",
            font=ctk.CTkFont(
                size=15,
                weight="bold"
            ),
            text_color=TEXT_PRIMARY
        ).pack(
            anchor="w",
            padx=20,
            pady=(20, 5)
        )

        ctk.CTkLabel(
            report_card,
            text=(
                "Generate a summary of employee activity "
                "and LeakGuard security events."
            ),
            font=ctk.CTkFont(
                size=11
            ),
            text_color=TEXT_SECONDARY
        ).pack(
            anchor="w",
            padx=20
        )

        ctk.CTkButton(
            report_card,
            text="Generate Report",
            width=160,
            height=40,
            corner_radius=8,
            fg_color=ACCENT_DARK,
            hover_color=ACCENT,
            text_color=TEXT_PRIMARY,
            command=self.generate_report
        ).pack(
            anchor="w",
            padx=20,
            pady=20
        )

    # ========================================================
    # REPORT CARD
    # ========================================================

    def create_report_card(
        self,
        parent,
        row,
        column,
        title,
        value
    ):

        card = ctk.CTkFrame(
            parent,
            fg_color=CARD_COLOR,
            corner_radius=12
        )

        card.grid(
            row=row,
            column=column,
            sticky="ew",
            padx=5
        )

        ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(
                size=9,
                weight="bold"
            ),
            text_color=TEXT_MUTED
        ).pack(
            anchor="w",
            padx=15,
            pady=(14, 2)
        )

        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=ctk.CTkFont(
                size=25,
                weight="bold"
            ),
            text_color=PURPLE
        )

        value_label.pack(
            anchor="w",
            padx=15,
            pady=(0, 14)
        )

        return value_label

    # ========================================================
    # SETTINGS PAGE
    # ========================================================

    def create_settings_page(self):

        page = self.create_page()

        self.pages["Settings"] = page

        ctk.CTkLabel(
            page,
            text="System Settings",
            font=ctk.CTkFont(
                size=20,
                weight="bold"
            ),
            text_color=TEXT_PRIMARY
        ).pack(
            anchor="w",
            pady=(0, 15)
        )

        card = ctk.CTkFrame(
            page,
            fg_color=CARD_COLOR,
            corner_radius=12
        )

        card.pack(
            fill="x"
        )

        self.add_setting(
            card,
            "Backend Server",
            self.backend_url
        )

        self.add_setting(
            card,
            "WebSocket",
            "ws://127.0.0.1:8000/ws/admin"
        )

        self.add_setting(
            card,
            "Admin User",
            self.username
        )

        self.add_setting(
            card,
            "Connection",
            "Live WebSocket monitoring enabled"
        )

    # ========================================================
    # SETTING ROW
    # ========================================================

    def add_setting(
        self,
        parent,
        title,
        value
    ):

        row = ctk.CTkFrame(
            parent,
            fg_color="transparent"
        )

        row.pack(
            fill="x",
            padx=20,
            pady=12
        )

        ctk.CTkLabel(
            row,
            text=title,
            font=ctk.CTkFont(
                size=11,
                weight="bold"
            ),
            text_color=TEXT_PRIMARY
        ).pack(
            anchor="w"
        )

        ctk.CTkLabel(
            row,
            text=value,
            font=ctk.CTkFont(
                size=11
            ),
            text_color=TEXT_SECONDARY
        ).pack(
            anchor="w",
            pady=(3, 0)
        )

    # ========================================================
    # PAGE NAVIGATION
    # ========================================================

    def show_page(
        self,
        page_name
    ):

        if page_name not in self.pages:
            return

        self.current_page = page_name

        # Hide all pages

        for page in self.pages.values():

            page.grid_remove()

        # Show selected page

        selected_page = self.pages[page_name]

        selected_page.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        selected_page.tkraise()

        # Update title

        self.page_title.configure(
            text=page_name
        )

        # Update navigation

        for name, button in self.nav_buttons.items():

            if name == page_name:

                button.configure(
                    fg_color=ACCENT_DARK,
                    text_color=TEXT_PRIMARY
                )

            else:

                button.configure(
                    fg_color="transparent",
                    text_color=TEXT_SECONDARY
                )

        # Page refresh

        if page_name == "Employees":
            self.refresh_employee_view()

        elif page_name == "Activity Logs":
            self.update_logs_view()

        elif page_name == "Security Events":
            self.update_security_view()

        elif page_name == "Reports":
            self.update_reports()

    # ========================================================
    # BACKEND - LOAD EMPLOYEES
    # ========================================================

    def load_employees(self):

        try:

            response = httpx.get(
                f"{self.backend_url}/employees/",
                timeout=5
            )

            response.raise_for_status()

            data = response.json()

            if isinstance(data, dict):

                employees = data.get(
                    "employees",
                    []
                )

            else:

                employees = data

            self.employee_status.clear()

            for employee in employees:

                employee_id = employee.get(
                    "id"
                )

                if employee_id is None:
                    continue

                self.employee_status[
                    employee_id
                ] = {

                    "username": employee.get(
                        "username",
                        "Unknown"
                    ),

                    "display_name": employee.get(
                        "display_name",
                        employee.get(
                            "username",
                            "Unknown"
                        )
                    ),

                    "role": employee.get(
                        "role",
                        "EMPLOYEE"
                    ),

                    "agent_id": employee.get(
                        "agent_id",
                        "Unknown"
                    ),

                    "machine_name": employee.get(
                        "machine_name",
                        "Unknown"
                    ),

                    "status": employee.get(
                        "status",
                        "OFFLINE"
                    ),

                    "last_seen": self.format_last_seen(
                        employee.get(
                            "last_seen"
                        )
                    )
                }

            self.refresh_employee_view()
            self.update_dashboard_statistics()

            self.system_status.configure(
                text="Backend Connected"
            )

            self.system_dot.configure(
                text_color=SUCCESS
            )

        except Exception as error:

            print(
                f"[ADMIN API] Could not load employees: {error}"
            )

            self.system_status.configure(
                text="Backend Disconnected"
            )

            self.system_dot.configure(
                text_color=DANGER
            )

    # ========================================================
    # BACKEND - LOAD LOGS
    # ========================================================

    def load_logs(self):

        try:

            response = httpx.get(
                f"{self.backend_url}/admin/logs",
                timeout=5
            )

            response.raise_for_status()

            data = response.json()

            if isinstance(data, dict):

                logs = data.get(
                    "logs",
                    data.get(
                        "activity_logs",
                        []
                    )
                )

            else:

                logs = data

            self.activity_events.clear()

            for log in logs:

                timestamp = log.get(
                    "timestamp",
                    ""
                )

                description = log.get(
                    "description",
                    log.get(
                        "event_type",
                        "Activity event"
                    )
                )

                employee_id = log.get(
                    "employee_id",
                    "Unknown"
                )

                entry = (
                    f"{self.format_last_seen(timestamp)}  "
                    f"[Employee {employee_id}]  "
                    f"{description}"
                )

                self.activity_events.append(
                    entry
                )

            self.activity_events = (
                self.activity_events[-100:]
            )

            self.update_logs_view()
            self.update_dashboard_activity()
            self.update_reports()

        except Exception as error:

            print(
                f"[ADMIN API] Could not load logs: {error}"
            )

    # ========================================================
    # BACKEND - PERIODIC REFRESH
    # ========================================================

    def refresh_backend_data(self):

        if not self.parent.winfo_exists():
            return

        self.load_employees()
        self.load_logs()

        self.parent.after(
            5000,
            self.refresh_backend_data
        )

    # ========================================================
    # DATE FORMATTER
    # ========================================================

    def format_last_seen(
        self,
        value
    ):

        if not value:
            return "Never"

        try:

            if isinstance(
                value,
                str
            ):

                parsed = datetime.fromisoformat(
                    value.replace(
                        "Z",
                        "+00:00"
                    )
                )

                return parsed.strftime(
                    "%H:%M:%S"
                )

        except Exception:
            pass

        return str(value)

    # ========================================================
    # WEBSOCKET MESSAGE
    # ========================================================

    def handle_websocket_message(
        self,
        message
    ):

        try:

            data = json.loads(
                message
            )

            event_type = data.get(
                "type"
            )

            # ------------------------------------------------
            # EMPLOYEE STATUS
            # ------------------------------------------------

            if event_type == "EMPLOYEE_STATUS":

                self.parent.after(
                    0,
                    lambda d=data:
                    self.handle_employee_status(d)
                )

            # ------------------------------------------------
            # SECURITY EVENT
            # ------------------------------------------------

            elif event_type == "SECURITY_EVENT":

                self.parent.after(
                    0,
                    lambda d=data:
                    self.handle_security_event(d)
                )

            # ------------------------------------------------
            # ACTIVITY EVENT
            # ------------------------------------------------

            elif event_type == "ACTIVITY_EVENT":

                self.parent.after(
                    0,
                    lambda d=data:
                    self.handle_activity_event(d)
                )

        except json.JSONDecodeError:

            print(
                "[ADMIN WS] Invalid JSON received"
            )

        except Exception as error:

            print(
                f"[ADMIN WS] Message handling error: {error}"
            )

    # ========================================================
    # EMPLOYEE STATUS EVENT
    # ========================================================

    def handle_employee_status(
        self,
        data
    ):

        employee_id = data.get(
            "employee_id"
        )

        if employee_id is None:
            return

        self.employee_status[
            employee_id
        ] = {

            "username": data.get(
                "username",
                "Unknown"
            ),

            "display_name": data.get(
                "display_name",
                data.get(
                    "username",
                    "Unknown"
                )
            ),

            "role": data.get(
                "role",
                "EMPLOYEE"
            ),

            "agent_id": data.get(
                "agent_id",
                "Unknown"
            ),

            "machine_name": data.get(
                "machine_name",
                "Unknown"
            ),

            "status": data.get(
                "status",
                "UNKNOWN"
            ),

            "last_seen": datetime.now().strftime(
                "%H:%M:%S"
            )
        }

        machine = data.get(
            "machine_name",
            "Unknown machine"
        )

        status = data.get(
            "status",
            "UNKNOWN"
        )

        self.add_activity(
            f"{machine} changed status to {status}"
        )

        self.refresh_employee_view()
        self.update_dashboard_statistics()

    # ========================================================
    # SECURITY EVENT
    # ========================================================

    def handle_security_event(
        self,
        data
    ):

        description = data.get(
            "description",
            "Security event received"
        )

        severity = data.get(
            "severity",
            "INFO"
        )

        event = {

            "description": description,

            "severity": severity,

            "time": datetime.now().strftime(
                "%H:%M:%S"
            )
        }

        self.security_events.append(
            event
        )

        self.security_events = (
            self.security_events[-100:]
        )

        self.add_security_event(
            f"[{severity}] {description}"
        )

        self.update_dashboard_statistics()

    # ========================================================
    # ACTIVITY EVENT
    # ========================================================

    def handle_activity_event(
        self,
        data
    ):

        description = data.get(
            "description",
            "Activity event received"
        )

        self.add_activity(
            description
        )

    # ========================================================
    # EMPLOYEE TABLE
    # ========================================================

    def refresh_employee_view(self):

        if not hasattr(
            self,
            "employee_table"
        ):
            return

        for widget in self.employee_table.winfo_children():

            widget.destroy()

        # ----------------------------------------------------
        # HEADERS
        # ----------------------------------------------------

        headers = [
            "EMPLOYEE",
            "MACHINE",
            "AGENT ID",
            "ROLE",
            "STATUS",
            "LAST SEEN"
        ]

        for column, header in enumerate(headers):

            ctk.CTkLabel(
                self.employee_table,
                text=header,
                font=ctk.CTkFont(
                    size=10,
                    weight="bold"
                ),
                text_color=TEXT_MUTED
            ).grid(
                row=0,
                column=column,
                sticky="w",
                padx=10,
                pady=(5, 12)
            )

        # ----------------------------------------------------
        # NO EMPLOYEES
        # ----------------------------------------------------

        if not self.employee_status:

            ctk.CTkLabel(
                self.employee_table,
                text="No registered employee agents found.",
                font=ctk.CTkFont(
                    size=12
                ),
                text_color=TEXT_SECONDARY
            ).grid(
                row=1,
                column=0,
                columnspan=6,
                pady=40
            )

            return

        # ----------------------------------------------------
        # EMPLOYEE ROWS
        # ----------------------------------------------------

        for row, employee in enumerate(
            self.employee_status.values(),
            start=1
        ):

            employee_name = employee.get(
                "display_name",
                employee.get(
                    "username",
                    "Unknown"
                )
            )

            machine = employee.get(
                "machine_name",
                "Unknown"
            )

            agent = employee.get(
                "agent_id",
                "Unknown"
            )

            role = employee.get(
                "role",
                "EMPLOYEE"
            )

            status = employee.get(
                "status",
                "OFFLINE"
            )

            last_seen = employee.get(
                "last_seen",
                "-"
            )

            # Status color

            if status == "ONLINE":

                status_color = SUCCESS

            elif status == "OFFLINE":

                status_color = DANGER

            else:

                status_color = WARNING

            values = [
                employee_name,
                machine,
                agent,
                role,
                status,
                last_seen
            ]

            for column, value in enumerate(values):

                if column == 4:

                    text_color = status_color
                    font_weight = "bold"

                else:

                    text_color = TEXT_SECONDARY
                    font_weight = "normal"

                ctk.CTkLabel(
                    self.employee_table,
                    text=str(value),
                    font=ctk.CTkFont(
                        size=11,
                        weight=font_weight
                    ),
                    text_color=text_color
                ).grid(
                    row=row,
                    column=column,
                    sticky="w",
                    padx=10,
                    pady=10
                )

    # ========================================================
    # DASHBOARD STATISTICS
    # ========================================================

    def update_dashboard_statistics(self):

        total = len(
            self.employee_status
        )

        online = sum(
            1
            for employee in self.employee_status.values()
            if employee.get(
                "status"
            ) == "ONLINE"
        )

        offline = sum(
            1
            for employee in self.employee_status.values()
            if employee.get(
                "status"
            ) == "OFFLINE"
        )

        security = len(
            self.security_events
        )

        if hasattr(
            self,
            "total_employees_value"
        ):

            self.total_employees_value.configure(
                text=str(total)
            )

            self.online_value.configure(
                text=str(online)
            )

            self.offline_value.configure(
                text=str(offline)
            )

            self.security_value.configure(
                text=str(security)
            )

    # ========================================================
    # ACTIVITY
    # ========================================================

    def add_activity(
        self,
        message
    ):

        timestamp = datetime.now().strftime(
            "%H:%M:%S"
        )

        entry = (
            f"{timestamp}  {message}"
        )

        self.activity_events.append(
            entry
        )

        self.activity_events = (
            self.activity_events[-100:]
        )

        self.update_dashboard_activity()
        self.update_logs_view()
        self.update_reports()

    # ========================================================
    # DASHBOARD ACTIVITY VIEW
    # ========================================================

    def update_dashboard_activity(self):

        if not hasattr(
            self,
            "dashboard_activity"
        ):
            return

        self.update_textbox(
            self.dashboard_activity,
            "\n".join(
                reversed(
                    self.activity_events
                )
            )
        )

    # ========================================================
    # ACTIVITY LOG VIEW
    # ========================================================

    def update_logs_view(self):

        if not hasattr(
            self,
            "logs_text"
        ):
            return

        if not self.activity_events:

            text = (
                "No activity logs received yet."
            )

        else:

            text = "\n".join(
                reversed(
                    self.activity_events
                )
            )

        self.update_textbox(
            self.logs_text,
            text
        )

    # ========================================================
    # SECURITY
    # ========================================================

    def add_security_event(
        self,
        message
    ):

        self.update_security_view()
        self.update_reports()

    # ========================================================
    # SECURITY VIEW
    # ========================================================

    def update_security_view(self):

        if not hasattr(
            self,
            "security_text"
        ):
            return

        if not self.security_events:

            text = (
                "No security events received yet."
            )

        else:

            text = "\n".join(
                reversed(
                    [
                        (
                            event["time"]
                            + "  ["
                            + event["severity"]
                            + "] "
                            + event["description"]
                        )
                        for event in self.security_events
                    ]
                )
            )

        self.update_textbox(
            self.security_text,
            text
        )

        if hasattr(
            self,
            "dashboard_security"
        ):

            self.update_textbox(
                self.dashboard_security,
                text
            )

    # ========================================================
    # TEXTBOX HELPER
    # ========================================================

    def update_textbox(
        self,
        textbox,
        text
    ):

        if textbox is None:
            return

        try:

            textbox.configure(
                state="normal"
            )

            textbox.delete(
                "1.0",
                "end"
            )

            if text:

                textbox.insert(
                    "1.0",
                    text
                )

            else:

                textbox.insert(
                    "1.0",
                    "No events received yet."
                )

            textbox.configure(
                state="disabled"
            )

        except Exception as error:

            print(
                f"[ADMIN UI] Textbox update error: {error}"
            )

    # ========================================================
    # REPORTS
    # ========================================================

    def update_reports(self):

        if not hasattr(
            self,
            "report_total"
        ):
            return

        total = (
            len(self.activity_events)
            + len(self.security_events)
        )

        self.report_total.configure(
            text=str(total)
        )

        self.report_security.configure(
            text=str(
                len(self.security_events)
            )
        )

        self.report_activity.configure(
            text=str(
                len(self.activity_events)
            )
        )

    # ========================================================
    # GENERATE REPORT
    # ========================================================

    def generate_report(self):

        timestamp = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        total = len(
            self.employee_status
        )

        online = sum(
            1
            for employee in self.employee_status.values()
            if employee.get("status") == "ONLINE"
        )

        offline = sum(
            1
            for employee in self.employee_status.values()
            if employee.get("status") == "OFFLINE"
        )

        report = (
            "LEAKGUARD SECURITY REPORT\n"
            "==========================\n\n"
            f"Generated: {timestamp}\n"
            f"Administrator: {self.username}\n\n"
            f"Employees: {total}\n"
            f"Online: {online}\n"
            f"Offline: {offline}\n"
            f"Activity Events: {len(self.activity_events)}\n"
            f"Security Events: {len(self.security_events)}\n"
        )

        print(
            "\n" + report
        )

        self.add_activity(
            "Security report generated"
        )

    # ========================================================
    # CLOCK
    # ========================================================

    def update_clock(self):

        try:

            if not self.parent.winfo_exists():
                return

            current_time = datetime.now().strftime(
                "%d %b %Y  |  %H:%M:%S"
            )

            if hasattr(
                self,
                "clock_label"
            ):

                self.clock_label.configure(
                    text=current_time
                )

            self.parent.after(
                1000,
                self.update_clock
            )

        except Exception:
            pass

    # ========================================================
    # CLOSE DASHBOARD
    # ========================================================

    def close_dashboard(self):

        print(
            "[ADMIN] Closing dashboard..."
        )

        try:

            if hasattr(
                self,
                "websocket_client"
            ):

                self.websocket_client.stop()

        except Exception as error:

            print(
                f"[ADMIN] WebSocket shutdown error: {error}"
            )

        try:

            self.parent.destroy()

        except Exception:
            pass