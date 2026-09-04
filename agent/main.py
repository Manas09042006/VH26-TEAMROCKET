import socket

from agent.heartbeat import HeartbeatAgent


BACKEND_URL = "http://127.0.0.1:8000"

AGENT_ID = "agent-test-001"


def main():
    machine_name = socket.gethostname()

    agent = HeartbeatAgent(
        backend_url=BACKEND_URL,
        agent_id=AGENT_ID,
        machine_name=machine_name,
        interval=5
    )

    agent.start()


if __name__ == "__main__":
    main()