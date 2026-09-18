import httpx


class BackendClient:
    def __init__(self, backend_url: str):
        self.backend_url = backend_url.rstrip("/")

    # ========================================================
    # HEARTBEAT
    # ========================================================

    def send_heartbeat(
        self,
        agent_id: str,
        machine_name: str
    ):
        url = f"{self.backend_url}/agents/heartbeat"

        payload = {
            "agent_id": agent_id,
            "machine_name": machine_name
        }

        response = httpx.post(
            url,
            json=payload,
            timeout=5
        )

        response.raise_for_status()

        return response.json()

    # ========================================================
    # EXISTING EVENT REQUEST
    # ========================================================

    def send_event_request(
        self,
        url: str,
        payload: dict
    ):
        response = httpx.post(
            url,
            json=payload,
            timeout=5
        )

        response.raise_for_status()

        return response.json()

    # ========================================================
    # NEW FILE ACTIVITY
    # ========================================================

    def send_file_activity(
        self,
        agent_id: str,
        project_name: str,
        project_path: str,
        file_path: str,
        file_name: str,
        activity_type: str = "OPEN",
        machine_name: str | None = None
    ):
        """
        Send project/file activity to the backend.

        This is intentionally separate from send_event_request()
        so the existing security-event system is not affected.
        """

        url = (
            f"{self.backend_url}"
            f"/agents/file-activity"
        )

        payload = {
            "agent_id": agent_id,
            "project_name": project_name,
            "project_path": project_path,
            "file_path": file_path,
            "file_name": file_name,
            "activity_type": activity_type,
            "machine_name": machine_name
        }

        response = httpx.post(
            url,
            json=payload,
            timeout=5
        )

        response.raise_for_status()

        return response.json()

    # ========================================================
    # CLOSE FILE ACTIVITY
    # ========================================================

    def close_file_activity(
        self,
        agent_id: str,
        project_name: str,
        project_path: str,
        file_path: str,
        file_name: str,
        machine_name: str | None = None
    ):
        """
        Tell the backend that the employee is no longer
        actively working on a file.
        """

        url = (
            f"{self.backend_url}"
            f"/agents/file-activity/close"
        )

        payload = {
            "agent_id": agent_id,
            "project_name": project_name,
            "project_path": project_path,
            "file_path": file_path,
            "file_name": file_name,
            "activity_type": "CLOSE",
            "machine_name": machine_name
        }

        response = httpx.post(
            url,
            json=payload,
            timeout=5
        )

        response.raise_for_status()

        return response.json()