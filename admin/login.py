import customtkinter as ctk
from tkinter import messagebox


class LoginWindow:
    def __init__(self, root, on_success):
        self.root = root
        self.on_success = on_success

        self.root.title("LeakGuard | Secure Administration")
        self.root.geometry("480x620")
        self.root.minsize(440, 580)

        self.root.configure(fg_color="#070B12")

        self.build_ui()

    def build_ui(self):

        # Main container
        container = ctk.CTkFrame(
            self.root,
            fg_color="#070B12"
        )
        container.pack(
            fill="both",
            expand=True,
            padx=45,
            pady=35
        )

        # Logo
        logo = ctk.CTkLabel(
            container,
            text="◈",
            font=ctk.CTkFont(
                family="Segoe UI",
                size=52,
                weight="bold"
            ),
            text_color="#5CE1E6"
        )
        logo.pack(pady=(20, 0))

        title = ctk.CTkLabel(
            container,
            text="LEAKGUARD",
            font=ctk.CTkFont(
                family="Segoe UI",
                size=30,
                weight="bold"
            ),
            text_color="#F2F7FA"
        )
        title.pack()

        subtitle = ctk.CTkLabel(
            container,
            text="SECURITY ADMINISTRATION CONSOLE",
            font=ctk.CTkFont(
                family="Consolas",
                size=10,
                weight="bold"
            ),
            text_color="#5CE1E6"
        )
        subtitle.pack(pady=(2, 35))

        # Login card
        card = ctk.CTkFrame(
            container,
            corner_radius=18,
            fg_color="#101722",
            border_width=1,
            border_color="#203040"
        )

        card.pack(
            fill="x",
            padx=5
        )

        heading = ctk.CTkLabel(
            card,
            text="Administrator Access",
            font=ctk.CTkFont(
                size=19,
                weight="bold"
            ),
            text_color="#FFFFFF"
        )
        heading.pack(
            anchor="w",
            padx=28,
            pady=(28, 4)
        )

        description = ctk.CTkLabel(
            card,
            text="Authenticate to access system controls",
            font=ctk.CTkFont(size=11),
            text_color="#718394"
        )
        description.pack(
            anchor="w",
            padx=28,
            pady=(0, 22)
        )

        # Username
        ctk.CTkLabel(
            card,
            text="ADMIN ID",
            font=ctk.CTkFont(
                size=10,
                weight="bold"
            ),
            text_color="#8FA4B5"
        ).pack(
            anchor="w",
            padx=28,
            pady=(5, 6)
        )

        self.username = ctk.CTkEntry(
            card,
            height=42,
            corner_radius=9,
            fg_color="#080D14",
            border_color="#243746",
            text_color="#FFFFFF",
            placeholder_text="Enter administrator ID",
            placeholder_text_color="#506170"
        )
        self.username.pack(
            fill="x",
            padx=28
        )

        # Password
        ctk.CTkLabel(
            card,
            text="PASSWORD",
            font=ctk.CTkFont(
                size=10,
                weight="bold"
            ),
            text_color="#8FA4B5"
        ).pack(
            anchor="w",
            padx=28,
            pady=(18, 6)
        )

        self.password = ctk.CTkEntry(
            card,
            height=42,
            corner_radius=9,
            fg_color="#080D14",
            border_color="#243746",
            text_color="#FFFFFF",
            placeholder_text="Enter password",
            placeholder_text_color="#506170",
            show="●"
        )
        self.password.pack(
            fill="x",
            padx=28
        )

        # Login button
        self.login_button = ctk.CTkButton(
            card,
            text="AUTHENTICATE  →",
            height=46,
            corner_radius=10,
            font=ctk.CTkFont(
                size=12,
                weight="bold"
            ),
            fg_color="#18A6A9",
            hover_color="#20C2C5",
            text_color="#FFFFFF",
            command=self.authenticate
        )

        self.login_button.pack(
            fill="x",
            padx=28,
            pady=(28, 28)
        )

        # Security status
        status = ctk.CTkLabel(
            container,
            text="●  ENCRYPTED ADMIN SESSION",
            font=ctk.CTkFont(
                family="Consolas",
                size=9
            ),
            text_color="#38D996"
        )

        status.pack(pady=(22, 0))

        self.username.focus()

        self.root.bind(
            "<Return>",
            lambda event: self.authenticate()
        )

    def authenticate(self):

        username = self.username.get().strip()
        password = self.password.get()

        if username == "admin" and password == "admin123":

            self.login_button.configure(
                text="ACCESS GRANTED ✓",
                fg_color="#168C6A"
            )

            self.root.after(
                500,
                lambda: self.on_success(username)
            )

        else:

            self.login_button.configure(
                text="ACCESS DENIED",
                fg_color="#B83A4B"
            )

            self.root.after(
                900,
                lambda: self.login_button.configure(
                    text="AUTHENTICATE  →",
                    fg_color="#18A6A9"
                )
            )

            messagebox.showerror(
                "Authentication Failed",
                "Invalid administrator credentials."
            )