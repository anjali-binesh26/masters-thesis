import json
import websocket


class AmarisoftAPI:
    """Reusable WebSocket client for the Amarisoft MME API."""

    def __init__(self, host: str = "192.168.20.1", port: int = 9000):
        self.url = f"ws://{host}:{port}"
        self._ws = None

    # ------------------------------------------------------------------
    # Connection Management
    # ------------------------------------------------------------------

    def connect(self):
        """Open the WebSocket connection."""
        self._ws = websocket.create_connection(self.url)

    def disconnect(self):
        """Close the WebSocket connection."""
        if self._ws:
            self._ws.close()
            self._ws = None

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _recv_message(self, expected_message: str) -> dict:
        """
        Receive messages until one matching `expected_message` is found.
        Returns the parsed JSON response.
        """
        while True:
            raw = self._ws.recv()
            response = json.loads(raw)
            if response.get("message") == expected_message:
                return response

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def send(self, request: dict) -> dict:
        """
        Serialize `request` to JSON, send it over the WebSocket,
        and return the matching parsed JSON response.
        """
        if not self._ws:
            raise RuntimeError("Not connected. Call connect() first.")

        expected_message = request.get("message")
        if not expected_message:
            raise ValueError("Request dictionary must contain a 'message' key.")

        self._ws.send(json.dumps(request))
        return self._recv_message(expected_message)