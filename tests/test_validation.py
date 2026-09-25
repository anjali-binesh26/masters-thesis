import copy
import unittest
from controller.validation import (ValidationError, normalize_message,
                                   validate_message, strict_json, BLOCKED_MESSAGES)


def flow(qfi=2, fiveqi=9):
    return {'qfi':qfi,'5qi':fiveqi,'priority_level':15,
            'pre_emption_capability':'shall_not_trigger_pre_emption',
            'pre_emption_vulnerability':'not_pre_emptable'}


class TestValidation(unittest.TestCase):
    def test_read_operations(self):
        for message in ('ue_get','config_get','stats'):
            validate_message({'message':message})
        validate_message({'message':'ue_get','imsi':'001010123456789','imei':'123456789012345','type':'3gpp'})
        validate_message({'message':'log_get','min':0,'max':100,'timeout':1,'allow_empty':True})

    def test_config_scalars_and_nested_logging(self):
        for request in (
            {'message':'config_set','relative_capacity':0},
            {'message':'config_set','relative_capacity':255},
            {'message':'config_set','authentication_mode':'auto'},
            {'message':'config_set','t3512':600},
            {'message':'config_set','t3412':-1},
            {'message':'config_set','mico_support':False},
            {'message':'config_set','logs':{'layers':{'nas':{'level':'debug','max_size':32}}}},
        ):
            validate_message(request)

    def test_normalization_is_nonmutating(self):
        source = {'message':' CONFIG_SET ','parameters':{'t3512':600}}
        original = copy.deepcopy(source)
        self.assertEqual(normalize_message(source),{'message':'config_set','t3512':600})
        self.assertEqual(source,original)

    def test_duplicate_envelopes_and_reserved_fields(self):
        for params in ({'t3512':600},{'message':'quit'},{'message_id':'x'},{'parameters':{}}):
            with self.assertRaises(ValidationError):
                normalize_message({'message':'config_set','t3512':600,'parameters':params})

    def test_invalid_values(self):
        for request in (
            [], {}, {'message':False}, {'message':'nonexistent'},
            {'message':'config_set'}, {'message':'config_set','5qi':9},
            {'message':'config_set','qci':9}, {'message':'config_set','log_options':'all.level=debug'},
            {'message':'config_set','relative_capacity':True},
            {'message':'config_set','relative_capacity':256},
            {'message':'config_set','relative_capacity':-1},
            {'message':'config_set','t3512':'600'},
            {'message':'config_set','t3512':-2},
            {'message':'config_set','t3501':31},
            {'message':'config_set','authentication_mode':'eps'},
            {'message':'config_set','logs':{'layers':{'nas':{'level':'superdebug'}}}},
            {'message':'config_set','logs':{'layers':{'all':{'level':'info'}}}},
            {'message':'config_set','logs':{'layers':{}}},
            {'message':'ue_get','imsi':''}, {'message':'ue_get','imsi':'abcd'},
            {'message':'ue_get','imsi':'00101','nai':'user@realm'},
            {'message':'ue_get','imei':'1234567890123456'},
            {'message':'ue_get','stats':True},
            {'message':'config_get','message_id':True},
            {'message':'log_get','timeout':float('nan')},
        ):
            with self.subTest(request=request), self.assertRaises(ValidationError):
                normalize_message(request)

    def test_blacklist_all_spellings(self):
        for name in BLOCKED_MESSAGES:
            for variant in (name,name.upper(),' '+name+' '):
                with self.assertRaises(PermissionError):
                    normalize_message({'message':variant})

    def test_strict_json(self):
        for text in ('{"x":1,"x":2}','{"x":NaN}','{} {}'):
            with self.assertRaises(ValidationError):
                strict_json(text)

    def test_full_qos_request(self):
        validate_message({'message':'ue_modify_pdu_session','imsi':'00101',
                          'pdu_session_id':1,'qos_flow':[flow()]})
        validate_message({'message':'ue_modify_bearer','imsi':'00101','erab_id':5,
                          'qos':{'qci':9}})

    def test_patch_is_not_wire_request(self):
        patch = {'message':'ue_modify_pdu_session','imsi':'00101',
                 'pdu_session_id':1,'qos_flow':[{'qfi':2,'5qi':8}]}
        normalize_message(patch,qos_patch=True)
        with self.assertRaises(ValidationError):
            normalize_message(patch)

    def test_qos_identifiers_and_ranges(self):
        for patch in (
            {'qos_flow':[]}, {'qos_flow':[{}]}, {'qos_flow':[{'5qi':8}]},
            {'qos_flow':[{'qfi':2}]}, {'qos_flow':[{'qfi':64,'5qi':8}]},
            {'qos_flow':[{'qfi':2,'5qi':255}]},
            {'qos_flow':[{'qfi':2,'5qi':8},{'qfi':2,'5qi':9}]},
            {'qos_flow':[{'qfi':2,'priority_level':0}]},
            {'pdu_session_id':0}, {'pdu_session_id':16}, {'imsi':''},
        ):
            request = dict(message='ue_modify_pdu_session',imsi='00101',pdu_session_id=1,
                           qos_flow=[{'qfi':2,'5qi':8}])
            request.update(patch)
            with self.subTest(patch=patch), self.assertRaises(ValidationError):
                normalize_message(request,qos_patch=True)

    def test_gbr_shape_and_relationship(self):
        valid = dict(maximum_bitrate_dl=200,maximum_bitrate_ul=200,
                     guaranteed_bitrate_dl=100,guaranteed_bitrate_ul=100)
        request = {'message':'ue_modify_bearer','imsi':'00101','erab_id':5,
                   'qos':{'qci':1,'gbr':valid}}
        validate_message(request)
        for bad in ({'ul_mbr':100},dict(valid,guaranteed_bitrate_dl=201),
                    dict(valid,maximum_bitrate_ul=-1),dict(valid,maximum_bitrate_ul=True)):
            request['qos']['gbr'] = bad
            with self.assertRaises(ValidationError):
                validate_message(request)


if __name__ == '__main__':
    unittest.main()
