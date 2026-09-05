import time

from agent.client import BackendClient


class HeartbeatAgent:
    def __init__(
        self,
        backend_url: str,
        agent_id: str,
        machine_name: str,
        interval: int = 240
    ):
        self.client = BackendClient(backend_url)
        self.agent_id = agent_id
        self.machine_name = machine_name
        self.interval = interval

    def start(self):
        print("LeakGuard Employee Agent started")
        print(f"Agent ID      : {self.agent_id}")
        print(f"Machine       : {self.machine_name}")
        print(f"Backend       : {self.client.backend_url}")
        print(f"Interval      : {self.interval} seconds")
        print()

        while True:
            try:
                response = self.client.send_heartbeat(
                    self.agent_id,
                    self.machine_name
                )

                print(
                    f"[HEARTBEAT] "
                    f"status={response['status']} "
                    f"last_seen={response['last_seen']}"
                )

            except Exception as error:
                print(
                    f"[HEARTBEAT ERROR] {error}"
                )

            time.sleep(self.interval)