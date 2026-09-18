import os
import socket
import threading

from agent.heartbeat import HeartbeatAgent
from agent.file_monitor import FileMonitor
from agent.events import EventReporter


# =========================================================
# Configuration
# =========================================================

BACKEND_URL = os.getenv(
    "LEAKGUARD_BACKEND_URL",
    "http://127.0.0.1:8000"
)

AGENT_ID = os.getenv(
    "LEAKGUARD_AGENT_ID",
    "agent-test-001"
)

PROJECT_PATH = os.path.abspath(
    os.getenv(
        "LEAKGUARD_PROJECT_PATH",
        os.getcwd()
    )
)

# Logical project name.
# This MUST be the same for employees working on the
# same logical project, even if their folders are different.
PROJECT_NAME = os.getenv(
    "LEAKGUARD_PROJECT_NAME",
    os.path.basename(PROJECT_PATH)
)


def main():
    machine_name = socket.gethostname()

    # =====================================================
    # Validate project path
    # =====================================================

    if not os.path.isdir(PROJECT_PATH):
        print("[ERROR] Project path does not exist:")
        print(f"        {PROJECT_PATH}")
        return

    # =====================================================
    # Startup information
    # =====================================================

    print("=" * 60)
    print("LeakGuard Agent")
    print("=" * 60)
    print(f"Agent ID     : {AGENT_ID}")
    print(f"Machine      : {machine_name}")
    print(f"Backend      : {BACKEND_URL}")
    print(f"Project Name : {PROJECT_NAME}")
    print(f"Project Path : {PROJECT_PATH}")
    print("=" * 60)

    # =====================================================
    # 1. Heartbeat agent
    # =====================================================

    heartbeat_agent = HeartbeatAgent(
        backend_url=BACKEND_URL,
        agent_id=AGENT_ID,
        machine_name=machine_name,
        interval=5
    )

    heartbeat_thread = threading.Thread(
        target=heartbeat_agent.start,
        daemon=True,
        name="LeakGuard-Heartbeat"
    )

    heartbeat_thread.start()

    print("[OK] Heartbeat agent started")

    # =====================================================
    # 2. Event reporter
    # =====================================================

    reporter = EventReporter(
        backend_url=BACKEND_URL,
        agent_id=AGENT_ID
    )

    print("[OK] Event reporter initialized")

    # =====================================================
    # 3. File activity callback
    # =====================================================

    def handle_file_activity(activity):
        try:
            file_path = activity.get("file_path")
            file_name = activity.get("file_name")
            activity_type = activity.get("activity_type")

            print(
                f"[FILE] {activity_type:<8} "
                f"{file_name} "
                f"-> {file_path}"
            )

            reporter.send_file_activity(
                project_name=PROJECT_NAME,
                project_path=PROJECT_PATH,
                file_path=file_path,
                file_name=file_name,
                activity_type=activity_type,
                machine_name=machine_name
            )

        except Exception as error:
            print(
                f"[WARNING] "
                f"Failed to report file activity: {error}"
            )

    # =====================================================
    # 4. File monitor
    # =====================================================

    file_monitor = FileMonitor(
        project_path=PROJECT_PATH,
        on_activity=handle_file_activity,
        interval=3
    )

    monitor_thread = threading.Thread(
        target=file_monitor.start,
        daemon=True,
        name="LeakGuard-FileMonitor"
    )

    monitor_thread.start()

    print("[OK] File monitor started")
    print(f"[OK] Monitoring: {PROJECT_PATH}")
    print()
    print("Monitoring filesystem activity...")
    print("Press Ctrl+C to stop.")
    print()

    # =====================================================
    # 5. Keep agent alive
    # =====================================================

    try:
        while True:
            monitor_thread.join(timeout=1)

    except KeyboardInterrupt:
        print("\n[INFO] Shutting down LeakGuard agent...")

        # -------------------------------------------------
        # Stop file monitor
        # -------------------------------------------------

        try:
            file_monitor.stop()
        except Exception as error:
            print(
                f"[WARNING] "
                f"File monitor shutdown: {error}"
            )

        # -------------------------------------------------
        # Stop heartbeat
        # -------------------------------------------------

        try:
            heartbeat_agent.stop()
        except Exception as error:
            print(
                f"[WARNING] "
                f"Heartbeat shutdown: {error}"
            )

        print("[OK] LeakGuard agent stopped.")


if __name__ == "__main__":
    main()