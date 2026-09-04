import customtkinter as ctk

from admin.login import LoginWindow
from admin.dashboard import DashboardWindow


class AdminApplication:

    def __init__(self):

        self.root = ctk.CTk()

        self.root.title(
            "LeakGuard | Security Administration"
        )

        self.root.geometry(
            "1280x760"
        )

        self.root.minsize(
            800,
            600
        )

        self.root.configure(
            fg_color="#080B12"
        )

        self.show_login()

    def show_login(self):

        self.login_window = LoginWindow(
            self.root,
            self.login_success
        )

    def login_success(self, username):

        for widget in self.root.winfo_children():
            widget.destroy()

        self.root.geometry(
            "1280x760"
        )

        self.root.minsize(
            800,
            600
        )

        self.dashboard = DashboardWindow(
            self.root,
            username
        )


if __name__ == "__main__":

    app = AdminApplication()

    app.root.mainloop()