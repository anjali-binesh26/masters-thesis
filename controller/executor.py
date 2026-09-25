"""Operation adapters for validated JSON changes, with honest verification status.

No test-specific values or natural-language parsing live here. LLM proposals
cannot supply verification code, compensation commands, or trusted baselines.
The operator confirms the actual payload and recovery policy after preflight.
Shared Callbox changes are not atomic; coordinate access with lab colleagues.
"""
import copy
from dataclasses import dataclass, field

from .validation import (READ_MESSAGES, ValidationError, normalize_message,
                         positive_timeout)


class ExecutionError(RuntimeError):
    def __init__(self, message, *, details=None, rollback_attempted=False,
                 rollback_succeeded=False, state_unknown=False):
        super().__init__(message)
        self.details = details or {}
        self.rollback_attempted = rollback_attempted
        self.rollback_succeeded = rollback_succeeded
        self.state_unknown = state_unknown


@dataclass
class ExecutionPlan:
    request: dict
    compensation: dict | None = None
    mode: str = 'read'
    before: dict = field(default_factory=dict)
    expected: dict = field(default_factory=dict)
    targets: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    guard: dict = field(default_factory=dict)

    def summary(self):
        return {k:copy.deepcopy(getattr(self,k)) for k in (
            'request','compensation','mode','before','expected','targets','warnings')}


def _send(api, request, timeout):
    # Transport owns correlation; validate again to cover alternative API clients.
    outgoing = normalize_message(request)
    response = api.send(outgoing,timeout=timeout)
    if not isinstance(response,dict) or 'error' in response:
        raise ExecutionError('API returned an error or malformed response',details={'response':response})
    return response


def _leaves(data, prefix=()):
    result = {}
    for key,value in data.items():
        path = prefix + (key,)
        if isinstance(value,dict):
            result.update(_leaves(value,path))
        else:
            result['.'.join(path)] = copy.deepcopy(value)
    return result


def _get(data, path):
    for part in path.split('.'):
        data = data[part]
    return copy.deepcopy(data)


def _put(data, path, value):
    parts = path.split('.')
    for part in parts[:-1]:
        data = data.setdefault(part,{})
    data[parts[-1]] = copy.deepcopy(value)


def _params(request):
    return {k:v for k,v in request.items() if k not in ('message','message_id')}


def _ue_key(ue):
    # IMEISV distinguishes the two lab devices even if their IMSIs are equal.
    key = (ue.get('imsi'),ue.get('nai'),ue.get('imeisv'))
    if not key[2] or not (key[0] or key[1]):
        raise ValidationError('UE has no stable subscriber + IMEISV identity')
    return key


def _ues(api, timeout):
    response = _send(api,{'message':'ue_get'},timeout)
    rows = response.get('ue_list')
    if not isinstance(rows,list) or not all(isinstance(u,dict) for u in rows):
        raise ValidationError('ue_get did not return a valid ue_list')
    return rows


def _select_ue(rows, request):
    matches = []
    for ue in rows:
        if any(ue.get(k) != request[k] for k in ('imsi','nai') if k in request):
            continue
        # IMEI and IMEISV share the 14-digit equipment identity; the final
        # IMEI check digit is not the IMEISV software-version suffix.
        if 'imei' in request and str(ue.get('imeisv',''))[:14] != request['imei'][:14]:
            continue
        matches.append(ue)
    if len(matches) != 1:
        raise ValidationError('Target must resolve to exactly one UE; provide its IMEI if needed')
    ue = matches[0]
    _ue_key(ue)
    if ue.get('registered') is not True:
        raise ValidationError('Target UE is not registered')
    return ue


def _session(ue, request):
    if request['message'] == 'ue_modify_pdu_session':
        if ue.get('rat_type') != 'NR':
            raise ValidationError('PDU QoS adapter supports registered NR UEs only')
        sessions = [b for b in ue.get('bearers',[]) if b.get('pdu_session_id') == request['pdu_session_id']]
        if len(sessions) != 1:
            raise ValidationError('PDU session is absent or ambiguous')
        return sessions[0]
    if ue.get('rat_type') not in ('LTE','NBIOT'):
        raise ValidationError('ue_modify_bearer is an EPS operation, not a 5G QoS operation')
    candidates = []
    for bearer in ue.get('bearers',[]):
        candidates.extend([bearer] + bearer.get('dedicated',[]))
    matches = [b for b in candidates if b.get('erab_id') == request['erab_id']]
    if len(matches) != 1:
        raise ValidationError('EPS bearer is absent or ambiguous')
    return matches[0]


def _qos_guard(ue, request):
    session = _session(ue,request)
    return {'identity':_ue_key(ue),'session':request.get('pdu_session_id',request.get('erab_id')),
            'flows':sorted(b['qos_flow_id'] for b in session.get('dedicated',[]))}


def _prepare_qos(api, request, baseline, timeout):
    if baseline is None:
        raise ValidationError('QoS requires --baseline with the complete current QoS request, established by the operator')
    original = normalize_message(baseline)
    identity_fields = ('message','imsi','nai','imei','pdu_session_id','erab_id','n3gpp')
    if any(original.get(k) != request.get(k) for k in identity_fields):
        raise ValidationError('QoS baseline must match the exact requested UE/session identifiers')
    if request.get('n3gpp'):
        raise ValidationError('Non-3GPP QoS needs a separate state adapter')
    ue = _select_ue(_ues(api,timeout),request)
    guard = _qos_guard(ue,request)
    effective = copy.deepcopy(original)
    if request['message'] == 'ue_modify_bearer':
        if not {'qci','priority_level','pre_emption_capability','pre_emption_vulnerability'} <= set(original['qos']):
            raise ValidationError('EPS baseline must contain QCI and complete ARP to avoid implicit default changes')
    if request['message'] == 'ue_modify_pdu_session':
        flows = {f['qfi']: f for f in effective['qos_flow']}
        if set(flows) != set(guard['flows']):
            raise ValidationError('Baseline must contain every current non-default flow, and no default or nonexistent flow')
        for patch in request['qos_flow']:
            if patch['qfi'] not in flows:
                raise ValidationError('Only existing non-default QoS flows can be updated')
            old = flows[patch['qfi']]
            if 'gbr' in patch and 'gbr' not in old:
                raise ValidationError('GBR changes require an existing GBR baseline; resource-type conversions are not supported')
            if '5qi' in patch and patch['5qi'] != old['5qi']:
                # Initial operational policy: no resource-type conversion or
                # arbitrary dynamic 5QI definitions without a qualified adapter.
                if old['5qi'] not in range(5,10) or patch['5qi'] not in range(5,10) or 'gbr' in old:
                    raise ValidationError('5QI changes currently support non-GBR profiles 5..9 only; other transitions need a qualified policy')
            for key,value in patch.items():
                if isinstance(value,dict):
                    old.setdefault(key,{}).update(value)
                else:
                    old[key] = value
    else:
        old = effective['qos']
        patch = request['qos']
        if 'gbr' in patch and 'gbr' not in old:
            raise ValidationError('GBR changes require an existing GBR baseline')
        if 'qci' in patch and patch['qci'] != old['qci']:
            if old['qci'] not in range(5,10) or patch['qci'] not in range(5,10) or 'gbr' in old:
                raise ValidationError('QCI changes currently support non-GBR profiles 5..9 only')
        for key,value in patch.items():
            if isinstance(value,dict):
                old.setdefault(key,{}).update(value)
            else:
                old[key] = value
    effective = normalize_message(effective)
    return ExecutionPlan(effective,original,'qos_manual',targets=[list(_ue_key(ue))],guard=guard,
        warnings=['Baseline is operator-supplied, not a live QoS read-back.',
                  'Complete non-default flow list is preserved. Default flow and QoS rules are not modified.',
                  'API acknowledgment is NOT proof of QoS application. Inspect NAS/NGAP evidence.',
                  'No automatic rollback without observable QoS state; compensation is supplied for operator review.'])


def prepare_execution(api, request, *, baseline=None, timeout=5.0):
    """Read-only preflight. baseline is local operator input, never LLM output."""
    positive_timeout(timeout)
    request = normalize_message(request,qos_patch=True)
    request.pop('message_id',None)
    if request['message'] in READ_MESSAGES:
        return ExecutionPlan(request)
    if request['message'].startswith('ue_modify'):
        return _prepare_qos(api,request,baseline,timeout)
    params = _params(request)
    expected = _leaves(params)
    timers = set(params) & {'t3512','t3412'}
    if timers and len(params) != 1:
        raise ValidationError('Registration timer changes must be separate from other settings')
    current = _send(api,{'message':'config_get'},timeout)
    if 'logs' in params and current.get('logs',{}).get('locked'):
        raise ValidationError('Server logging is locked')
    supplied = normalize_message(baseline) if baseline is not None else None
    if supplied and supplied['message'] != 'config_set':
        raise ValidationError('Configuration baseline must be a config_set request')
    before, guard, missing = {}, {}, []
    for path in expected:
        try:
            value = _get(current,path)
            guard[path] = value
            if supplied:
                try:
                    if _get(supplied,path) != value:
                        raise ValidationError('Baseline disagrees with live config_get')
                except KeyError:
                    pass
        except (KeyError,TypeError):
            if path.startswith('logs.'):
                raise ValidationError(f'Cannot observe logging field {path}')
            try:
                value = _get(supplied,path)
            except (KeyError,TypeError):
                raise ValidationError(f'No documented live read-back for {path}; provide a known current --baseline')
            missing.append(path)
        before[path] = value
    compensation = {'message':'config_set'}
    for path,value in before.items():
        _put(compensation,path,value)
    normalize_message(compensation)
    mode = 'config' if not missing else 'config_manual'
    targets = []
    warnings = ['Core-wide change; coordinate with other lab users.']
    if missing:
        warnings.append('Original values for '+', '.join(missing)+' rely on the operator baseline, not live read-back.')
    if timers:
        mode = 'timer'
        timer = next(iter(timers))
        rats = ('NR',) if timer == 't3512' else ('LTE','NBIOT')
        for ue in _ues(api,timeout):
            if ue.get('registered') is True and ue.get('rat_type') in rats:
                key = list(_ue_key(ue))
                if key in targets:
                    raise ValidationError('Duplicate UE identities in timer preflight')
                if type(ue.get(timer)) is not int:
                    raise ValidationError('Registered UE did not expose its timer value')
                targets.append(key)
        if not targets:
            raise ValidationError('No registered UEs of the required RAT available for timer verification')
        warnings.extend(['Every listed UE must re-register before verification.',
                         'UE overrides or requested timer values can prevent an exact match.',
                         'Timer restoration needs another registration cycle; it is never claimed automatically.'])
    if mode == 'config_manual':
        warnings.append('No automatic value verification/rollback; result will remain unverified.')
    return ExecutionPlan(request,compensation,mode,before,expected,targets,warnings,guard)


def _observe_config(api, plan, timeout):
    response = _send(api,{'message':'config_get'},timeout)
    found = {path:_get(response,path) for path in plan.expected}
    probe = {'message':'config_set'}
    for path,value in found.items():
        _put(probe,path,value)
    normalize_message(probe)
    return found


def _refresh_guard(api, plan, timeout):
    if plan.mode == 'qos_manual':
        ue = _select_ue(_ues(api,timeout),plan.request)
        if _qos_guard(ue,plan.request) != plan.guard:
            raise ValidationError('UE/session changed since preflight; prepare and confirm again')
        return
    response = _send(api,{'message':'config_get'},timeout)
    if 'logs' in plan.request and response.get('logs',{}).get('locked'):
        raise ValidationError('Logging became locked after preflight')
    for path,value in plan.guard.items():
        if _get(response,path) != value:
            raise ValidationError('Configuration changed after preflight; prepare and confirm again')


def execute_plan(api, plan, *, confirm, timeout=5.0, after_apply=None, confirm_rollback=None):
    """confirm(summary) must return True. Read operations need no confirmation.

    after_apply(summary) is a UI callback for timer re-registration, not a test
    of success. Only the subsequent API read can verify the observed UE timers.
    Recovery writes require confirm_rollback(summary) to return True separately.
    The CLI obtains session permission before connection or any read operations.
    """
    positive_timeout(timeout)
    request = normalize_message(plan.request)
    if plan.mode == 'read':
        return {'status':'read_complete','verified':True,'response':_send(api,request,timeout)}
    normalize_message(plan.compensation)
    if not callable(confirm) or confirm(plan.summary()) is not True:
        return {'status':'cancelled','verified':False,'write_sent':False}
    _refresh_guard(api,plan,timeout)
    result = {'status':'unknown','verified':False,'request':request,
              'compensation':plan.compensation,'mode':plan.mode,'before':plan.before}
    try:
        result['response'] = _send(api,request,timeout)
    except Exception as exc:
        result['apply_error'] = str(exc)
    if plan.mode in ('qos_manual','config_manual'):
        result['status'] = 'accepted_unverified' if 'apply_error' not in result else 'unknown'
        result['note'] = 'No observable value read-back. Inspect evidence; never treat this as verified success.'
        return result
    if plan.mode == 'timer':
        result['status'] = 'pending_verification'
        try:
            if not callable(after_apply) or after_apply(plan.summary()) is not True:
                return result
            timer = next(iter(plan.expected))
            rows = _ues(api,timeout)
            observed = []
            for key in plan.targets:
                matches = [u for u in rows if list(_ue_key(u)) == key]
                if len(matches) != 1 or matches[0].get('registered') is not True:
                    raise ValidationError('An original target UE is missing or not registered')
                value = matches[0].get(timer)
                if type(value) is not int:
                    raise ValidationError('UE timer is missing or malformed')
                observed.append({'identity':key,timer:value})
            result['observed'] = observed
            result['verified'] = all(row[timer] == plan.expected[timer] for row in observed)
            result['status'] = 'verified' if result['verified'] else 'verification_failed'
            result['note'] = 'Verification covers listed UEs after operator-triggered registration, not all core subscribers.'
        except (Exception,KeyboardInterrupt) as exc:
            result['status'] = 'unknown'
            result['verification_error'] = str(exc)
        return result
    # Bounded reconciliation; never resend the original mutation.
    found = None
    for _ in range(2):
        try:
            found = _observe_config(api,plan,timeout)
            break
        except Exception as exc:
            result['verification_error'] = str(exc)
    if found is None:
        result['note'] = 'State unknown. No blind compensation was sent.'
        return result
    result['after'] = found
    if found == plan.expected:
        result.update(status='verified',verified=True)
        return result
    if found == plan.before:
        result.update(status='not_applied',rollback_attempted=False)
        return result
    # Do not overwrite a third-party value. Compensate only a partial application
    # whose every changed field is one of our before/after values.
    if any(found[k] not in (plan.before[k],plan.expected[k]) for k in found):
        result.update(status='conflict',note='Unexpected concurrent value; no automatic rollback sent.')
        return result
    if not callable(confirm_rollback) or confirm_rollback({
            'request':copy.deepcopy(plan.compensation),'observed':copy.deepcopy(found)}) is not True:
        result.update(status='recovery_pending',rollback_attempted=False,
                      note='Recovery declined; partial application remains. Inspect state before restoring.')
        return result
    try:
        if _observe_config(api,plan,timeout) != found:
            result.update(status='conflict',note='State changed before compensation.')
            return result
    except Exception as exc:
        result.update(status='unknown',verification_error=str(exc))
        return result
    result['rollback_attempted'] = True
    try:
        _send(api,plan.compensation,timeout)
    except Exception as exc:
        result['rollback_error'] = str(exc)
    try:
        restored = _observe_config(api,plan,timeout)
        result['restored'] = restored
        result['rollback_succeeded'] = restored == plan.before
        result['status'] = 'rolled_back' if result['rollback_succeeded'] else 'rollback_failed'
    except Exception as exc:
        result.update(status='unknown',rollback_succeeded=False,rollback_error=str(exc))
    return result
