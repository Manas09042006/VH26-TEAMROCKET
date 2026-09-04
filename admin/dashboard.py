import customtkinter as ctk
from datetime import datetime


class DashboardWindow:

    def __init__(self, root, username):
        self.root = root
        self.username = username
        self.sidebar_open = True
        self.dark_mode = True
        self.current_page = "Dashboard"

        self.setup_theme()
        self.setup_window()
        self.build_interface()

        self.root.bind("<F11>", self.toggle_fullscreen)
        self.root.bind("<Escape>", self.exit_fullscreen)

        self.update_clock()
        self.show_dashboard()

    # =========================================================
    # THEME
    # =========================================================

    def setup_theme(self):

        if self.dark_mode:
            self.colors = {
                "bg": "#080C14",
                "sidebar": "#0B111C",
                "card": "#111927",
                "card_hover": "#172235",
                "border": "#1D2A3A",

                "primary": "#4F8CFF",
                "primary_hover": "#6B9FFF",

                "success": "#32D583",
                "warning": "#FFB547",
                "danger": "#FF5C70",
                "info": "#5EC8FF",

                "text": "#F4F7FB",
                "muted": "#8C9AAF",
                "dim": "#596679",

                "input": "#0E1622",
            }

        else:
            self.colors = {
                "bg": "#F3F6FA",
                "sidebar": "#FFFFFF",
                "card": "#FFFFFF",
                "card_hover": "#F0F4FA",
                "border": "#DCE3EC",

                "primary": "#2864D7",
                "primary_hover": "#3E78E5",

                "success": "#159F63",
                "warning": "#D98A00",
                "danger": "#D9364F",
                "info": "#168DC4",

                "text": "#172033",
                "muted": "#68758A",
                "dim": "#8E9AAC",

                "input": "#F0F3F7",
            }

        ctk.set_appearance_mode("dark" if self.dark_mode else "light")

    # =========================================================
    # WINDOW
    # =========================================================

    def setup_window(self):

        self.root.title("LeakGuard | Security Administration")

        # Full screen
        self.root.attributes("-fullscreen", True)

        self.root.configure(
            fg_color=self.colors["bg"]
        )

        self.root.minsize(1000, 650)

    def toggle_fullscreen(self, event=None):

        current = self.root.attributes("-fullscreen")

        self.root.attributes(
            "-fullscreen",
            not current
        )

    def exit_fullscreen(self, event=None):

        self.root.attributes(
            "-fullscreen",
            False
        )

    # =========================================================
    # MAIN INTERFACE
    # =========================================================

    def build_interface(self):

        self.root.grid_columnconfigure(
            0,
            weight=0
        )

        self.root.grid_columnconfigure(
            1,
            weight=1
        )

        self.root.grid_rowconfigure(
            0,
            weight=1
        )

        self.build_sidebar()
        self.build_main_area()

    # =========================================================
    # SIDEBAR
    # =========================================================

    def build_sidebar(self):

        self.sidebar = ctk.CTkFrame(
            self.root,
            width=250,
            corner_radius=0,
            fg_color=self.colors["sidebar"],
            border_width=1,
            border_color=self.colors["border"]
        )

        self.sidebar.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        self.sidebar.grid_propagate(False)

        self.sidebar.grid_rowconfigure(
            10,
            weight=1
        )

        # -------------------------
        # LOGO
        # -------------------------

        logo_frame = ctk.CTkFrame(
            self.sidebar,
            fg_color="transparent"
        )

        logo_frame.pack(
            fill="x",
            padx=20,
            pady=(24, 20)
        )

        logo_icon = ctk.CTkLabel(
            logo_frame,
            text="◈",
            font=ctk.CTkFont(
                size=30,
                weight="bold"
            ),
            text_color=self.colors["primary"]
        )

        logo_icon.pack(
            side="left"
        )

        logo_text = ctk.CTkFrame(
            logo_frame,
            fg_color="transparent"
        )

        logo_text.pack(
            side="left",
            padx=10
        )

        ctk.CTkLabel(
            logo_text,
            text="LEAKGUARD",
            font=ctk.CTkFont(
                size=18,
                weight="bold"
            ),
            text_color=self.colors["text"]
        ).pack(anchor="w")

        ctk.CTkLabel(
            logo_text,
            text="SECURITY CONSOLE",
            font=ctk.CTkFont(
                size=9,
                weight="bold"
            ),
            text_color=self.colors["muted"]
        ).pack(anchor="w")

        # -------------------------
        # SYSTEM OWNER
        # -------------------------

        profile = ctk.CTkFrame(
            self.sidebar,
            fg_color=self.colors["card"],
            corner_radius=12,
            border_width=1,
            border_color=self.colors["border"]
        )

        profile.pack(
            fill="x",
            padx=15,
            pady=(0, 20)
        )

        ctk.CTkLabel(
            profile,
            text="SYSTEM OWNER",
            font=ctk.CTkFont(
                size=9,
                weight="bold"
            ),
            text_color=self.colors["muted"]
        ).pack(
            anchor="w",
            padx=14,
            pady=(12, 2)
        )

        ctk.CTkLabel(
            profile,
            text=self.username.upper(),
            font=ctk.CTkFont(
                size=14,
                weight="bold"
            ),
            text_color=self.colors["text"]
        ).pack(
            anchor="w",
            padx=14
        )

        ctk.CTkLabel(
            profile,
            text="●  Administrator",
            font=ctk.CTkFont(size=10),
            text_color=self.colors["success"]
        ).pack(
            anchor="w",
            padx=14,
            pady=(2, 12)
        )

        # -------------------------
        # NAVIGATION
        # -------------------------

        ctk.CTkLabel(
            self.sidebar,
            text="CONTROL CENTER",
            font=ctk.CTkFont(
                size=9,
                weight="bold"
            ),
            text_color=self.colors["dim"]
        ).pack(
            anchor="w",
            padx=20,
            pady=(0, 8)
        )

        self.nav_buttons = {}

        navigation = [
            ("Dashboard", "⌂"),
            ("Employees", "♙"),
            ("Activity Logs", "≡"),
            ("Security Events", "⚠"),
            ("Reports", "▤"),
            ("Settings", "⚙"),
        ]

        for name, icon in navigation:
            self.create_nav_button(
                name,
                icon
            )

        # -------------------------
        # BOTTOM
        # -------------------------

        bottom = ctk.CTkFrame(
            self.sidebar,
            fg_color="transparent"
        )

        bottom.pack(
            side="bottom",
            fill="x",
            padx=15,
            pady=15
        )

        ctk.CTkButton(
            bottom,
            text="⇥   LOGOUT",
            height=42,
            corner_radius=10,
            fg_color="transparent",
            hover_color=self.colors["card_hover"],
            text_color=self.colors["danger"],
            font=ctk.CTkFont(
                size=12,
                weight="bold"
            ),
            command=self.logout
        ).pack(fill="x")

    # =========================================================
    # NAV BUTTON
    # =========================================================

    def create_nav_button(self, name, icon):

        button = ctk.CTkButton(
            self.sidebar,
            text=f"   {icon}     {name}",
            height=45,
            corner_radius=10,
            anchor="w",
            fg_color="transparent",
            hover_color=self.colors["card_hover"],
            text_color=self.colors["muted"],
            font=ctk.CTkFont(
                size=12,
                weight="bold"
            ),
            command=lambda: self.navigate(name)
        )

        button.pack(
            fill="x",
            padx=12,
            pady=3
        )

        self.nav_buttons[name] = button

    # =========================================================
    # MAIN AREA
    # =========================================================

    def build_main_area(self):

        self.main = ctk.CTkFrame(
            self.root,
            fg_color=self.colors["bg"],
            corner_radius=0
        )

        self.main.grid(
            row=0,
            column=1,
            sticky="nsew"
        )

        self.main.grid_rowconfigure(
            1,
            weight=1
        )

        self.main.grid_columnconfigure(
            0,
            weight=1
        )

        self.build_topbar()

        self.content = ctk.CTkScrollableFrame(
            self.main,
            fg_color="transparent",
            corner_radius=0
        )

        self.content.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=30,
            pady=(10, 25)
        )

    # =========================================================
    # TOP BAR
    # =========================================================

    def build_topbar(self):

        self.topbar = ctk.CTkFrame(
            self.main,
            height=76,
            fg_color=self.colors["bg"],
            corner_radius=0
        )

        self.topbar.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=25
        )

        self.topbar.grid_columnconfigure(
            2,
            weight=1
        )

        # Sidebar toggle

        self.sidebar_button = ctk.CTkButton(
            self.topbar,
            text="☰",
            width=45,
            height=40,
            corner_radius=10,
            fg_color=self.colors["card"],
            hover_color=self.colors["card_hover"],
            text_color=self.colors["text"],
            font=ctk.CTkFont(
                size=18,
                weight="bold"
            ),
            command=self.toggle_sidebar
        )

        self.sidebar_button.grid(
            row=0,
            column=0,
            padx=(0, 15),
            pady=18
        )

        # Page title

        self.page_title = ctk.CTkLabel(
            self.topbar,
            text="DASHBOARD",
            font=ctk.CTkFont(
                size=14,
                weight="bold"
            ),
            text_color=self.colors["text"]
        )

        self.page_title.grid(
            row=0,
            column=1,
            sticky="w"
        )

        # Right side

        self.status = ctk.CTkLabel(
            self.topbar,
            text="●  SYSTEM ONLINE",
            font=ctk.CTkFont(
                size=11,
                weight="bold"
            ),
            text_color=self.colors["success"]
        )

        self.status.grid(
            row=0,
            column=3,
            padx=20
        )

        self.clock = ctk.CTkLabel(
            self.topbar,
            text="",
            font=ctk.CTkFont(
                size=11
            ),
            text_color=self.colors["muted"]
        )

        self.clock.grid(
            row=0,
            column=4,
            padx=(10, 15)
        )

        self.mode_button = ctk.CTkButton(
            self.topbar,
            text="☾",
            width=42,
            height=40,
            corner_radius=10,
            fg_color=self.colors["card"],
            hover_color=self.colors["card_hover"],
            text_color=self.colors["text"],
            font=ctk.CTkFont(size=17),
            command=self.toggle_theme
        )

        self.mode_button.grid(
            row=0,
            column=5
        )

    # =========================================================
    # SIDEBAR TOGGLE
    # =========================================================

    def toggle_sidebar(self):

        if self.sidebar_open:

            self.sidebar.grid_remove()

            self.sidebar_open = False

        else:

            self.sidebar.grid()

            self.sidebar_open = True

    # =========================================================
    # NAVIGATION
    # =========================================================

    def navigate(self, page):

        self.current_page = page

        self.set_active(page)

        self.page_title.configure(
            text=page.upper()
        )

        self.clear_content()

        if page == "Dashboard":
            self.show_dashboard()

        elif page == "Employees":
            self.show_employees()

        elif page == "Activity Logs":
            self.show_logs()

        elif page == "Security Events":
            self.show_security()

        elif page == "Reports":
            self.show_reports()

        elif page == "Settings":
            self.show_settings()

    def set_active(self, active):

        for name, button in self.nav_buttons.items():

            if name == active:

                button.configure(
                    fg_color=self.colors["primary"],
                    hover_color=self.colors["primary_hover"],
                    text_color="#FFFFFF"
                )

            else:

                button.configure(
                    fg_color="transparent",
                    hover_color=self.colors["card_hover"],
                    text_color=self.colors["muted"]
                )

    def clear_content(self):

        for widget in self.content.winfo_children():
            widget.destroy()

    # =========================================================
    # DASHBOARD
    # =========================================================

    def show_dashboard(self):

        # Header

        ctk.CTkLabel(
            self.content,
            text="Security Overview",
            font=ctk.CTkFont(
                size=30,
                weight="bold"
            ),
            text_color=self.colors["text"]
        ).pack(
            anchor="w",
            pady=(10, 3)
        )

        ctk.CTkLabel(
            self.content,
            text="Monitor resource leaks, system activity and security health.",
            font=ctk.CTkFont(
                size=13
            ),
            text_color=self.colors["muted"]
        ).pack(
            anchor="w",
            pady=(0, 25)
        )

        # Stats

        stats = ctk.CTkFrame(
            self.content,
            fg_color="transparent"
        )

        stats.pack(
            fill="x",
            pady=(0, 25)
        )

        stats.grid_columnconfigure(
            (0, 1, 2, 3),
            weight=1
        )

        self.create_stat_card(
            stats,
            0,
            "128",
            "TOTAL SCANS",
            "↑ 18% this month",
            self.colors["primary"]
        )

        self.create_stat_card(
            stats,
            1,
            "94",
            "PASSED",
            "73.4% success rate",
            self.colors["success"]
        )

        self.create_stat_card(
            stats,
            2,
            "7",
            "SECURITY ALERTS",
            "2 require attention",
            self.colors["warning"]
        )

        self.create_stat_card(
            stats,
            3,
            "3",
            "RESOURCE LEAKS",
            "Build blocking issues",
            self.colors["danger"]
        )

        # Lower section

        lower = ctk.CTkFrame(
            self.content,
            fg_color="transparent"
        )

        lower.pack(
            fill="both",
            expand=True
        )

        lower.grid_columnconfigure(
            0,
            weight=2
        )

        lower.grid_columnconfigure(
            1,
            weight=1
        )

        self.create_activity_panel(lower)
        self.create_health_panel(lower)

    # =========================================================
    # STAT CARD
    # =========================================================

    def create_stat_card(
        self,
        parent,
        column,
        value,
        title,
        description,
        accent
    ):

        card = ctk.CTkFrame(
            parent,
            fg_color=self.colors["card"],
            corner_radius=14,
            border_width=1,
            border_color=self.colors["border"]
        )

        card.grid(
            row=0,
            column=column,
            sticky="ew",
            padx=6
        )

        ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(
                size=10,
                weight="bold"
            ),
            text_color=self.colors["muted"]
        ).pack(
            anchor="w",
            padx=18,
            pady=(18, 2)
        )

        ctk.CTkLabel(
            card,
            text=value,
            font=ctk.CTkFont(
                size=32,
                weight="bold"
            ),
            text_color=self.colors["text"]
        ).pack(
            anchor="w",
            padx=18
        )

        ctk.CTkLabel(
            card,
            text=description,
            font=ctk.CTkFont(
                size=10
            ),
            text_color=accent
        ).pack(
            anchor="w",
            padx=18,
            pady=(2, 18)
        )

    # =========================================================
    # ACTIVITY PANEL
    # =========================================================

    def create_activity_panel(self, parent):

        panel = ctk.CTkFrame(
            parent,
            fg_color=self.colors["card"],
            corner_radius=14,
            border_width=1,
            border_color=self.colors["border"]
        )

        panel.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 10)
        )

        ctk.CTkLabel(
            panel,
            text="Recent Activity",
            font=ctk.CTkFont(
                size=16,
                weight="bold"
            ),
            text_color=self.colors["text"]
        ).pack(
            anchor="w",
            padx=20,
            pady=(20, 2)
        )

        ctk.CTkLabel(
            panel,
            text="Latest administrator and analyzer events",
            font=ctk.CTkFont(size=10),
            text_color=self.colors["muted"]
        ).pack(
            anchor="w",
            padx=20,
            pady=(0, 15)
        )

        activities = [
            ("Resource scan completed", "main.py", "2 min ago", "success"),
            ("Leak detected", "database.py", "18 min ago", "danger"),
            ("Employee permissions updated", "admin", "42 min ago", "info"),
            ("Security report generated", "weekly", "1 hr ago", "info"),
            ("CI build blocked", "workflow", "2 hrs ago", "danger"),
        ]

        for title, target, time, state in activities:

            row = ctk.CTkFrame(
                panel,
                fg_color="transparent"
            )

            row.pack(
                fill="x",
                padx=18,
                pady=4
            )

            indicator_color = self.colors[state]

            ctk.CTkLabel(
                row,
                text="●",
                font=ctk.CTkFont(size=13),
                text_color=indicator_color
            ).pack(
                side="left"
            )

            info = ctk.CTkFrame(
                row,
                fg_color="transparent"
            )

            info.pack(
                side="left",
                padx=10
            )

            ctk.CTkLabel(
                info,
                text=title,
                font=ctk.CTkFont(
                    size=11,
                    weight="bold"
                ),
                text_color=self.colors["text"]
            ).pack(anchor="w")

            ctk.CTkLabel(
                info,
                text=target,
                font=ctk.CTkFont(size=9),
                text_color=self.colors["muted"]
            ).pack(anchor="w")

            ctk.CTkLabel(
                row,
                text=time,
                font=ctk.CTkFont(size=9),
                text_color=self.colors["dim"]
            ).pack(
                side="right"
            )

    # =========================================================
    # HEALTH PANEL
    # =========================================================

    def create_health_panel(self, parent):

        panel = ctk.CTkFrame(
            parent,
            fg_color=self.colors["card"],
            corner_radius=14,
            border_width=1,
            border_color=self.colors["border"]
        )

        panel.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(10, 0)
        )

        ctk.CTkLabel(
            panel,
            text="System Health",
            font=ctk.CTkFont(
                size=16,
                weight="bold"
            ),
            text_color=self.colors["text"]
        ).pack(
            anchor="w",
            padx=20,
            pady=(20, 2)
        )

        ctk.CTkLabel(
            panel,
            text="Current infrastructure status",
            font=ctk.CTkFont(size=10),
            text_color=self.colors["muted"]
        ).pack(
            anchor="w",
            padx=20,
            pady=(0, 20)
        )

        health = [
            ("Analyzer Engine", "Operational", self.colors["success"]),
            ("Resource Tracker", "Operational", self.colors["success"]),
            ("CI Integration", "Operational", self.colors["success"]),
            ("Security Database", "Operational", self.colors["success"]),
        ]

        for name, status, color in health:

            row = ctk.CTkFrame(
                panel,
                fg_color="transparent"
            )

            row.pack(
                fill="x",
                padx=20,
                pady=8
            )

            ctk.CTkLabel(
                row,
                text=name,
                font=ctk.CTkFont(size=10),
                text_color=self.colors["text"]
            ).pack(side="left")

            ctk.CTkLabel(
                row,
                text=f"● {status}",
                font=ctk.CTkFont(
                    size=9,
                    weight="bold"
                ),
                text_color=color
            ).pack(side="right")

    # =========================================================
    # EMPLOYEES
    # =========================================================

    def show_employees(self):

        self.page_header(
            "Employees",
            "Manage employees, roles and system access."
        )

        actions = ctk.CTkFrame(
            self.content,
            fg_color="transparent"
        )

        actions.pack(
            fill="x",
            pady=(0, 20)
        )

        ctk.CTkButton(
            actions,
            text="+  ADD EMPLOYEE",
            height=40,
            corner_radius=9,
            fg_color=self.colors["primary"],
            hover_color=self.colors["primary_hover"],
            font=ctk.CTkFont(
                size=11,
                weight="bold"
            )
        ).pack(side="right")

        employees = [
            ("EMP-001", "Aarav Sharma", "Security Analyst", "Active"),
            ("EMP-002", "Riya Patel", "Developer", "Active"),
            ("EMP-003", "Karan Mehta", "DevOps Engineer", "Active"),
            ("EMP-004", "Neha Rao", "System Administrator", "Active"),
            ("EMP-005", "Vikram Singh", "Developer", "Suspended"),
        ]

        table = ctk.CTkFrame(
            self.content,
            fg_color=self.colors["card"],
            corner_radius=14,
            border_width=1,
            border_color=self.colors["border"]
        )

        table.pack(
            fill="both",
            expand=True
        )

        headers = [
            "EMPLOYEE ID",
            "NAME",
            "ROLE",
            "STATUS",
            "ACTION"
        ]

        for i, header in enumerate(headers):

            table.grid_columnconfigure(
                i,
                weight=1
            )

            ctk.CTkLabel(
                table,
                text=header,
                font=ctk.CTkFont(
                    size=9,
                    weight="bold"
                ),
                text_color=self.colors["muted"]
            ).grid(
                row=0,
                column=i,
                sticky="w",
                padx=18,
                pady=18
            )

        for row_index, employee in enumerate(
            employees,
            start=1
        ):

            for column_index, value in enumerate(employee):

                if column_index == 3:

                    status_color = (
                        self.colors["success"]
                        if value == "Active"
                        else self.colors["danger"]
                    )

                    ctk.CTkLabel(
                        table,
                        text=f"● {value}",
                        font=ctk.CTkFont(size=10),
                        text_color=status_color
                    ).grid(
                        row=row_index,
                        column=column_index,
                        sticky="w",
                        padx=18,
                        pady=15
                    )

                elif column_index == 4:

                    ctk.CTkButton(
                        table,
                        text="VIEW",
                        width=70,
                        height=30,
                        corner_radius=7,
                        fg_color=self.colors["input"],
                        hover_color=self.colors["card_hover"],
                        text_color=self.colors["text"],
                        font=ctk.CTkFont(
                            size=9,
                            weight="bold"
                        )
                    ).grid(
                        row=row_index,
                        column=column_index,
                        padx=18,
                        pady=8
                    )

                else:

                    ctk.CTkLabel(
                        table,
                        text=value,
                        font=ctk.CTkFont(size=10),
                        text_color=self.colors["text"]
                    ).grid(
                        row=row_index,
                        column=column_index,
                        sticky="w",
                        padx=18,
                        pady=15
                    )

    # =========================================================
    # ACTIVITY LOGS
    # =========================================================

    def show_logs(self):

        self.page_header(
            "Activity Logs",
            "Complete audit trail of administrator and system activity."
        )

        logs = [
            ("10:42:31", "ADMIN", "Login successful", "Authentication"),
            ("10:38:14", "SYSTEM", "Resource scan completed", "Analyzer"),
            ("10:21:06", "ADMIN", "Permissions viewed", "Access Control"),
            ("09:57:42", "SYSTEM", "Leak detected in database.py", "Security"),
            ("09:31:20", "CI", "Build blocked", "Pipeline"),
            ("09:12:18", "ADMIN", "Security report generated", "Reports"),
        ]

        for time, actor, action, category in logs:

            card = ctk.CTkFrame(
                self.content,
                fg_color=self.colors["card"],
                corner_radius=10,
                border_width=1,
                border_color=self.colors["border"]
            )

            card.pack(
                fill="x",
                pady=5
            )

            ctk.CTkLabel(
                card,
                text=time,
                width=90,
                font=ctk.CTkFont(
                    size=10,
                    weight="bold"
                ),
                text_color=self.colors["muted"]
            ).pack(
                side="left",
                padx=15,
                pady=15
            )

            ctk.CTkLabel(
                card,
                text=actor,
                width=80,
                font=ctk.CTkFont(
                    size=10,
                    weight="bold"
                ),
                text_color=self.colors["primary"]
            ).pack(
                side="left"
            )

            ctk.CTkLabel(
                card,
                text=action,
                font=ctk.CTkFont(
                    size=11,
                    weight="bold"
                ),
                text_color=self.colors["text"]
            ).pack(
                side="left",
                padx=10
            )

            ctk.CTkLabel(
                card,
                text=category,
                font=ctk.CTkFont(size=9),
                text_color=self.colors["muted"]
            ).pack(
                side="right",
                padx=20
            )

    # =========================================================
    # SECURITY EVENTS
    # =========================================================

    def show_security(self):

        self.page_header(
            "Security Events",
            "Threats, resource leaks and policy violations detected by LeakGuard."
        )

        events = [
            (
                "CRITICAL",
                "Resource leak detected",
                "database.py",
                "Connection opened without guaranteed close.",
                self.colors["danger"]
            ),
            (
                "HIGH",
                "Build blocked by LeakGuard",
                "CI Pipeline",
                "Static analysis returned exit code 1.",
                self.colors["warning"]
            ),
            (
                "MEDIUM",
                "Repeated scan failure",
                "payment.py",
                "Analyzer encountered an unsupported pattern.",
                self.colors["warning"]
            ),
        ]

        for severity, title, target, description, color in events:

            card = ctk.CTkFrame(
                self.content,
                fg_color=self.colors["card"],
                corner_radius=14,
                border_width=1,
                border_color=self.colors["border"]
            )

            card.pack(
                fill="x",
                pady=7
            )

            ctk.CTkLabel(
                card,
                text=severity,
                width=80,
                height=30,
                corner_radius=7,
                fg_color=color,
                text_color="#FFFFFF",
                font=ctk.CTkFont(
                    size=9,
                    weight="bold"
                )
            ).pack(
                side="left",
                padx=18,
                pady=18
            )

            info = ctk.CTkFrame(
                card,
                fg_color="transparent"
            )

            info.pack(
                side="left",
                fill="x",
                expand=True,
                padx=5,
                pady=14
            )

            ctk.CTkLabel(
                info,
                text=title,
                font=ctk.CTkFont(
                    size=12,
                    weight="bold"
                ),
                text_color=self.colors["text"]
            ).pack(anchor="w")

            ctk.CTkLabel(
                info,
                text=target,
                font=ctk.CTkFont(size=9),
                text_color=color
            ).pack(anchor="w")

            ctk.CTkLabel(
                info,
                text=description,
                font=ctk.CTkFont(size=10),
                text_color=self.colors["muted"]
            ).pack(anchor="w")

            ctk.CTkButton(
                card,
                text="INSPECT",
                width=85,
                height=32,
                corner_radius=8,
                fg_color=self.colors["input"],
                hover_color=self.colors["card_hover"],
                text_color=self.colors["text"],
                font=ctk.CTkFont(
                    size=9,
                    weight="bold"
                )
            ).pack(
                side="right",
                padx=18
            )

    # =========================================================
    # REPORTS
    # =========================================================

    def show_reports(self):

        self.page_header(
            "Reports",
            "Generate and review security analysis reports."
        )

        reports = [
            ("Weekly Security Report", "128 scans • 3 leaks", "Generated today"),
            ("Resource Leak Summary", "17 detected • 14 resolved", "Generated yesterday"),
            ("CI Compliance Report", "94 successful builds", "Generated 2 days ago"),
            ("Employee Activity Report", "5 administrators", "Generated 3 days ago"),
        ]

        for title, details, date in reports:

            card = ctk.CTkFrame(
                self.content,
                fg_color=self.colors["card"],
                corner_radius=13,
                border_width=1,
                border_color=self.colors["border"]
            )

            card.pack(
                fill="x",
                pady=6
            )

            icon = ctk.CTkLabel(
                card,
                text="▤",
                font=ctk.CTkFont(
                    size=24,
                    weight="bold"
                ),
                text_color=self.colors["primary"]
            )

            icon.pack(
                side="left",
                padx=20,
                pady=18
            )

            info = ctk.CTkFrame(
                card,
                fg_color="transparent"
            )

            info.pack(
                side="left",
                fill="x",
                expand=True,
                pady=14
            )

            ctk.CTkLabel(
                info,
                text=title,
                font=ctk.CTkFont(
                    size=12,
                    weight="bold"
                ),
                text_color=self.colors["text"]
            ).pack(anchor="w")

            ctk.CTkLabel(
                info,
                text=details,
                font=ctk.CTkFont(size=10),
                text_color=self.colors["muted"]
            ).pack(anchor="w")

            ctk.CTkLabel(
                info,
                text=date,
                font=ctk.CTkFont(size=9),
                text_color=self.colors["dim"]
            ).pack(anchor="w")

            ctk.CTkButton(
                card,
                text="VIEW REPORT",
                width=110,
                height=34,
                corner_radius=8,
                fg_color=self.colors["primary"],
                hover_color=self.colors["primary_hover"],
                font=ctk.CTkFont(
                    size=9,
                    weight="bold"
                )
            ).pack(
                side="right",
                padx=20
            )

    # =========================================================
    # SETTINGS
    # =========================================================

    def show_settings(self):

        self.page_header(
            "Settings",
            "Configure the administration console."
        )

        self.settings_card(
            "Appearance",
            "Change the visual appearance of the administration console.",
            self.create_appearance_setting
        )

        self.settings_card(
            "Security",
            "Manage authentication and administrator security policies.",
            self.create_security_setting
        )

        self.settings_card(
            "System",
            "Configure analyzer and dashboard behavior.",
            self.create_system_setting
        )

    def settings_card(
        self,
        title,
        description,
        content_builder
    ):

        card = ctk.CTkFrame(
            self.content,
            fg_color=self.colors["card"],
            corner_radius=14,
            border_width=1,
            border_color=self.colors["border"]
        )

        card.pack(
            fill="x",
            pady=7
        )

        ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(
                size=15,
                weight="bold"
            ),
            text_color=self.colors["text"]
        ).pack(
            anchor="w",
            padx=20,
            pady=(18, 2)
        )

        ctk.CTkLabel(
            card,
            text=description,
            font=ctk.CTkFont(size=10),
            text_color=self.colors["muted"]
        ).pack(
            anchor="w",
            padx=20,
            pady=(0, 12)
        )

        content_builder(card)

    def create_appearance_setting(self, parent):

        row = ctk.CTkFrame(
            parent,
            fg_color="transparent"
        )

        row.pack(
            fill="x",
            padx=20,
            pady=(0, 18)
        )

        ctk.CTkLabel(
            row,
            text="Day / Night Mode",
            font=ctk.CTkFont(size=11),
            text_color=self.colors["text"]
        ).pack(side="left")

        switch = ctk.CTkSwitch(
            row,
            text="",
            command=self.toggle_theme
        )

        switch.pack(side="right")

        if self.dark_mode:
            switch.select()

    def create_security_setting(self, parent):

        row = ctk.CTkFrame(
            parent,
            fg_color="transparent"
        )

        row.pack(
            fill="x",
            padx=20,
            pady=(0, 18)
        )

        ctk.CTkLabel(
            row,
            text="Administrator session protection",
            font=ctk.CTkFont(size=11),
            text_color=self.colors["text"]
        ).pack(side="left")

        ctk.CTkSwitch(
            row,
            text="Enabled"
        ).pack(side="right")

    def create_system_setting(self, parent):

        row = ctk.CTkFrame(
            parent,
            fg_color="transparent"
        )

        row.pack(
            fill="x",
            padx=20,
            pady=(0, 18)
        )

        ctk.CTkLabel(
            row,
            text="Live system monitoring",
            font=ctk.CTkFont(size=11),
            text_color=self.colors["text"]
        ).pack(side="left")

        ctk.CTkSwitch(
            row,
            text="Enabled"
        ).pack(side="right")

    # =========================================================
    # PAGE HEADER
    # =========================================================

    def page_header(self, title, description):

        ctk.CTkLabel(
            self.content,
            text=title,
            font=ctk.CTkFont(
                size=30,
                weight="bold"
            ),
            text_color=self.colors["text"]
        ).pack(
            anchor="w",
            pady=(10, 3)
        )

        ctk.CTkLabel(
            self.content,
            text=description,
            font=ctk.CTkFont(
                size=13
            ),
            text_color=self.colors["muted"]
        ).pack(
            anchor="w",
            pady=(0, 25)
        )

    # =========================================================
    # THEME
    # =========================================================

    def toggle_theme(self):

        self.dark_mode = not self.dark_mode

        self.setup_theme()

        for widget in self.root.winfo_children():
            widget.destroy()

        self.build_interface()

        self.set_active(
            self.current_page
        )

        self.page_title.configure(
            text=self.current_page.upper()
        )

        self.update_clock()

        self.clear_content()

        if self.current_page == "Dashboard":
            self.show_dashboard()

        elif self.current_page == "Employees":
            self.show_employees()

        elif self.current_page == "Activity Logs":
            self.show_logs()

        elif self.current_page == "Security Events":
            self.show_security()

        elif self.current_page == "Reports":
            self.show_reports()

        elif self.current_page == "Settings":
            self.show_settings()

    # =========================================================
    # CLOCK
    # =========================================================

    def update_clock(self):

        if not self.root.winfo_exists():
            return

        now = datetime.now()

        self.clock.configure(
            text=now.strftime(
                "%d %b %Y   •   %I:%M:%S %p"
            )
        )

        self.root.after(
            1000,
            self.update_clock
        )

    # =========================================================
    # LOGOUT
    # =========================================================

    def logout(self):

        self.root.destroy()