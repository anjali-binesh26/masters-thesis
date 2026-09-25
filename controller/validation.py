"""A deliberately bounded Remote API policy for ltemme.pdf, version 2024-06-15.

Schemas describe supported operations, not lab test cases. Unknown fields fail
closed. Printed manual pages: messages 57-60, timers 62-63, UE 77-79,
EPS modification 86-87, PDU modification 87-88, GBR 33.
"""
import copy
import json
import math
import re

BLOCKED_MESSAGES = frozenset({'quit', 'log_reset', 'ue_del', 'ue_detach', 'me_del'})
READ_MESSAGES = frozenset({'config_get', 'ue_get', 'stats', 'log_get'})
LOG_LAYERS = ('nas ip s1ap ngap gtpu rx s6 cx s13 sgsap sbcap lcsap lppa '
              'n12 n13 n8 n17 n50 n5 nl1 nrppa epdg ikev2 ipsec n20').split()


class ValidationError(ValueError):
    pass


def integer(low=None, high=None, required=False):
    return dict(type=int, min=low, max=high, required=required)


def string(choices=None, pattern=None, required=False):
    return dict(type=str, choices=choices, pattern=pattern, required=required)


def obj(fields, required=False):
    return dict(type=dict, fields=fields, required=required)


LEVEL = string(['none', 'error', 'info', 'debug'])
# Manual log_options accepts none/error/info/debug (printed page 9).
CAPABILITY = string(['shall_not_trigger_pre_emption', 'may_trigger_pre_emption'])
VULNERABILITY = string(['not_pre_emptable', 'pre_emptable'])
IMSI = string(pattern=r'[0-9]{5,15}')
IMEI = string(pattern=r'[0-9]{14,15}')
GBR = obj({name: integer(1, required=True) for name in (
    'maximum_bitrate_dl', 'maximum_bitrate_ul',
    'guaranteed_bitrate_dl', 'guaranteed_bitrate_ul')})
QOS_CHARACTERISTICS = obj({
    'priority_level': integer(0,127), 'packet_delay_budget': integer(-1,1023),
    'extended_packet_delay_budget': integer(-1,109999),
    'packet_error_rate': string(pattern=r'[0-9]E-[0-9]'),
    'averaging_window': integer(-1,4095), 'maximum_data_burst_volume': integer(-1,2000000),
    'cn_packet_delay_budget_dl': integer(-1,1099990),
    'cn_packet_delay_budget_ul': integer(-1,1099990),
})
ARP = {'priority_level': integer(1,15), 'pre_emption_capability': CAPABILITY,
       'pre_emption_vulnerability': VULNERABILITY, 'gbr': GBR}
FLOW = dict(qfi=integer(0,63,True), **{'5qi':integer(1,254,True)},
            **{k:dict(v, required=k != 'gbr') for k,v in ARP.items()},
            **{'5qi_qos':QOS_CHARACTERISTICS})
CONFIG_FIELDS = {
    'logs': obj({'layers': obj({layer: obj({
        'level': LEVEL, 'max_size': integer(-1), 'key':dict(type=bool),
        'crypto':dict(type=bool), 'payload':dict(type=bool), 'verbose':dict(type=bool),
    }) for layer in LOG_LAYERS})}),
    'relative_capacity': integer(0,255),
    'authentication_mode': string(['auto','force','skip']),
    't3402': integer(-1), 't3412': integer(-1), 't3412_low_priority': integer(-1),
    't3512': integer(-1), 't3501': integer(1,30),
    'psm': dict(type=bool), 'mico_support':dict(type=bool),
}
MESSAGE_SCHEMAS = {
    'config_get': {}, 'stats': {},
    'ue_get': {'imsi':IMSI, 'nai':string(), 'imei':IMEI,
               'type':string(['3gpp','n3gpp','both']), 'radio_capabilities':dict(type=bool)},
    'config_set': CONFIG_FIELDS,
    'ue_modify_bearer': {'imsi':dict(IMSI,required=True), 'imei':IMEI,
        'erab_id':integer(5,15,True),
        'qos':obj(dict(qci=integer(1,255,True), **ARP), True)},
    'ue_modify_pdu_session': {'imsi':IMSI, 'nai':string(), 'imei':IMEI,
        'n3gpp':dict(type=bool), 'pdu_session_id':integer(1,15,True),
        'qos_flow':dict(type=list, items=FLOW, required=True)},
    'log_get': {'min':integer(0), 'max':integer(1,4096),
        'timeout':dict(type=(int,float),min=0,max=30), 'allow_empty':dict(type=bool),
        'ue_id':integer(0), 'layers':obj({k:LEVEL for k in LOG_LAYERS}),
        'short':dict(type=bool), 'headers':dict(type=bool),
        'max_size':integer(1,1048576),
        'start_timestamp':dict(type=(int,float),min=0),
        'end_timestamp':dict(type=(int,float),min=0)},
}


def strict_json(text):
    """Reject duplicate keys and non-JSON NaN/Infinity; never extract substrings."""
    def pairs(items):
        result = {}
        for key,value in items:
            if key in result:
                raise ValidationError(f'Duplicate JSON key: {key}')
            result[key] = value
        return result
    def constant(value):
        raise ValidationError(f'Invalid JSON constant: {value}')
    try:
        return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)
    except json.JSONDecodeError as exc:
        raise ValidationError(f'Invalid JSON: {exc}') from exc


def _fields(data, schema, path, partial=False):
    unknown = set(data) - set(schema)
    if unknown:
        raise ValidationError(f'{path}: unsupported fields {sorted(unknown)}')
    for key,rule in schema.items():
        if rule.get('required') and key not in data and not partial:
            raise ValidationError(f'{path}: missing required field {key}')
    for key,value in data.items():
        rule = schema[key]
        name = f'{path}.{key}'
        expected = rule['type']
        if not isinstance(value,expected) or (isinstance(value,bool) and expected is not bool):
            raise ValidationError(f'{name}: incorrect type')
        if isinstance(value,(int,float)) and not isinstance(value,bool):
            if isinstance(value,float) and not math.isfinite(value):
                raise ValidationError(f'{name}: must be finite')
            if rule.get('min') is not None and value < rule['min']:
                raise ValidationError(f'{name}: below minimum {rule["min"]}')
            if rule.get('max') is not None and value > rule['max']:
                raise ValidationError(f'{name}: exceeds maximum {rule["max"]}')
        if isinstance(value,str):
            if not value.strip():
                raise ValidationError(f'{name}: cannot be empty')
            if rule.get('choices') and value not in rule['choices']:
                raise ValidationError(f'{name}: expected one of {rule["choices"]}')
            if rule.get('pattern') and not re.fullmatch(rule['pattern'],value):
                raise ValidationError(f'{name}: invalid format')
        if isinstance(value,dict):
            if not value:
                raise ValidationError(f'{name}: empty object')
            _fields(value,rule['fields'],name,partial)
            if key == 'gbr' and not partial:
                for direction in ('ul','dl'):
                    if value[f'guaranteed_bitrate_{direction}'] > value[f'maximum_bitrate_{direction}']:
                        raise ValidationError(f'{name}: guaranteed bitrate exceeds maximum')
            if key == '5qi_qos' and not partial and 'packet_delay_budget' in value:
                if not {'priority_level','packet_error_rate'} <= set(value):
                    raise ValidationError(f'{name}: delay budget needs priority and error rate')
        if isinstance(value,list):
            if not value:
                raise ValidationError(f'{name}: empty replacement list is prohibited')
            for index,item in enumerate(value):
                if not isinstance(item,dict) or not item:
                    raise ValidationError(f'{name}[{index}]: expected nonempty object')
                _fields(item,rule['items'],f'{name}[{index}]',partial)


def normalize_message(request, *, qos_patch=False):
    if not isinstance(request,dict):
        raise ValidationError('Request must be a dictionary')
    result = copy.deepcopy(request)
    name = result.get('message')
    if not isinstance(name,str) or not name.strip():
        raise ValidationError("Request needs a nonempty 'message' string")
    name = name.strip().lower()
    if name in BLOCKED_MESSAGES:
        raise PermissionError(f'{name} is blocked by security policy')
    if name not in MESSAGE_SCHEMAS:
        raise ValidationError(f'Unsupported message: {name}')
    result['message'] = name
    if 'parameters' in result:
        params = result.pop('parameters')
        if not isinstance(params,dict):
            raise ValidationError('parameters must be an object')
        if set(params) & (set(result) | {'message','message_id','parameters'}):
            raise ValidationError('Conflicting or reserved nested parameters')
        result.update(params)
    if 'message_id' in result and (type(result['message_id']) not in (str,int)):
        raise ValidationError('message_id must be a string or integer')
    params = {k:v for k,v in result.items() if k not in ('message','message_id')}
    partial = qos_patch and name in ('ue_modify_bearer','ue_modify_pdu_session')
    _fields(params,MESSAGE_SCHEMAS[name],name,partial)
    if 'imsi' in params and 'nai' in params:
        raise ValidationError('Use imsi or nai, not both')
    if name == 'config_set' and not params:
        raise ValidationError('config_set needs at least one change')
    if name.startswith('ue_modify'):
        if not ({'imsi','nai'} & set(params)):
            raise ValidationError('A subscriber identifier is required')
        if name == 'ue_modify_bearer':
            if not {'imsi','erab_id','qos'} <= set(params):
                raise ValidationError('Bearer update needs imsi, erab_id and qos')
        else:
            if not {'pdu_session_id','qos_flow'} <= set(params):
                raise ValidationError('PDU update needs pdu_session_id and qos_flow')
            flows = params['qos_flow']
            ids = [f.get('qfi') for f in flows]
            if None in ids or len(ids) != len(set(ids)):
                raise ValidationError('Every flow needs a unique qfi')
            if partial and any(set(f) == {'qfi'} for f in flows):
                raise ValidationError('QoS patch must change a flow parameter')
    return result


def validate_message(request):
    normalize_message(request)


def positive_timeout(value):
    if type(value) not in (int,float) or not math.isfinite(value) or value <= 0:
        raise ValidationError('Timeout must be finite and positive')
    return value
