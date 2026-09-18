import os
import time
from typing import Callable


class FileMonitor:
    """
    Lightweight project file activity monitor.

    The monitor watches a project directory and detects
    filesystem changes without requiring an additional
    third-party dependency.

    It reports:
        - initial file discovery
        - file modifications
        - new files
        - deleted files

    It does NOT claim to know which file is currently open
    in VS Code or another editor. Exact "file opened" detection
    requires editor/application integration.
    """

    def __init__(
        self,
        project_path: str,
        on_activity: Callable[[dict], None],
        interval: int = 3
    ):
        self.project_path = os.path.abspath(
            os.path.expanduser(project_path)
        )

        self.on_activity = on_activity

        self.interval = max(1, interval)

        self.running = False

        # Stores:
        #
        # normalized_file_path -> metadata
        #
        # Example:
        # {
        #     "mtime": 1758012345.22,
        #     "size": 4521
        # }
        self.files = {}

    # ========================================================
    # PATH HELPERS
    # ========================================================

    @staticmethod
    def normalize_path(path: str) -> str:
        """
        Normalize path for reliable comparisons.
        """

        return os.path.normcase(
            os.path.normpath(
                os.path.abspath(path)
            )
        )

    def get_relative_path(
        self,
        file_path: str
    ) -> str:
        """
        Return the file path relative to the project directory.
        """

        try:
            relative = os.path.relpath(
                file_path,
                self.project_path
            )

            return relative.replace(
                os.sep,
                "/"
            )

        except ValueError:
            return os.path.basename(file_path)

    def get_project_name(self) -> str:
        """
        Use the project directory name as the project name.
        """

        name = os.path.basename(
            os.path.normpath(
                self.project_path
            )
        )

        return name or "Unknown Project"

    # ========================================================
    # FILE FILTERING
    # ========================================================

    def should_ignore(
        self,
        file_path: str
    ) -> bool:
        """
        Ignore files/directories that should not be monitored.
        """

        normalized = file_path.replace(
            "\\",
            "/"
        ).lower()

        ignored_parts = (
            "/.git/",
            "/__pycache__/",
            "/node_modules/",
            "/.venv/",
            "/venv/",
            "/env/",
            "/.idea/",
            "/.pytest_cache/",
            "/dist/",
            "/build/",
            "/leakguard.db/"
        )

        for part in ignored_parts:
            if part in normalized:
                return True

        ignored_names = (
            ".pyc",
            ".pyo",
            ".log",
            ".tmp",
            ".swp",
        )

        return normalized.endswith(
            ignored_names
        )

    # ========================================================
    # SCAN PROJECT
    # ========================================================

    def scan_files(self) -> dict:
        """
        Scan the project directory and return file metadata.
        """

        current_files = {}

        if not os.path.isdir(
            self.project_path
        ):
            return current_files

        for root, directories, filenames in os.walk(
            self.project_path
        ):

            # Prevent walking ignored directories.
            directories[:] = [
                directory
                for directory in directories
                if not self.should_ignore(
                    os.path.join(root, directory)
                )
            ]

            for filename in filenames:

                file_path = os.path.join(
                    root,
                    filename
                )

                if self.should_ignore(
                    file_path
                ):
                    continue

                try:
                    stat = os.stat(
                        file_path
                    )

                    normalized_path = (
                        self.normalize_path(
                            file_path
                        )
                    )

                    current_files[
                        normalized_path
                    ] = {
                        "file_path": file_path,
                        "file_name": filename,
                        "mtime": stat.st_mtime,
                        "size": stat.st_size,
                    }

                except (
                    PermissionError,
                    FileNotFoundError,
                    OSError
                ):
                    # A file can disappear while scanning.
                    # Ignore it safely.
                    continue

        return current_files

    # ========================================================
    # ACTIVITY CREATION
    # ========================================================

    def create_activity(
        self,
        file_data: dict,
        activity_type: str
    ) -> dict:
        """
        Create the standard activity payload consumed
        by the agent.
        """

        file_path = file_data["file_path"]

        return {
            "project_name": self.get_project_name(),

            "project_path": self.project_path,

            "file_path": file_path,

            "file_name": file_data["file_name"],

            "relative_path": self.get_relative_path(
                file_path
            ),

            "activity_type": activity_type,

            "timestamp": time.time(),
        }

    # ========================================================
    # INITIAL SCAN
    # ========================================================

    def initialize(self):
        """
        Take the first snapshot.

        We deliberately do NOT report every existing file
        as OPEN. Otherwise starting the agent in a project with
        500 files would create 500 fake activity events.
        """

        self.files = self.scan_files()

        print(
            f"[FILE MONITOR] "
            f"Project: {self.get_project_name()}"
        )

        print(
            f"[FILE MONITOR] "
            f"Path: {self.project_path}"
        )

        print(
            f"[FILE MONITOR] "
            f"Tracking {len(self.files)} files"
        )

    # ========================================================
    # CHECK FOR CHANGES
    # ========================================================

    def check_for_changes(self):
        """
        Compare the current filesystem state with the
        previous state.
        """

        current_files = self.scan_files()

        # ----------------------------------------------------
        # NEW OR MODIFIED FILES
        # ----------------------------------------------------

        for normalized_path, current in (
            current_files.items()
        ):

            previous = self.files.get(
                normalized_path
            )

            # New file
            if previous is None:

                activity = self.create_activity(
                    current,
                    "CREATED"
                )

                self.on_activity(
                    activity
                )

                continue

            # Existing file changed
            if (
                current["mtime"]
                != previous["mtime"]
                or current["size"]
                != previous["size"]
            ):

                activity = self.create_activity(
                    current,
                    "MODIFIED"
                )

                self.on_activity(
                    activity
                )

        # ----------------------------------------------------
        # DELETED FILES
        # ----------------------------------------------------

        for normalized_path, previous in (
            self.files.items()
        ):

            if normalized_path not in current_files:

                activity = self.create_activity(
                    previous,
                    "DELETED"
                )

                self.on_activity(
                    activity
                )

        self.files = current_files

    # ========================================================
    # MONITOR LOOP
    # ========================================================

    def start(self):
        """
        Start monitoring the project directory.

        This method blocks until stop() is called.
        """

        if self.running:
            return

        self.running = True

        self.initialize()

        print(
            "[FILE MONITOR] "
            "Monitoring started"
        )

        while self.running:

            try:

                self.check_for_changes()

            except Exception as error:

                print(
                    f"[FILE MONITOR ERROR] "
                    f"{error}"
                )

            time.sleep(
                self.interval
            )

    # ========================================================
    # STOP
    # ========================================================

    def stop(self):
        """
        Stop the monitoring loop.
        """

        self.running = False

        print(
            "[FILE MONITOR] "
            "Monitoring stopped"
        )