"""Serialized WebSocket transport with validation and strict reply correlation."""
import hashlib
import hmac
import json
import logging
import threading
import time
from uuid import uuid4

import websocket
from .validation import (BLOCKED_MESSAGES, normalize_message, positive_timeout,
                         strict_json)

logger = logging.getLogger(__name__)


class AmarisoftAPIError(RuntimeError):
    """An identified Amarisoft response rejected the request."""


class ProtocolError(RuntimeError):
    """Malformed response, unexpected handshake or uncorrelated server error."""


class AmarisoftAPI:
    def __init__(self, host='127.0.0.1', port=9000, password=None, audit=None):
        if not isinstance(host,str) or not host or any(c in host for c in '/?#@'):
            raise ValueError('host must be a hostname or IP address')
        if type(port) is not int or not 1 <= port <= 65535:
            raise ValueError('port must be in 1..65535')
        address = f'[{host}]' if ':' in host and not host.startswith('[') else host
        self.url = f'ws://{address}:{port}'
        self.password = password
        self.audit = audit
        self._ws = None
        self._lock = threading.RLock()

    def _record(self, event, payload):
        logger.info('%s %s',event,payload.get('message') if isinstance(payload,dict) else '')
        if self.audit:
            self.audit(event,payload)

    def _receive(self, deadline):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError('Remote API deadline exceeded')
        self._ws.settimeout(remaining)
        try:
            raw = self._ws.recv()
        except (websocket.WebSocketTimeoutException, TimeoutError) as exc:
            raise TimeoutError('Remote API response timed out') from exc
        if not raw:
            raise ConnectionError('Remote API closed the WebSocket')
        try:
            response = strict_json(raw)
        except ValueError as exc:
            raise ProtocolError('Server returned invalid JSON') from exc
        if not isinstance(response,dict):
            raise ProtocolError('Server response must be an object')
        return response

    def connect(self, timeout=5.0):
        positive_timeout(timeout)
        with self._lock:
            if self._ws is not None:
                raise RuntimeError('Already connected')
            deadline = time.monotonic() + timeout
            self._ws = websocket.create_connection(self.url,timeout=timeout)
            try:
                hello = self._receive(deadline)
                if hello.get('type') != 'MME':
                    raise ProtocolError('Expected an Amarisoft MME endpoint')
                if hello.get('message') == 'authenticate':
                    if not self.password:
                        raise ProtocolError('Server needs authentication; set AMARISOFT_PASSWORD')
                    if not all(isinstance(hello.get(k),str) for k in ('name','challenge')):
                        raise ProtocolError('Invalid authentication challenge')
                    key = f"{hello['type']}:{self.password}:{hello['name']}".encode()
                    response = hmac.new(key,hello['challenge'].encode(),hashlib.sha256).hexdigest()
                    identifier = uuid4().hex
                    self._ws.settimeout(max(0.001,deadline-time.monotonic()))
                    self._ws.send(json.dumps({'message':'authenticate','message_id':identifier,'res':response}))
                    authenticated = self._recv_message('authenticate',identifier,deadline)
                    if authenticated.get('ready') is not True:
                        raise ProtocolError('Authentication did not establish readiness')
                elif hello.get('message') != 'ready':
                    raise ProtocolError('Expected ready or authenticate handshake')
                self._record('connected',{'url':self.url})
            except BaseException:
                self.disconnect()
                raise

    def disconnect(self):
        with self._lock:
            ws, self._ws = self._ws, None
            if ws is not None:
                ws.close()

    def _recv_message(self, name, identifier, deadline):
        while True:
            response = self._receive(deadline)
            if response.get('message_id') != identifier:
                if 'error' in response and 'message_id' not in response:
                    raise ProtocolError(f"Uncorrelated server error: {response['error']}")
                continue
            if 'error' in response:
                raise AmarisoftAPIError(str(response['error']))
            if response.get('message') != name:
                raise ProtocolError('Reply ID matches but message name does not')
            if 'notification' in response:
                continue
            return response

    def send(self, request, timeout=5.0):
        positive_timeout(timeout)
        outgoing = normalize_message(request)
        # Always override caller IDs, including IDs produced by the LLM.
        outgoing['message_id'] = uuid4().hex
        with self._lock:
            if self._ws is None:
                raise RuntimeError('Not connected. Call connect() first.')
            deadline = time.monotonic() + timeout
            self._ws.settimeout(timeout)
            self._record('send',outgoing)
            try:
                self._ws.send(json.dumps(outgoing,allow_nan=False))
                response = self._recv_message(outgoing['message'],outgoing['message_id'],deadline)
            except (websocket.WebSocketTimeoutException, TimeoutError) as exc:
                self._record('timeout',{'message':outgoing['message'],'message_id':outgoing['message_id']})
                raise TimeoutError('Request outcome may be unknown after timeout') from exc
            self._record('response',response)
            return response
