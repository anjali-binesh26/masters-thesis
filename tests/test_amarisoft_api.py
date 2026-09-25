import hashlib
import hmac
import json
import unittest
from unittest.mock import MagicMock, patch
import websocket
from controller.amarisoft_api import AmarisoftAPI, AmarisoftAPIError, ProtocolError
from controller.validation import BLOCKED_MESSAGES, ValidationError


class TestAPI(unittest.TestCase):
    def setUp(self):
        self.api = AmarisoftAPI()
        self.ws = MagicMock()
        self.api._ws = self.ws

    def echo(self, extra=None):
        request = json.loads(self.ws.send.call_args.args[0])
        return json.dumps(dict(message=request['message'],message_id=request['message_id'],**(extra or {})))

    def test_send_assigns_fresh_ids_without_mutating(self):
        self.ws.recv.side_effect = lambda:self.echo()
        request = {'message':'config_get','message_id':'caller'}
        one = self.api.send(request)
        two = self.api.send(request)
        self.assertNotEqual(one['message_id'],two['message_id'])
        self.assertEqual(request['message_id'],'caller')

    def test_stale_event_notification_skipped(self):
        replies = iter([lambda:json.dumps({'message':'config_get','message_id':'old'}),
                        lambda:json.dumps({'message':'ready'}),
                        lambda:self.echo({'notification':'pending'}),lambda:self.echo({'name':'MME'})])
        self.ws.recv.side_effect = lambda:next(replies)()
        self.assertEqual(self.api.send({'message':'config_get'})['name'],'MME')
        self.assertEqual(self.ws.recv.call_count,4)

    def test_correlated_error(self):
        self.ws.recv.side_effect = lambda:self.echo({'error':'rejected'})
        with self.assertRaises(AmarisoftAPIError):
            self.api.send({'message':'config_get'})

    def test_uncorrelated_error(self):
        self.ws.recv.return_value = '{"error":"bad request"}'
        with self.assertRaises(ProtocolError):
            self.api.send({'message':'config_get'})

    def test_malformed_and_closed_responses(self):
        for reply,exception in [('[]',ProtocolError),('not json',ProtocolError),('',ConnectionError)]:
            self.ws.recv.return_value = reply
            with self.assertRaises(exception):
                self.api.send({'message':'config_get'})

    def test_timeout_and_finite_timeouts(self):
        self.ws.recv.side_effect = websocket.WebSocketTimeoutException('timeout')
        with self.assertRaises(TimeoutError):
            self.api.send({'message':'config_get'})
        for timeout in (0,-1,True,float('inf'),float('nan')):
            with self.assertRaises(ValidationError):
                self.api.send({'message':'config_get'},timeout)

    def test_blocked_and_invalid_never_sent(self):
        for name in BLOCKED_MESSAGES:
            with self.assertRaises(PermissionError):
                self.api.send({'message':' '+name.upper()+' '})
        with self.assertRaises(ValidationError):
            self.api.send({'message':'config_set','qci':9})
        self.ws.send.assert_not_called()

    def test_nested_canonical_wire_payload(self):
        self.ws.recv.side_effect = lambda:self.echo()
        self.api.send({'message':'CONFIG_SET','parameters':{'t3512':600}})
        outgoing = json.loads(self.ws.send.call_args.args[0])
        self.assertEqual(outgoing['t3512'],600)
        self.assertNotIn('parameters',outgoing)

    @patch('controller.amarisoft_api.websocket.create_connection')
    def test_ready_handshake(self,create):
        api = AmarisoftAPI()
        create.return_value.recv.return_value = '{"message":"ready","type":"MME"}'
        api.connect()
        api.disconnect()
        create.return_value.close.assert_called_once()

    @patch('controller.amarisoft_api.websocket.create_connection')
    def test_missing_auth_password_closes(self,create):
        api = AmarisoftAPI()
        create.return_value.recv.return_value = '{"message":"authenticate","type":"MME"}'
        with self.assertRaises(ProtocolError):
            api.connect()
        create.return_value.close.assert_called_once()
        self.assertIsNone(api._ws)

    @patch('controller.amarisoft_api.websocket.create_connection')
    def test_authenticated_handshake(self,create):
        api = AmarisoftAPI(password='test-password')
        ws = create.return_value
        def reply():
            if not ws.send.called:
                return json.dumps({'message':'authenticate','type':'MME','name':'lab','challenge':'nonce'})
            sent = json.loads(ws.send.call_args.args[0])
            return json.dumps({'message':'authenticate','message_id':sent['message_id'],'ready':True})
        ws.recv.side_effect = reply
        api.connect()
        sent = json.loads(ws.send.call_args.args[0])
        expected = hmac.new(b'MME:test-password:lab',b'nonce',hashlib.sha256).hexdigest()
        self.assertEqual(sent['res'],expected)
        api.disconnect()

    def test_disconnected(self):
        self.api._ws = None
        with self.assertRaises(RuntimeError):
            self.api.send({'message':'config_get'})

    def test_wrong_message_for_id(self):
        def reply():
            value = json.loads(self.echo())
            value['message'] = 'ue_get'
            return json.dumps(value)
        self.ws.recv.side_effect = reply
        with self.assertRaises(ProtocolError):
            self.api.send({'message':'config_get'})


if __name__ == '__main__':
    unittest.main()
