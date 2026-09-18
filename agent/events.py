from agent.client import BackendClient


class EventReporter:
    def __init__(
        self,
        backend_url: str,
        agent_id: str
    ):
        self.client = BackendClient(backend_url)
        self.agent_id = agent_id

    # ========================================================
    # EXISTING SECURITY EVENT
    # ========================================================

    def send_event(
        self,
        event_type: str,
        description: str,
        severity: str = "INFO"
    ):
        """
        Send an existing LeakGuard security/activity event.

        This method is intentionally preserved so the existing
        analyzer and security-event pipeline continues to work.
        """

        try:
            url = (
                f"{self.client.backend_url}"
                f"/agents/event"
            )

            payload = {
                "agent_id": self.agent_id,
                "event_type": event_type,
                "description": description,
                "severity": severity
            }

            response = self.client.send_event_request(
                url,
                payload
            )

            print(
                f"[BACKEND EVENT] "
                f"{event_type} | severity={severity}"
            )

            return response

        except Exception as error:
            print(
                f"[BACKEND EVENT WARNING] "
                f"Could not report event: {error}"
            )

            return None

    # ========================================================
    # NEW PROJECT / FILE ACTIVITY
    # ========================================================

    def send_file_activity(
        self,
        project_name: str,
        project_path: str,
        file_path: str,
        file_name: str,
        activity_type: str = "OPEN",
        machine_name: str | None = None
    ):
        """
        Report project/file activity to the backend.

        Examples of activity_type:

            OPEN
            MODIFY
            SAVE
            CLOSE
        """

        try:
            response = self.client.send_file_activity(
                agent_id=self.agent_id,
                project_name=project_name,
                project_path=project_path,
                file_path=file_path,
                file_name=file_name,
                activity_type=activity_type,
                machine_name=machine_name
            )

            conflict = response.get(
                "activity",
                {}
            ).get(
                "conflict_detected",
                False
            )

            if conflict:
                print(
                    f"[FILE CONFLICT] "
                    f"{project_name}/{file_name}"
                )

            else:
                print(
                    f"[FILE ACTIVITY] "
                    f"{activity_type} | "
                    f"{project_name}/{file_name}"
                )

            return response

        except Exception as error:
            print(
                f"[FILE ACTIVITY WARNING] "
                f"Could not report file activity: {error}"
            )

            return None

    # ========================================================
    # NEW CLOSE FILE
    # ========================================================

    def close_file_activity(
        self,
        project_name: str,
        project_path: str,
        file_path: str,
        file_name: str,
        machine_name: str | None = None
    ):
        """
        Tell the backend that the employee has stopped
        working on a file.
        """

        try:
            response = self.client.close_file_activity(
                agent_id=self.agent_id,
                project_name=project_name,
                project_path=project_path,
                file_path=file_path,
                file_name=file_name,
                machine_name=machine_name
            )

            print(
                f"[FILE ACTIVITY] "
                f"CLOSE | "
                f"{project_name}/{file_name}"
            )

            return response

        except Exception as error:
            print(
                f"[FILE ACTIVITY WARNING] "
                f"Could not close file activity: {error}"
            )

            return None

    # ========================================================
    # EXISTING SCAN RESULT
    # ========================================================

    def send_scan_result(
        self,
        filename: str,
        leaks: list
    ):
        """
        Report the result of a LeakGuard source-code scan.

        Existing behavior preserved.
        """

        if leaks:
            descriptions = []

            for leak in leaks:

                variable = leak.get(
                    "variable",
                    "unknown"
                )

                resource_type = leak.get(
                    "resource_type",
                    "unknown"
                )

                open_line = leak.get(
                    "open_line",
                    "unknown"
                )

                leak_line = leak.get(
                    "leak_line",
                    "unknown"
                )

                reason = leak.get(
                    "reason",
                    "Resource was not released"
                )

                descriptions.append(
                    f"{resource_type} '{variable}' "
                    f"opened at line {open_line}, "
                    f"leak detected at line {leak_line}. "
                    f"{reason}"
                )

            description = (
                f"{len(leaks)} resource leak(s) detected "
                f"in {filename}. "
                + " | ".join(descriptions)
            )

            return self.send_event(
                event_type="RESOURCE_LEAK",
                description=description,
                severity="HIGH"
            )

        return self.send_event(
            event_type="SCAN_COMPLETED",
            description=(
                f"LeakGuard scan completed successfully "
                f"for {filename}. "
                f"No resource leaks detected."
            ),
            severity="INFO"
        )