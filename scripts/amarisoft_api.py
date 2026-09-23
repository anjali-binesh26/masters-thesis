import json
import logging
import time
import websocket

logger = logging.getLogger(__name__)

BLOCKED_MESSAGES = {"quit", "log_reset", "ue_del", "ue_detach", "me_del"}


class AmarisoftAPIError(Exception):
    """Custom exception raised when the Amarisoft API returns an error response."""
    pass


class AmarisoftAPI:
    """Reusable WebSocket client for the Amarisoft MME API."""

    def __init__(self, host: str = "192.168.20.1", port: int = 9000):
        self.url = f"ws://{host}:{port}"
        self._ws = None

    # ------------------------------------------------------------------
    # Connection Management
    # ------------------------------------------------------------------

    def connect(self, timeout: float = 5.0):
        """Open the WebSocket connection."""
        self._ws = websocket.create_connection(self.url, timeout=timeout)
        logger.info("Connected to %s", self.url)

    def disconnect(self):
        """Close the WebSocket connection."""
        if self._ws:
            self._ws.close()
            self._ws = None
            logger.info("Disconnected from %s", self.url)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _recv_message(self, expected_message: str, timeout: float = 5.0) -> dict:
        """
        Receive messages until one matching `expected_message` is found.
        Returns the parsed JSON response.
        Raises TimeoutError if no matching response arrives within `timeout` seconds.
        Raises AmarisoftAPIError if the response contains an 'error' key.
        """
        start_time = time.time()
        while True:
            elapsed = time.time() - start_time
            remaining = timeout - elapsed
            if remaining <= 0:
                logger.error(
                    "Timed out waiting for message '%s' after %s seconds.",
                    expected_message,
                    timeout,
                )
                raise TimeoutError(
                    f"Timed out after {timeout} seconds waiting for message '{expected_message}'."
                )

            if self._ws:
                self._ws.settimeout(remaining)

            try:
                raw = self._ws.recv()
            except Exception as e:
                if "timed out" in str(e).lower() or type(e).__name__ in (
                    "WebSocketTimeoutException",
                    "timeout",
                    "SocketTimeout",
                ):
                    logger.error(
                        "Timed out waiting for message '%s' after %s seconds.",
                        expected_message,
                        timeout,
                    )
                    raise TimeoutError(
                        f"Timed out after {timeout} seconds waiting for message '{expected_message}'."
                    ) from e
                raise

            response = json.loads(raw)

            # Check for error key in parsed response
            if response.get("message") == expected_message:
                if "error" in response:
                    logger.error(
                        "AmarisoftAPIError for message '%s': %s",
                        expected_message,
                        response["error"],
                    )
                    raise AmarisoftAPIError(response["error"])
                return response
            elif "error" in response and "message" not in response:
                logger.error(
                    "AmarisoftAPIError for message '%s': %s",
                    expected_message,
                    response["error"],
                )
                raise AmarisoftAPIError(response["error"])

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def send(self, request: dict, timeout: float = 5.0) -> dict:
        """
        Serialize `request` to JSON, send it over the WebSocket,
        and return the matching parsed JSON response.
        Raises PermissionError if the message is in BLOCKED_MESSAGES.
        """
        if not self._ws:
            raise RuntimeError("Not connected. Call connect() first.")

        if not isinstance(request, dict):
            raise TypeError("Request must be a dictionary.")

        raw_message = request.get("message")
        if not raw_message or not isinstance(raw_message, str):
            raise ValueError("Request dictionary must contain a valid string 'message' key.")

        message_name = raw_message.strip().lower()
        if message_name in BLOCKED_MESSAGES or raw_message in BLOCKED_MESSAGES:
            logger.warning(
                "Message '%s' is blocked and was refused.", raw_message
            )
            raise PermissionError(
                f"Operation '{raw_message}' is blocked by security policy."
            )

        logger.info("Sending message: %s", raw_message)
        logger.debug("Outgoing payload: %s", request)
        self._ws.send(json.dumps(request))
        return self._recv_message(raw_message, timeout=timeout)