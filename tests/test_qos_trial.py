import copy
import unittest
from unittest.mock import MagicMock

from controller import qos_trial as trial
from controller.executor import prepare_execution
from controller.validation import normalize_message, ValidationError


IMSI = '001010123456789'
IMEI = '12345678901234'


def state(flows=(), session=2, tmsi=101, extra_ue=False):
    ue = {'imsi':IMSI,'imeisv':IMEI+'01','rat_type':'NR','registered':True,
          '5g_tmsi':tmsi,'bearers':[{'apn':'internet','pdu_session_id':session,
          'sst':1,'qos_flow_id':1,'ip':'172.16.3.2',
          'dedicated':[{'qos_flow_id':qfi} for qfi in flows]}]}
    rows = [ue]
    if extra_ue:
        other = copy.deepcopy(ue)
        other['imeisv'] = '9876543210987601'
        rows.append(other)
    return {'ue_list':rows}


class TestQoSTrial(unittest.TestCase):
    def setUp(self):
        self.api = MagicMock()
        self.api.send.return_value = state(extra_ue=True)
        self.plan = trial.prepare(self.api,IMSI,IMEI,'internet',55000)
        self.api.reset_mock()
        self.events = []
        self.record = lambda event,payload:self.events.append((event,payload))
        self.receipt = {'status':'accepted_unverified','pdu_session_id':2,'qos_flow_id':3}

    def create(self, **kwargs):
        return trial.create(self.api,self.plan,confirm=lambda p:True,
                            record=self.record,policy_confirmed=True,**kwargs)

    def cleanup(self, **kwargs):
        return trial.cleanup(self.api,self.plan,self.receipt,confirm=lambda r:True,
                             record=self.record,policy_confirmed=True,**kwargs)

    def writes(self):
        return [c.args[0] for c in self.api.send.call_args_list
                if c.args[0]['message'] != 'ue_get']

    def test_identity_and_session_are_discovered_not_assumed(self):
        self.assertEqual(self.plan['before']['pdu_session_id'],2)
        self.assertEqual(self.plan['request']['imei'],IMEI)
        self.assertNotIn('pdu_session_id',self.plan['request'])

    def test_missing_or_existing_sessions_fail_closed(self):
        for reply in ({'ue_list':[]},state(flows=(2,)),state(session=0)):
            self.api.send.return_value = reply
            with self.assertRaises(ValidationError):
                trial.prepare(self.api,IMSI,IMEI,'internet',55000)
        self.assertEqual(self.writes(),[])

    def test_unknown_policy_or_cancel_never_sends_creation(self):
        with self.assertRaises(ValidationError):
            trial.create(self.api,self.plan,confirm=lambda p:True,record=self.record)
        result = trial.create(self.api,self.plan,confirm=lambda p:False,
                              record=self.record,policy_confirmed=True)
        self.assertEqual(result['status'],'cancelled')
        self.assertEqual(self.writes(),[])

    def test_guard_detects_change_during_approval(self):
        for reply in (state(tmsi=102),state(session=1),state(flows=(4,))):
            self.api.send.return_value = reply
            with self.assertRaises(ValidationError):
                self.create()
        self.assertEqual(self.writes(),[])

    def test_valid_receipt_is_not_full_qos_verification(self):
        self.api.send.side_effect = [state(),{'pdu_session_id':2,'qos_flow_id':3}]
        result = self.create()
        self.assertEqual(result['status'],'accepted_unverified')
        self.assertFalse(result['qos_verified'])
        self.assertEqual([e[0] for e in self.events],['creation_intent','creation_response'])
        self.assertEqual(len(self.writes()),1)

    def test_uncertain_creation_never_retries(self):
        self.api.send.side_effect = [state(),TimeoutError('lost reply')]
        with self.assertRaises(TimeoutError):
            self.create()
        self.assertEqual(len(self.writes()),1)
        self.assertEqual(self.events[0][0],'creation_intent')

    def test_invalid_receipts_not_used_for_cleanup(self):
        for reply in ({}, {'pdu_session_id':2,'qos_flow_id':1},
                      {'pdu_session_id':3,'qos_flow_id':3},
                      {'pdu_session_id':2,'qos_flow_id':True},
                      {'pdu_session_id':2,'qos_flow_id':3,'warning':'ignored'}):
            self.api.send.side_effect = [state(),reply]
            self.assertEqual(self.create()['status'],'unknown')
        bad = dict(self.receipt,qos_flow_id=1)
        with self.assertRaises(ValidationError):
            trial.cleanup_request(self.plan,bad)

    def test_cleanup_only_exact_new_flow_and_guarded_twice(self):
        self.api.send.side_effect = [state(flows=(3,)),state(flows=(3,)),{}]
        self.assertEqual(self.cleanup()['status'],'cleanup_sent')
        self.assertEqual(self.writes(),[{'message':'ue_deactivate_bearer','imsi':IMSI,
            'imei':IMEI,'pdu_session_id':2,'qos_flow_id':3}])

    def test_cleanup_conflict_after_approval_sends_nothing(self):
        self.api.send.side_effect = [state(flows=(3,)),state(flows=(3,4))]
        with self.assertRaises(ValidationError):
            self.cleanup()
        self.assertEqual(self.writes(),[])

    def test_cleanup_cancel_or_unknown_policy_sends_nothing(self):
        self.api.send.return_value = state(flows=(3,))
        with self.assertRaises(ValidationError):
            trial.cleanup(self.api,self.plan,self.receipt,confirm=lambda r:True,record=self.record)
        result = trial.cleanup(self.api,self.plan,self.receipt,confirm=lambda r:False,
                               record=self.record,policy_confirmed=True)
        self.assertEqual(result['status'],'cleanup_pending')
        self.assertEqual(self.writes(),[])

    def test_restoration_requires_same_original_session(self):
        self.api.send.return_value = state()
        self.assertTrue(trial.verify_cleanup(self.api,self.plan)['restoration_verified'])
        for reply in (state(flows=(3,)),state(tmsi=999),{'ue_list':[]}):
            self.api.send.return_value = reply
            with self.assertRaises(ValidationError):
                trial.verify_cleanup(self.api,self.plan)

    def test_new_operations_cannot_fall_through_uc1_executor(self):
        for request in (self.plan['request'],trial.cleanup_request(self.plan,self.receipt)):
            with self.assertRaisesRegex(ValidationError,'lifecycle runner'):
                prepare_execution(self.api,request)
        self.assertEqual(self.writes(),[])

    def test_schema_rejects_malformed_filters_and_out_of_scope_values(self):
        variants = []
        for name,value in [('qci',1),('imei','123'),('imsi',False)]:
            variants.append(dict(self.plan['request'],**{name:value}))
        request = copy.deepcopy(self.plan['request'])
        request['filters'][0]['precedence'] = 80
        variants.append(request)
        request = copy.deepcopy(self.plan['request'])
        request['filters'][0]['components'] = [{'remote_port':55000,'proto_id':17}]
        variants.append(request)
        for request in variants:
            with self.assertRaises(ValidationError):
                normalize_message(request)


if __name__ == '__main__':
    unittest.main()
