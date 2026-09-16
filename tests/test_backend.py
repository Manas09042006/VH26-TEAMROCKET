import unittest
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database.database import Base, get_db
from backend.database.models import ActivityLog, AdminUser, Employee
from backend.main import app
from backend.services import employee_service, event_service, heartbeat_service
from backend.core.security import get_password_hash


# Use isolated in-memory SQLite database with StaticPool for unit tests
TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=TEST_ENGINE
)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


class TestBackend(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app.dependency_overrides[get_db] = override_get_db
        # Also patch SessionLocal in heartbeat_service for testing
        cls.original_session_local = heartbeat_service.SessionLocal
        heartbeat_service.SessionLocal = TestingSessionLocal

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        heartbeat_service.SessionLocal = cls.original_session_local

    def setUp(self):
        Base.metadata.create_all(bind=TEST_ENGINE)
        self.client = TestClient(app)
        self.db = TestingSessionLocal()

        # Seed admin user and test employee
        admin = AdminUser(
            username="admin",
            password_hash=get_password_hash("admin123"),
            role="ADMIN"
        )
        self.db.add(admin)

        employee = Employee(
            username="test.dev",
            display_name="Test Developer",
            role="DEVELOPER",
            machine_name="DEV-BOX-01",
            agent_id="agent-unit-001",
            status="OFFLINE"
        )
        self.db.add(employee)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=TEST_ENGINE)

    # -------------------------------------------------------------
    # 1. Health & Root Endpoints
    # -------------------------------------------------------------

    def test_root_endpoint(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["system"], "LeakGuard")
        self.assertEqual(data["status"], "online")

    def test_health_check(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "healthy"})

    # -------------------------------------------------------------
    # 2. Authentication
    # -------------------------------------------------------------

    def test_auth_login_success(self):
        response = self.client.post("/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("access_token", data)
        self.assertEqual(data["user"]["username"], "admin")

    def test_auth_login_failure(self):
        response = self.client.post("/auth/login", json={
            "username": "admin",
            "password": "wrongpassword"
        })
        self.assertEqual(response.status_code, 401)

    # -------------------------------------------------------------
    # 3. Employee CRUD
    # -------------------------------------------------------------

    def test_create_and_get_employees(self):
        # Create
        response = self.client.post("/employees/", json={
            "username": "alice.security",
            "display_name": "Alice Smith",
            "role": "SECURITY",
            "machine_name": "SEC-STATION",
            "agent_id": "agent-sec-999"
        })
        self.assertEqual(response.status_code, 201)
        created = response.json()["employee"]
        self.assertEqual(created["username"], "alice.security")

        # Duplicate check
        dup_response = self.client.post("/employees/", json={
            "username": "alice.security",
            "display_name": "Alice Duplicate"
        })
        self.assertEqual(dup_response.status_code, 409)

        # Get list
        list_response = self.client.get("/employees/")
        self.assertEqual(list_response.status_code, 200)
        data = list_response.json()
        self.assertGreaterEqual(data["count"], 2)

        # Get single
        emp_id = created["id"]
        single_response = self.client.get(f"/employees/{emp_id}")
        self.assertEqual(single_response.status_code, 200)
        self.assertEqual(single_response.json()["username"], "alice.security")

        # Update
        update_response = self.client.put(f"/employees/{emp_id}", json={
            "display_name": "Alice S. Senior"
        })
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(update_response.json()["employee"]["display_name"], "Alice S. Senior")

        # Delete
        delete_response = self.client.delete(f"/employees/{emp_id}")
        self.assertEqual(delete_response.status_code, 200)

        # Verify 404 after deletion
        not_found = self.client.get(f"/employees/{emp_id}")
        self.assertEqual(not_found.status_code, 404)

    # -------------------------------------------------------------
    # 4. Agent Heartbeat & Registration
    # -------------------------------------------------------------

    def test_agent_heartbeat_existing(self):
        response = self.client.post("/agents/heartbeat", json={
            "agent_id": "agent-unit-001",
            "machine_name": "NEW-DEV-BOX"
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ONLINE")
        self.assertIsNotNone(data["last_seen"])

    def test_agent_heartbeat_auto_register(self):
        response = self.client.post("/agents/heartbeat", json={
            "agent_id": "agent-new-discover-123",
            "machine_name": "AUTO-BOX"
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ONLINE")

        # Verify created in DB
        emp = self.db.query(Employee).filter(Employee.agent_id == "agent-new-discover-123").first()
        self.assertIsNotNone(emp)
        self.assertEqual(emp.status, "ONLINE")

    def test_agent_explicit_registration(self):
        response = self.client.post("/agents/register", json={
            "agent_id": "agent-explicit-01",
            "machine_name": "WORKSTATION-X",
            "display_name": "Custom Agent Name"
        })
        self.assertEqual(response.status_code, 200)
        emp = response.json()["employee"]
        self.assertEqual(emp["agent_id"], "agent-explicit-01")
        self.assertEqual(emp["display_name"], "Custom Agent Name")

    # -------------------------------------------------------------
    # 5. Agent Events & Admin Logs
    # -------------------------------------------------------------

    def test_agent_events_and_admin_logs(self):
        # Send info event
        info_resp = self.client.post("/agents/event", json={
            "agent_id": "agent-unit-001",
            "event_type": "SCAN_COMPLETED",
            "description": "File scanned, 0 leaks.",
            "severity": "INFO"
        })
        self.assertEqual(info_resp.status_code, 200)

        # Send high severity event (Leak)
        leak_resp = self.client.post("/agents/event", json={
            "agent_id": "agent-unit-001",
            "event_type": "RESOURCE_LEAK",
            "description": "File descriptor leak detected at line 42.",
            "severity": "HIGH"
        })
        self.assertEqual(leak_resp.status_code, 200)

        # Query admin logs
        logs_resp = self.client.get("/admin/logs")
        self.assertEqual(logs_resp.status_code, 200)
        logs_data = logs_resp.json()
        self.assertGreaterEqual(logs_data["count"], 2)

        # Query stats
        stats_resp = self.client.get("/admin/stats")
        self.assertEqual(stats_resp.status_code, 200)
        stats = stats_resp.json()
        self.assertGreaterEqual(stats["total_logs"], 2)
        self.assertGreaterEqual(stats["security_incidents"], 1)

    # -------------------------------------------------------------
    # 6. Heartbeat Timeout Transition
    # -------------------------------------------------------------

    def test_heartbeat_timeout_transition(self):
        import asyncio

        # Set employee last seen to 500 seconds ago and status ONLINE
        emp = self.db.query(Employee).filter(Employee.agent_id == "agent-unit-001").first()
        emp.status = "ONLINE"
        emp.last_seen = datetime.now(timezone.utc) - timedelta(seconds=500)
        self.db.commit()

        # Run check_employee_status
        asyncio.run(heartbeat_service.check_employee_status())

        # Verify status is now OFFLINE
        self.db.refresh(emp)
        self.assertEqual(emp.status, "OFFLINE")

    # -------------------------------------------------------------
    # 7. WebSocket Admin Connection & Broadcasting
    # -------------------------------------------------------------

    def test_websocket_broadcast_on_heartbeat(self):
        with self.client.websocket_connect("/ws/admin") as ws:
            # Employee is initially OFFLINE in setUp.
            # Sending heartbeat should change status to ONLINE and broadcast EMPLOYEE_STATUS.
            self.client.post("/agents/heartbeat", json={
                "agent_id": "agent-unit-001",
                "machine_name": "BOX-LIVE"
            })

            msg = ws.receive_json()
            self.assertEqual(msg["type"], "EMPLOYEE_STATUS")
            self.assertEqual(msg["agent_id"], "agent-unit-001")
            self.assertEqual(msg["status"], "ONLINE")
            self.assertEqual(msg["username"], "test.dev")
            self.assertEqual(msg["display_name"], "Test Developer")

    def test_websocket_broadcast_on_event(self):
        with self.client.websocket_connect("/ws/admin") as ws:
            # Trigger an event via REST API
            self.client.post("/agents/event", json={
                "agent_id": "agent-unit-001",
                "event_type": "RESOURCE_LEAK",
                "description": "WS broadcast test leak.",
                "severity": "HIGH"
            })

            # Should receive ACTIVITY_EVENT first
            msg1 = ws.receive_json()
            self.assertEqual(msg1["type"], "ACTIVITY_EVENT")

            # Should receive SECURITY_EVENT second (because severity is HIGH)
            msg2 = ws.receive_json()
            self.assertEqual(msg2["type"], "SECURITY_EVENT")
            self.assertEqual(msg2["severity"], "HIGH")


if __name__ == "__main__":
    unittest.main()
