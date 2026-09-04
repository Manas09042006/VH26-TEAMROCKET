import httpx


class BackendClient:
    def __init__(self, backend_url: str):
        self.backend_url = backend_url.rstrip("/")

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