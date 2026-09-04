from agent.client import BackendClient


class EventReporter:
    def __init__(self, backend_url: str, agent_id: str):
        self.client = BackendClient(backend_url)
        self.agent_id = agent_id

    def send_event(
        self,
        event_type: str,
        description: str,
        severity: str = "INFO"
    ):
        try:
            url = f"{self.client.backend_url}/agents/event"

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

    def send_scan_result(
        self,
        filename: str,
        leaks: list
    ):
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
                f"for {filename}. No resource leaks detected."
            ),
            severity="INFO"
        )