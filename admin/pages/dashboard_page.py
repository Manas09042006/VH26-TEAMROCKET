import customtkinter as ctk
from datetime import datetime


class DashboardWindow(ctk.CTkFrame):

    BG = "#080B12"
    SIDEBAR = "#0B0F17"
    CARD = "#111722"
    CARD_HOVER = "#171F2C"
    BORDER = "#202938"

    TEXT = "#F4F7FB"
    MUTED = "#8B96A8"

    ACCENT = "#6878FF"
    SUCCESS = "#35D48A"
    WARNING = "#F4B942"
    DANGER = "#FF5C70"

    def __init__(self, master, username):

        super().__init__(
            master,
            fg_color=self.BG
        )

        self.master = master
        self.username = username

        self.current_page = "Dashboard"
        self.sidebar_collapsed = False

        self.pack(
            fill="both",
            expand=True
        )

        self.build_layout()

        self.create_pages()

        self.show_page("Dashboard")

        self.update_clock()

        self.bind("<Configure>", self.on_resize)

    # ==========================================================
    # MAIN LAYOUT
    # ==========================================================

    def build_layout(self):

        self.grid_rowconfigure(
            0,
            weight=1
        )

        self.grid_columnconfigure(
            1,
            weight=1
        )

        # Sidebar
        self.sidebar = ctk.CTkFrame(
            self,
            width=250,
            corner_radius=0,
            fg_color=self.SIDEBAR
        )

        self.sidebar.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        self.sidebar.grid_propagate(False)

        # Main
        self.main_area = ctk.CTkFrame(
            self,
            fg_color=self.BG,
            corner_radius=0
        )

        self.main_area.grid(
            row=0,
            column=1,
            sticky="nsew"
        )

        self.main_area.grid_rowconfigure(
            1,
            weight=1
        )

        self.main_area.grid_columnconfigure(
            0,
            weight=1
        )

        self.build_sidebar()
        self.build_topbar()

        self.content_area = ctk.CTkFrame(
            self.main_area,
            fg_color=self.BG,
            corner_radius=0
        )

        self.content_area.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=25,
            pady=(0, 25)
        )

        self.content_area.grid_rowconfigure(
            0,
            weight=1
        )

        self.content_area.grid_columnconfigure(
            0,
            weight=1
        )

    # ==========================================================
    # SIDEBAR
    # ==========================================================

    def build_sidebar(self):

        self.logo_frame = ctk.CTkFrame(
            self.sidebar,
            fg_color="transparent"
        )

        self.logo_frame.pack(
            fill="x",
            padx=18,
            pady=(22, 20)
        )

        self.logo = ctk.CTkLabel(
            self.logo_frame,
            text="L",
            width=42,
            height=42,
            corner_radius=12,
            fg_color=self.ACCENT,
            text_color="white",
            font=ctk.CTkFont(
                size=20,
                weight="bold"
            )
        )

        self.logo.pack(
            side="left"
        )

        self.logo_text = ctk.CTkFrame(
            self.logo_frame,
            fg_color="transparent"
        )

        self.logo_text.pack(
            side="left",
            padx=12
        )

        ctk.CTkLabel(
            self.logo_text,
            text="LEAKGUARD",
            text_color=self.TEXT,
            font=ctk.CTkFont(
                size=14,
                weight="bold"
            )
        ).pack(anchor="w")

        ctk.CTkLabel(
            self.logo_text,
            text="ADMIN CONSOLE",
            text_color=self.MUTED,
            font=ctk.CTkFont(
                size=9
            )
        ).pack(anchor="w")

        # Navigation
        self.navigation = ctk.CTkFrame(
            self.sidebar,
            fg_color="transparent"
        )

        self.navigation.pack(
            fill="x",
            padx=12
        )

        self.nav_buttons = {}

        items = [
            ("⌂", "Dashboard"),
            ("◉", "Employees"),
            ("≡", "Activity Logs"),
            ("⚠", "Security Events"),
            ("▣", "Reports"),
            ("⚙", "Settings"),
        ]

        for icon, name in items:
            self.create_nav_button(
                icon,
                name
            )

        # Bottom
        self.sidebar_bottom = ctk.CTkFrame(
            self.sidebar,
            fg_color="transparent"
        )

        self.sidebar_bottom.pack(
            side="bottom",
            fill="x",
            padx=18,
            pady=20
        )

        self.status_label = ctk.CTkLabel(
            self.sidebar_bottom,
            text="●  SYSTEM OPERATIONAL",
            text_color=self.SUCCESS,
            font=ctk.CTkFont(size=10)
        )

        self.status_label.pack(
            anchor="w",
            pady=(0, 15)
        )

        self.logout_button = ctk.CTkButton(
            self.sidebar_bottom,
            text="Logout",
            height=38,
            fg_color="transparent",
            hover_color="#18131A",
            text_color=self.DANGER,
            border_width=1,
            border_color="#30202A",
            command=self.logout
        )

        self.logout_button.pack(
            fill="x"
        )

    def create_nav_button(self, icon, name):

        button = ctk.CTkButton(
            self.navigation,
            text=f"{icon}    {name}",
            height=44,
            anchor="w",
            corner_radius=9,
            fg_color="transparent",
            hover_color=self.CARD_HOVER,
            text_color=self.MUTED,
            font=ctk.CTkFont(
                size=12
            ),
            command=lambda n=name: self.show_page(n)
        )

        button.pack(
            fill="x",
            pady=2
        )

        # Reliable hover
        button.bind(
            "<Enter>",
            lambda event, b=button: self.nav_enter(b)
        )

        button.bind(
            "<Leave>",
            lambda event, b=button: self.nav_leave(b)
        )

        self.nav_buttons[name] = button

    def nav_enter(self, button):

        if button.cget("fg_color") != self.ACCENT:
            button.configure(
                fg_color=self.CARD_HOVER,
                text_color=self.TEXT
            )

    def nav_leave(self, button):

        if button.cget("fg_color") != self.ACCENT:
            button.configure(
                fg_color="transparent",
                text_color=self.MUTED
            )

    # ==========================================================
    # TOPBAR
    # ==========================================================

    def build_topbar(self):

        self.topbar = ctk.CTkFrame(
            self.main_area,
            height=82,
            corner_radius=0,
            fg_color=self.BG
        )

        self.topbar.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=25
        )

        self.topbar.grid_columnconfigure(
            1,
            weight=1
        )

        # Menu
        self.menu_button = ctk.CTkButton(
            self.topbar,
            text="☰",
            width=40,
            height=40,
            fg_color="transparent",
            hover_color=self.CARD_HOVER,
            text_color=self.TEXT,
            font=ctk.CTkFont(size=18),
            command=self.toggle_sidebar
        )

        self.menu_button.grid(
            row=0,
            column=0,
            padx=(0, 12)
        )

        # Heading
        heading = ctk.CTkFrame(
            self.topbar,
            fg_color="transparent"
        )

        heading.grid(
            row=0,
            column=1,
            sticky="w"
        )

        self.section_label = ctk.CTkLabel(
            heading,
            text="ADMINISTRATION",
            text_color=self.ACCENT,
            font=ctk.CTkFont(
                size=9,
                weight="bold"
            )
        )

        self.section_label.pack(
            anchor="w"
        )

        self.page_title = ctk.CTkLabel(
            heading,
            text="Dashboard",
            text_color=self.TEXT,
            font=ctk.CTkFont(
                size=20,
                weight="bold"
            )
        )

        self.page_title.pack(
            anchor="w"
        )

        # Right
        right = ctk.CTkFrame(
            self.topbar,
            fg_color="transparent"
        )

        right.grid(
            row=0,
            column=2
        )

        self.clock_label = ctk.CTkLabel(
            right,
            text="--:--:--",
            text_color=self.MUTED,
            font=ctk.CTkFont(
                size=12
            )
        )

        self.clock_label.pack(
            side="left",
            padx=15
        )

        self.connection = ctk.CTkLabel(
            right,
            text="● Localhost",
            text_color=self.SUCCESS,
            font=ctk.CTkFont(
                size=11
            )
        )

        self.connection.pack(
            side="left",
            padx=10
        )

        self.avatar = ctk.CTkLabel(
            right,
            text=username_initial(self.username),
            width=38,
            height=38,
            corner_radius=10,
            fg_color="#1B2332",
            text_color=self.ACCENT,
            font=ctk.CTkFont(
                size=13,
                weight="bold"
            )
        )

        self.avatar.pack(
            side="left"
        )

    # ==========================================================
    # PAGES
    # ==========================================================

    def create_pages(self):

        self.pages = {}

        page_names = [
            "Dashboard",
            "Employees",
            "Activity Logs",
            "Security Events",
            "Reports",
            "Settings"
        ]

        for name in page_names:

            frame = ctk.CTkScrollableFrame(
                self.content_area,
                fg_color=self.BG,
                corner_radius=0
            )

            frame.grid(
                row=0,
                column=0,
                sticky="nsew"
            )

            self.pages[name] = frame

        self.build_dashboard_page()
        self.build_simple_pages()

    # ==========================================================
    # DASHBOARD
    # ==========================================================

    def build_dashboard_page(self):

        page = self.pages["Dashboard"]

        page.grid_columnconfigure(
            0,
            weight=1
        )

        # Welcome
        welcome = ctk.CTkFrame(
            page,
            fg_color="transparent"
        )

        welcome.grid(
            row=0,
            column=0,
            sticky="ew",
            pady=(5, 20)
        )

        ctk.CTkLabel(
            welcome,
            text="SYSTEM OVERVIEW",
            text_color=self.ACCENT,
            font=ctk.CTkFont(
                size=9,
                weight="bold"
            )
        ).pack(anchor="w")

        ctk.CTkLabel(
            welcome,
            text=f"Good morning, {self.username}",
            text_color=self.TEXT,
            font=ctk.CTkFont(
                size=27,
                weight="bold"
            )
        ).pack(anchor="w")

        ctk.CTkLabel(
            welcome,
            text="Monitor security activity, resource leaks and system access.",
            text_color=self.MUTED,
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w", pady=(4, 0))

        # Stats
        self.stats_frame = ctk.CTkFrame(
            page,
            fg_color="transparent"
        )

        self.stats_frame.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(0, 18)
        )

        for i in range(4):
            self.stats_frame.grid_columnconfigure(
                i,
                weight=1
            )

        stats = [
            ("Total Scans", "128", "+12 this week", self.ACCENT),
            ("Passed", "94", "73.4% success rate", self.SUCCESS),
            ("Security Alerts", "7", "Requires review", self.WARNING),
            ("Resource Leaks", "3", "Detected by analyzer", self.DANGER),
        ]

        self.stat_cards = []

        for i, (title, value, sub, color) in enumerate(stats):

            card = self.create_stat_card(
                self.stats_frame,
                title,
                value,
                sub,
                color
            )

            card.grid(
                row=0,
                column=i,
                sticky="nsew",
                padx=6
            )

            self.stat_cards.append(card)

        # Two-column area
        self.middle = ctk.CTkFrame(
            page,
            fg_color="transparent"
        )

        self.middle.grid(
            row=2,
            column=0,
            sticky="ew",
            pady=(0, 18)
        )

        self.middle.grid_columnconfigure(
            0,
            weight=3
        )

        self.middle.grid_columnconfigure(
            1,
            weight=2
        )

        self.build_activity_panel()
        self.build_health_panel()

        # Scan table
        self.build_scan_panel()

    # ==========================================================
    # STAT CARD
    # ==========================================================

    def create_stat_card(
        self,
        parent,
        title,
        value,
        subtitle,
        color
    ):

        card = ctk.CTkFrame(
            parent,
            fg_color=self.CARD,
            border_width=1,
            border_color=self.BORDER,
            corner_radius=14,
            height=110
        )

        card.grid_propagate(False)

        icon = ctk.CTkLabel(
            card,
            text="●",
            width=38,
            height=38,
            corner_radius=10,
            fg_color="#171D2A",
            text_color=color,
            font=ctk.CTkFont(size=13)
        )

        icon.place(
            x=16,
            y=18
        )

        ctk.CTkLabel(
            card,
            text=title,
            text_color=self.MUTED,
            font=ctk.CTkFont(size=10)
        ).place(
            x=65,
            y=15
        )

        ctk.CTkLabel(
            card,
            text=value,
            text_color=self.TEXT,
            font=ctk.CTkFont(
                size=25,
                weight="bold"
            )
        ).place(
            x=65,
            y=34
        )

        ctk.CTkLabel(
            card,
            text=subtitle,
            text_color=self.MUTED,
            font=ctk.CTkFont(size=8)
        ).place(
            x=65,
            y=73
        )

        card.bind(
            "<Enter>",
            lambda e: card.configure(
                fg_color=self.CARD_HOVER
            )
        )

        card.bind(
            "<Leave>",
            lambda e: card.configure(
                fg_color=self.CARD
            )
        )

        return card

    # ==========================================================
    # ACTIVITY PANEL
    # ==========================================================

    def build_activity_panel(self):

        panel = ctk.CTkFrame(
            self.middle,
            fg_color=self.CARD,
            border_width=1,
            border_color=self.BORDER,
            corner_radius=14
        )

        panel.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 8)
        )

        panel.grid_columnconfigure(
            0,
            weight=1
        )

        ctk.CTkLabel(
            panel,
            text="RECENT ACTIVITY",
            text_color=self.ACCENT,
            font=ctk.CTkFont(
                size=9,
                weight="bold"
            )
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=20,
            pady=(20, 3)
        )

        ctk.CTkLabel(
            panel,
            text="System Activity",
            text_color=self.TEXT,
            font=ctk.CTkFont(
                size=16,
                weight="bold"
            )
        ).grid(
            row=1,
            column=0,
            sticky="w",
            padx=20,
            pady=(0, 10)
        )

        activities = [
            ("✓", "Security scan completed", "Production repository", "2 min ago", self.SUCCESS),
            ("!", "Resource leak detected", "tests/branch_leak.py", "8 min ago", self.WARNING),
            ("→", "Administrator login", "Local security console", "15 min ago", self.ACCENT),
        ]

        for row, (icon, title, desc, time, color) in enumerate(activities, 2):

            item = ctk.CTkFrame(
                panel,
                fg_color="transparent"
            )

            item.grid(
                row=row,
                column=0,
                sticky="ew",
                padx=20,
                pady=6
            )

            item.grid_columnconfigure(
                1,
                weight=1
            )

            ctk.CTkLabel(
                item,
                text=icon,
                width=30,
                height=30,
                corner_radius=8,
                fg_color="#171D2A",
                text_color=color
            ).grid(
                row=0,
                column=0,
                rowspan=2,
                padx=(0, 10)
            )

            ctk.CTkLabel(
                item,
                text=title,
                text_color=self.TEXT,
                font=ctk.CTkFont(
                    size=11,
                    weight="bold"
                ),
                anchor="w"
            ).grid(
                row=0,
                column=1,
                sticky="ew"
            )

            ctk.CTkLabel(
                item,
                text=desc,
                text_color=self.MUTED,
                font=ctk.CTkFont(size=9),
                anchor="w"
            ).grid(
                row=1,
                column=1,
                sticky="ew"
            )

            ctk.CTkLabel(
                item,
                text=time,
                text_color=self.MUTED,
                font=ctk.CTkFont(size=8)
            ).grid(
                row=0,
                column=2,
                rowspan=2,
                padx=(10, 0)
            )

    # ==========================================================
    # HEALTH PANEL
    # ==========================================================

    def build_health_panel(self):

        panel = ctk.CTkFrame(
            self.middle,
            fg_color=self.CARD,
            border_width=1,
            border_color=self.BORDER,
            corner_radius=14
        )

        panel.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(8, 0)
        )

        ctk.CTkLabel(
            panel,
            text="SYSTEM HEALTH",
            text_color=self.ACCENT,
            font=ctk.CTkFont(
                size=9,
                weight="bold"
            )
        ).pack(
            anchor="w",
            padx=20,
            pady=(20, 3)
        )

        ctk.CTkLabel(
            panel,
            text="Security Status",
            text_color=self.TEXT,
            font=ctk.CTkFont(
                size=16,
                weight="bold"
            )
        ).pack(
            anchor="w",
            padx=20,
            pady=(0, 15)
        )

        systems = [
            "LeakGuard Analyzer",
            "Admin Authentication",
            "Audit Logging",
            "Local Server"
        ]

        for system in systems:

            row = ctk.CTkFrame(
                panel,
                fg_color="transparent"
            )

            row.pack(
                fill="x",
                padx=20,
                pady=7
            )

            ctk.CTkLabel(
                row,
                text=system,
                text_color=self.MUTED,
                font=ctk.CTkFont(size=10)
            ).pack(
                side="left"
            )

            ctk.CTkLabel(
                row,
                text="● ONLINE",
                text_color=self.SUCCESS,
                font=ctk.CTkFont(
                    size=8,
                    weight="bold"
                )
            ).pack(
                side="right"
            )

    # ==========================================================
    # SCAN PANEL
    # ==========================================================

    def build_scan_panel(self):

        panel = ctk.CTkFrame(
            self.pages["Dashboard"],
            fg_color=self.CARD,
            border_width=1,
            border_color=self.BORDER,
            corner_radius=14
        )

        panel.grid(
            row=3,
            column=0,
            sticky="ew"
        )

        panel.grid_columnconfigure(
            0,
            weight=1
        )

        header = ctk.CTkFrame(
            panel,
            fg_color="transparent"
        )

        header.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=20,
            pady=20
        )

        ctk.CTkLabel(
            header,
            text="LATEST SCAN RESULTS",
            text_color=self.ACCENT,
            font=ctk.CTkFont(
                size=9,
                weight="bold"
            )
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text="Resource Analysis",
            text_color=self.TEXT,
            font=ctk.CTkFont(
                size=16,
                weight="bold"
            )
        ).pack(
            side="left",
            pady=(4, 0)
        )

        ctk.CTkButton(
            header,
            text="Run Scan",
            width=100,
            height=32,
            fg_color=self.ACCENT,
            hover_color="#5969EA",
            command=self.run_scan
        ).pack(
            side="right"
        )

        rows = [
            ("LeakGuard", "Full Analysis", "PASSED", "0"),
            ("Test Repository", "Pull Request", "BLOCKED", "3"),
        ]

        for row, data in enumerate(rows, 1):

            repo, scan, result, issues = data

            line = ctk.CTkFrame(
                panel,
                fg_color="transparent"
            )

            line.grid(
                row=row,
                column=0,
                sticky="ew",
                padx=20,
                pady=6
            )

            line.grid_columnconfigure(
                0,
                weight=2
            )

            line.grid_columnconfigure(
                1,
                weight=2
            )

            line.grid_columnconfigure(
                2,
                weight=1
            )

            ctk.CTkLabel(
                line,
                text=repo,
                text_color=self.TEXT,
                anchor="w"
            ).grid(
                row=0,
                column=0,
                sticky="ew"
            )

            ctk.CTkLabel(
                line,
                text=scan,
                text_color=self.MUTED,
                anchor="w"
            ).grid(
                row=0,
                column=1,
                sticky="ew"
            )

            color = (
                self.SUCCESS
                if result == "PASSED"
                else self.DANGER
            )

            ctk.CTkLabel(
                line,
                text=result,
                text_color=color,
                font=ctk.CTkFont(
                    size=9,
                    weight="bold"
                )
            ).grid(
                row=0,
                column=2
            )

            ctk.CTkLabel(
                line,
                text=issues,
                text_color=self.TEXT
            ).grid(
                row=0,
                column=3,
                padx=15
            )

    # ==========================================================
    # OTHER PAGES
    # ==========================================================

    def build_simple_pages(self):

        page_data = {
            "Employees": (
                "EMPLOYEE MANAGEMENT",
                "Manage employees, roles and permissions."
            ),
            "Activity Logs": (
                "AUDIT TRAIL",
                "Review administrator and system activity."
            ),
            "Security Events": (
                "SECURITY MONITOR",
                "Review detected security events and resource leaks."
            ),
            "Reports": (
                "SECURITY REPORTS",
                "Generate and review LeakGuard analysis reports."
            ),
            "Settings": (
                "SYSTEM SETTINGS",
                "Configure administrator and dashboard preferences."
            )
        }

        for name, (eyebrow, description) in page_data.items():

            page = self.pages[name]

            ctk.CTkLabel(
                page,
                text=eyebrow,
                text_color=self.ACCENT,
                font=ctk.CTkFont(
                    size=9,
                    weight="bold"
                )
            ).pack(
                anchor="w",
                pady=(10, 5)
            )

            ctk.CTkLabel(
                page,
                text=name,
                text_color=self.TEXT,
                font=ctk.CTkFont(
                    size=28,
                    weight="bold"
                )
            ).pack(
                anchor="w"
            )

            ctk.CTkLabel(
                page,
                text=description,
                text_color=self.MUTED,
                font=ctk.CTkFont(size=12)
            ).pack(
                anchor="w",
                pady=(5, 25)
            )

            card = ctk.CTkFrame(
                page,
                fg_color=self.CARD,
                border_width=1,
                border_color=self.BORDER,
                corner_radius=14,
                height=180
            )

            card.pack(
                fill="x"
            )

            card.pack_propagate(False)

            ctk.CTkLabel(
                card,
                text=f"{name} module",
                text_color=self.TEXT,
                font=ctk.CTkFont(
                    size=18,
                    weight="bold"
                )
            ).pack(
                pady=(50, 5)
            )

            ctk.CTkLabel(
                card,
                text="Module ready for live system data.",
                text_color=self.MUTED
            ).pack()

    # ==========================================================
    # PAGE SWITCHING
    # ==========================================================

    def show_page(self, page_name):

        if page_name not in self.pages:
            return

        self.current_page = page_name

        # Show selected page
        self.pages[page_name].tkraise()

        self.page_title.configure(
            text=page_name
        )

        # Update navigation
        for name, button in self.nav_buttons.items():

            if name == page_name:

                button.configure(
                    fg_color=self.ACCENT,
                    text_color="white"
                )

            else:

                button.configure(
                    fg_color="transparent",
                    text_color=self.MUTED
                )

    # ==========================================================
    # SIDEBAR COLLAPSE
    # ==========================================================

    def toggle_sidebar(self):

        if self.sidebar_collapsed:

            self.sidebar.configure(
                width=250
            )

            self.logo_text.pack(
                side="left",
                padx=12
            )

            for name, button in self.nav_buttons.items():

                icon = button.cget("text")[0]

                button.configure(
                    text=f"{icon}    {name}"
                )

            self.sidebar_collapsed = False

        else:

            self.sidebar.configure(
                width=75
            )

            self.logo_text.pack_forget()

            for name, button in self.nav_buttons.items():

                icon = button.cget("text")[0]

                button.configure(
                    text=icon,
                    anchor="center"
                )

            self.sidebar_collapsed = True

    # ==========================================================
    # RESPONSIVE RESIZE
    # ==========================================================

    def on_resize(self, event):

        width = self.winfo_width()

        if width < 850:

            self.sidebar.configure(
                width=75
            )

        elif not self.sidebar_collapsed:

            self.sidebar.configure(
                width=250
            )

    # ==========================================================
    # CLOCK
    # ==========================================================

    def update_clock(self):

        now = datetime.now()

        self.clock_label.configure(
            text=now.strftime("%H:%M:%S")
        )

        self.after(
            1000,
            self.update_clock
        )

    # ==========================================================
    # ACTIONS
    # ==========================================================

    def run_scan(self):

        print("LeakGuard scan requested.")

    def logout(self):

        self.master.destroy()


def username_initial(username):

    if not username:
        return "A"

    return username[0].upper()