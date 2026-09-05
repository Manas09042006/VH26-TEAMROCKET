import threading
import asyncio
import websockets


class AdminWebSocketClient:
    def __init__(self, on_message):
        self.on_message = on_message
        self.running = False
        self.thread = None

    def start(self):
        if self.running:
            return

        self.running = True

        self.thread = threading.Thread(
            target=self._run,
            daemon=True
        )

        self.thread.start()

    def _run(self):
        asyncio.run(self._connect())

    async def _connect(self):
        uri = "ws://127.0.0.1:8000/ws/admin"

        while self.running:
            try:
                async with websockets.connect(uri) as websocket:
                    print("[ADMIN WS] Connected")

                    while self.running:
                        message = await websocket.recv()

                        self.on_message(message)

            except Exception as error:
                print(
                    f"[ADMIN WS] Connection lost: {error}"
                )

                await asyncio.sleep(3)

    def stop(self):
        self.running = False