"""One-UE NR flow lifecycle feasibility, not the multi-UE UC2 executor.

No throughput or complete QoS verification is inferred from ue_get. Creation
requires an empty dedicated-flow baseline and an operator-established release
policy or explicit approval of the documented-default assumption and its session
release risk. Cleanup targets only the ID returned for this recorded creation.
"""
import copy

from .validation import normalize_message, ValidationError


def send(api, request, timeout=5):
    reply = api.send(normalize_message(request), timeout=timeout)
    if not isinstance(reply, dict) or 'error' in reply:
        raise ValidationError('API returned an error or malformed response')
    return reply


def snapshot(api, imsi, imei, apn, timeout=5):
    reply = send(api, {'message':'ue_get'}, timeout)
    rows = reply.get('ue_list')
    if not isinstance(rows, list) or not all(isinstance(u,dict) for u in rows):
        raise ValidationError('Missing or malformed UE list')
    matches = [u for u in rows if u.get('imsi') == imsi
               and str(u.get('imeisv',''))[:14] == imei[:14]]
    if len(matches) != 1:
        raise ValidationError('IMSI + IMEI must identify exactly one UE')
    ue = matches[0]
    if ue.get('registered') is not True or ue.get('rat_type') != 'NR':
        raise ValidationError('Selected UE must be registered on NR')
    sessions = [s for s in ue.get('bearers',[]) if s.get('apn') == apn]
    if len(sessions) != 1:
        raise ValidationError('APN must identify exactly one current PDU session')
    session = sessions[0]
    for key, low, high in [('pdu_session_id',1,15),('qos_flow_id',1,63),('sst',0,255)]:
        if type(session.get(key)) is not int or not low <= session[key] <= high:
            raise ValidationError('Missing or invalid session field: '+key)
    if type(ue.get('5g_tmsi')) is not int or not isinstance(ue.get('imeisv'),str):
        raise ValidationError('Missing registration identity guard')
    if not session.get('ip') and not session.get('ipv6'):
        raise ValidationError('Session has no observable IP address')
    dedicated = session.get('dedicated',[])
    if not isinstance(dedicated,list) or any(
            not isinstance(f,dict) or type(f.get('qos_flow_id')) is not int
            or not 1 <= f['qos_flow_id'] <= 63 for f in dedicated):
        raise ValidationError('Malformed dedicated-flow list')
    ids = sorted(f['qos_flow_id'] for f in dedicated)
    if len(ids) != len(set(ids)) or session['qos_flow_id'] in ids:
        raise ValidationError('Ambiguous flow identities')
    return {'imsi':imsi, 'imei':imei, 'imeisv':ue['imeisv'],
            '5g_tmsi':ue['5g_tmsi'], 'apn':apn,
            'pdu_session_id':session['pdu_session_id'],
            'default_qfi':session['qos_flow_id'], 'sst':session['sst'],
            'sd':session.get('sd'), 'ip':session.get('ip'), 'ipv6':session.get('ipv6'),
            'dedicated':ids}


def same_session(before, after):
    if {k:v for k,v in before.items() if k != 'dedicated'} != {
            k:v for k,v in after.items() if k != 'dedicated'}:
        raise ValidationError('UE registration or session changed; no write is permitted')


def prepare(api, imsi, imei, apn, remote_port, five_qi=9, timeout=5):
    # Only a narrow test profile: non-GBR, no preemption, UDP to a chosen port.
    # These are explicit experiment settings, not general UC2 policy defaults.
    if apn.lower() == 'ims':
        raise ValidationError('This feasibility runner does not modify IMS sessions')
    normalize_message({'message':'ue_get','imsi':imsi,'imei':imei})
    before = snapshot(api, imsi, imei, apn, timeout)
    if before['dedicated']:
        raise ValidationError('Trial requires a session with no existing dedicated flows')
    request = {'message':'ue_activate_dedicated_bearer','imsi':imsi,'imei':imei,
               'apn':apn,'sst':before['sst'],'qci':five_qi,'priority_level':15,
               'pre_emption_capability':'shall_not_trigger_pre_emption',
               'pre_emption_vulnerability':'not_pre_emptable',
               'filters':[{'direction':'both','id':0,'precedence':200,
                           'components':[{'proto_id':17},{'remote_port':remote_port}]}]}
    if before['sd'] is not None:
        request['sd'] = before['sd']
    return {'request':normalize_message(request),'before':before,
            'verification':'Flow presence only; full QoS needs independent NAS/NGAP evidence.'}


def current(api, plan, timeout):
    b = plan['before']
    return snapshot(api,b['imsi'],b['imei'],b['apn'],timeout)


def create(api, plan, *, confirm, record, policy_confirmed=False, timeout=5):
    if policy_confirmed is not True:
        raise ValidationError('Release policy or documented-default risk must be approved before creation')
    request = normalize_message(plan['request'])
    if request['message'] != 'ue_activate_dedicated_bearer':
        raise ValidationError('Expected flow creation')
    if not confirm(copy.deepcopy(plan)):
        return {'status':'cancelled','write_sent':False}
    after_approval = current(api,plan,timeout)
    same_session(plan['before'],after_approval)
    if after_approval['dedicated']:
        raise ValidationError('Dedicated flows appeared after preflight; creation cancelled')
    # Persist intent before sending. Never retry creation after a timeout.
    record('creation_intent',request)
    reply = send(api,request,timeout)
    record('creation_response',reply)
    qfi = reply.get('qos_flow_id')
    if (type(qfi) is not int or not 1 <= qfi <= 63
            or qfi == plan['before']['default_qfi']
            or type(reply.get('pdu_session_id')) is not int
            or reply['pdu_session_id'] != plan['before']['pdu_session_id']
            or 'warning' in reply):
        return {'status':'unknown','qos_verified':False,
                'note':'No reliable creation receipt. Do not retry or guess a cleanup ID.'}
    return {'status':'accepted_unverified','qos_verified':False,'qos_flow_id':qfi,
            'pdu_session_id':reply['pdu_session_id']}


def cleanup_request(plan, receipt):
    qfi = receipt.get('qos_flow_id')
    b = plan['before']
    if (receipt.get('status') not in ('accepted_unverified','flow_present')
            or type(qfi) is not int or not 1 <= qfi <= 63
            or qfi == b['default_qfi'] or b['dedicated']
            or receipt.get('pdu_session_id') != b['pdu_session_id']):
        raise ValidationError('No safe creation receipt for cleanup')
    return normalize_message({'message':'ue_deactivate_bearer',
        'imsi':b['imsi'],'imei':b['imei'],'pdu_session_id':b['pdu_session_id'],
        'qos_flow_id':qfi})


def observe(api, plan, receipt, timeout=5):
    request = cleanup_request(plan,receipt)
    now = current(api,plan,timeout)
    same_session(plan['before'],now)
    expected = [request['qos_flow_id']]
    if now['dedicated'] != expected:
        raise ValidationError('Expected exactly the newly created flow; inspect before proceeding')
    return now


def cleanup(api, plan, receipt, *, confirm, record, policy_confirmed=False, timeout=5):
    if policy_confirmed is not True:
        raise ValidationError('Release policy or documented-default risk must be approved before cleanup')
    request = cleanup_request(plan,receipt)
    observe(api,plan,receipt,timeout)
    if not confirm(copy.deepcopy(request)):
        return {'status':'cleanup_pending','write_sent':False}
    observe(api,plan,receipt,timeout)  # Recheck after the human approval pause.
    record('cleanup_intent',request)
    reply = send(api,request,timeout)
    record('cleanup_response',reply)
    return {'status':'cleanup_sent','restoration_verified':False}


def verify_cleanup(api, plan, timeout=5):
    now = current(api,plan,timeout)
    same_session(plan['before'],now)
    if now['dedicated'] != plan['before']['dedicated']:
        raise ValidationError('Test flow remains or other flows changed')
    return {'status':'session_restored','restoration_verified':True,
            'qos_verified':False,'after':now}
