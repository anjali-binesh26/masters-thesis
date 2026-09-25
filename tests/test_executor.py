import copy
import unittest
from unittest.mock import MagicMock
from controller.executor import prepare_execution, execute_plan
from controller.validation import ValidationError


def flow(qfi=2):
    return {'qfi':qfi,'5qi':9,'priority_level':15,
            'pre_emption_capability':'shall_not_trigger_pre_emption',
            'pre_emption_vulnerability':'not_pre_emptable'}


def ue(imei='1234567890123401',timer=1800):
    return {'imsi':'001010123456789','imeisv':imei,'registered':True,'rat_type':'NR',
            't3512':timer,'bearers':[{'pdu_session_id':1,'qos_flow_id':1,
                                    'dedicated':[{'qos_flow_id':2},{'qos_flow_id':3}]}]}


def config(nas='debug',ip='debug'):
    return {'logs':{'layers':{'nas':{'level':nas},'ip':{'level':ip}}}}


class TestExecutor(unittest.TestCase):
    def setUp(self):
        self.api = MagicMock()
        self.request = {'message':'config_set',**config('info','info')}

    def prepare(self,request=None,baseline=None):
        return prepare_execution(self.api,request or self.request,baseline=baseline)

    def run_plan(self,plan,confirm=lambda summary:True,after_apply=None):
        return execute_plan(self.api,plan,confirm=confirm,after_apply=after_apply,
                            confirm_rollback=lambda summary:True)

    def test_partial_application_without_recovery_permission_never_rolls_back(self):
        for permission in (None,lambda summary:False):
            with self.subTest(permission=permission):
                self.api.reset_mock()
                self.api.send.side_effect = [config(),config(),{},config('info','debug')]
                result = execute_plan(self.api,self.prepare(),confirm=lambda summary:True,
                                      confirm_rollback=permission)
                self.assertEqual(result['status'],'recovery_pending')
                self.assertFalse(result['rollback_attempted'])
                writes = [c for c in self.api.send.call_args_list if c.args[0]['message']=='config_set']
                self.assertEqual(len(writes),1)

    def test_concurrent_change_during_rollback_confirmation_aborts(self):
        self.api.send.side_effect = [config(),config(),{},config('info','debug'),config('error','debug')]
        result = self.run_plan(self.prepare())
        self.assertEqual(result['status'],'conflict')
        self.assertEqual(len([c for c in self.api.send.call_args_list if c.args[0]['message']=='config_set']),1)

    def test_logging_success(self):
        self.api.send.side_effect = [config(),config(),{},config('info','info')]
        result = self.run_plan(self.prepare())
        self.assertTrue(result['verified'])
        self.assertEqual(self.api.send.call_count,4)

    def test_cancel_only_preflight_reads(self):
        self.api.send.return_value = config()
        plan = self.prepare()
        self.assertEqual(self.run_plan(plan,lambda summary:False)['status'],'cancelled')
        self.assertEqual(self.api.send.call_count,1)

    def test_partial_application_compensates_and_verifies(self):
        self.api.send.side_effect = [config(),config(),{},config('info','debug'),
                                    config('info','debug'),{},config()]
        result = self.run_plan(self.prepare())
        self.assertEqual(result['status'],'rolled_back')
        self.assertTrue(result['rollback_succeeded'])
        self.assertEqual(self.api.send.call_args_list[-2].args[0],{'message':'config_set',**config()})

    def test_rollback_acknowledgment_is_not_success(self):
        self.api.send.side_effect = [config(),config(),{},config('info','debug'),
                                    config('info','debug'),{},config('info','debug')]
        result = self.run_plan(self.prepare())
        self.assertEqual(result['status'],'rollback_failed')
        self.assertFalse(result['rollback_succeeded'])

    def test_rollback_timeout_can_still_be_verified(self):
        self.api.send.side_effect = [config(),config(),{},config('info','debug'),
                                    config('info','debug'),TimeoutError('lost'),config()]
        result = self.run_plan(self.prepare())
        self.assertTrue(result['rollback_succeeded'])

    def test_apply_timeout_reconciles_without_resending(self):
        self.api.send.side_effect = [config(),config(),TimeoutError('lost'),config('info','info')]
        self.assertTrue(self.run_plan(self.prepare())['verified'])
        self.assertEqual(self.api.send.call_count,4)

    def test_verification_failure_retries_only_read(self):
        self.api.send.side_effect = [config(),config(),{},TimeoutError('lost'),config('info','info')]
        self.assertTrue(self.run_plan(self.prepare())['verified'])

    def test_unknown_state_has_no_blind_rollback(self):
        self.api.send.side_effect = [config(),config(),{},TimeoutError('lost'),TimeoutError('lost')]
        result = self.run_plan(self.prepare())
        self.assertEqual(result['status'],'unknown')
        self.assertNotIn('rollback_attempted',result)

    def test_unexpected_third_party_value_not_overwritten(self):
        self.api.send.side_effect = [config(),config(),{},config('error','debug')]
        self.assertEqual(self.run_plan(self.prepare())['status'],'conflict')

    def test_concurrent_change_before_apply_aborts(self):
        self.api.send.side_effect = [config(),config('error','debug')]
        with self.assertRaises(ValidationError):
            self.run_plan(self.prepare())
        self.assertEqual(self.api.send.call_count,2)

    def test_unobservable_logging_is_rejected(self):
        self.api.send.return_value = {}
        with self.assertRaises(ValidationError):
            self.prepare()

    def test_locked_logging_is_rejected(self):
        self.api.send.return_value = {'logs':{'locked':True}}
        with self.assertRaises(ValidationError):
            self.prepare()

    def test_scalar_without_readback_needs_baseline(self):
        self.api.send.return_value = {}
        with self.assertRaises(ValidationError):
            self.prepare({'message':'config_set','relative_capacity':100})

    def test_scalar_baseline_does_not_imply_verification(self):
        self.api.send.side_effect = [{},{},{}]
        plan = self.prepare({'message':'config_set','relative_capacity':100},
                            {'message':'config_set','relative_capacity':50})
        result = self.run_plan(plan)
        self.assertEqual(result['status'],'accepted_unverified')
        self.assertFalse(result['verified'])

    def test_invalid_compensation_baseline_aborts(self):
        self.api.send.return_value = {}
        with self.assertRaises(ValidationError):
            self.prepare({'message':'config_set','relative_capacity':100},
                         {'message':'config_set','relative_capacity':999})

    def test_timer_two_shared_imsi_devices(self):
        before = [ue(),ue('9876543210987601')]
        after = [ue(timer=600),ue('9876543210987601',600)]
        self.api.send.side_effect = [{},{'ue_list':before},{},{},{'ue_list':after}]
        plan = self.prepare({'message':'config_set','t3512':600},
                            {'message':'config_set','t3512':1800})
        callback = MagicMock(return_value=True)
        result = self.run_plan(plan,after_apply=callback)
        self.assertTrue(result['verified'])
        self.assertEqual(len(result['observed']),2)
        callback.assert_called_once()

    def test_timer_missing_second_device_not_success(self):
        self.api.send.side_effect = [{},{'ue_list':[ue(),ue('9876543210987601')]},
                                    {},{},{'ue_list':[ue(timer=600)]}]
        plan = self.prepare({'message':'config_set','t3512':600},
                            {'message':'config_set','t3512':1800})
        self.assertEqual(self.run_plan(plan,after_apply=lambda s:True)['status'],'unknown')

    def test_timer_waiting_is_not_success(self):
        self.api.send.side_effect = [{},{'ue_list':[ue()]},{},{}]
        plan = self.prepare({'message':'config_set','t3512':600},
                            {'message':'config_set','t3512':1800})
        result = self.run_plan(plan,after_apply=lambda s:False)
        self.assertEqual(result['status'],'pending_verification')
        self.assertFalse(result['verified'])

    def test_timer_override_reports_failure(self):
        self.api.send.side_effect = [{},{'ue_list':[ue()]},{},{},{'ue_list':[ue()]}]
        plan = self.prepare({'message':'config_set','t3512':600},
                            {'message':'config_set','t3512':1800})
        self.assertEqual(self.run_plan(plan,after_apply=lambda s:True)['status'],'verification_failed')

    def qos(self):
        return {'message':'ue_modify_pdu_session','imsi':'001010123456789',
                'imei':'12345678901234','pdu_session_id':1,'qos_flow':[flow(2),flow(3)]}

    def patch(self):
        return dict(self.qos(),qos_flow=[{'qfi':2,'5qi':8}])

    def test_qos_preserves_other_flow_and_unknown_unchanged_values(self):
        original = self.qos()
        before = copy.deepcopy(original)
        self.api.send.side_effect = [{'ue_list':[ue()]},{'ue_list':[ue()]},{}]
        plan = self.prepare(self.patch(),original)
        self.assertEqual(plan.request['qos_flow'][0]['5qi'],8)
        self.assertEqual(plan.request['qos_flow'][1],flow(3))
        self.assertEqual(original,before)
        result = self.run_plan(plan)
        self.assertEqual(result['status'],'accepted_unverified')
        self.assertFalse(result['verified'])
        self.assertEqual(result['compensation'],original)

    def test_qos_missing_baseline_does_not_send(self):
        with self.assertRaises(ValidationError):
            self.prepare(self.patch())
        self.api.send.assert_not_called()

    def test_qos_default_flow_is_rejected(self):
        self.api.send.return_value = {'ue_list':[ue()]}
        with self.assertRaises(ValidationError):
            self.prepare(dict(self.patch(),qos_flow=[{'qfi':1,'5qi':8}]),self.qos())

    def test_qos_incomplete_baseline_is_rejected(self):
        self.api.send.return_value = {'ue_list':[ue()]}
        with self.assertRaises(ValidationError):
            self.prepare(self.patch(),dict(self.qos(),qos_flow=[flow(2)]))

    def test_qos_duplicate_imsi_requires_imei(self):
        original,patch = self.qos(),self.patch()
        original.pop('imei'); patch.pop('imei')
        self.api.send.return_value = {'ue_list':[ue(),ue('9876543210987601')]}
        with self.assertRaises(ValidationError):
            self.prepare(patch,original)

    def test_qos_session_changed_during_confirmation(self):
        changed = ue()
        changed['bearers'][0]['dedicated'] = [{'qos_flow_id':2}]
        self.api.send.side_effect = [{'ue_list':[ue()]},{'ue_list':[changed]}]
        with self.assertRaises(ValidationError):
            self.run_plan(self.prepare(self.patch(),self.qos()))
        self.assertEqual(self.api.send.call_count,2)

    def test_qos_non_nr_target_rejected(self):
        device = ue(); device['rat_type'] = 'LTE'
        self.api.send.return_value = {'ue_list':[device]}
        with self.assertRaises(ValidationError):
            self.prepare(self.patch(),self.qos())

    def test_qos_resource_transition_rejected(self):
        self.api.send.return_value = {'ue_list':[ue()]}
        with self.assertRaises(ValidationError):
            self.prepare(dict(self.patch(),qos_flow=[{'qfi':2,'5qi':1}]),self.qos())

    def test_read_only_does_not_ask_confirmation(self):
        self.api.send.return_value = {'ue_list':[]}
        confirm = MagicMock()
        result = self.run_plan(self.prepare({'message':'ue_get'}),confirm=confirm)
        self.assertEqual(result['status'],'read_complete')
        confirm.assert_not_called()


if __name__ == '__main__':
    unittest.main()
