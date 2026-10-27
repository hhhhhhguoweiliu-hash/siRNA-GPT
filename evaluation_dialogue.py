"""Shared-round execution; provider mode requires explicit usage confirmation.

Default remains offline. HTTP fixture mode uses the provider adapter without a
network request; its responses/usage are never labelled real model evidence.
"""
import copy
import json
import time
from pathlib import Path

from conversation import PlannedSession, expand_plan, propose, SCOPE
from core import save_json, TaskError, TOOLS
from evaluation_contract import FINAL_ANSWER_STYLE, FIELD_INSTRUCTIONS, input_sha256, workflow_answer
from evaluation_protocol import evaluation_settings
from verified_imports import calculation_candidate

CHECKS = {
    'candidate_check': 'inspect_candidates', 'reference_check': 'verify_target',
    'score_check': 'score_candidates', 'seed_check': 'match_seed',
    'expression_check': 'query_expression', 'report_required': 'compile_report',
}
BOOL_FIELDS = set(CHECKS) | {'both_expression_states', 'compare_all_requested_candidates',
                           'allow_builtin_expression', 'chain_assumption_provided'}


def fixed_plan(conditions):
    """One published rule for all cases; no case ID or expected-answer lookup."""
    if set(conditions) - BOOL_FIELDS or any(type(v) is not bool for v in conditions.values()):
        raise ValueError('共同条件表只接受已声明的布尔条件')
    requested = [tool for key, tool in CHECKS.items() if conditions.get(key, False)]
    return expand_plan(requested) if requested else []


def common_round(round_spec):
    """Whitelist input content; no reviewer fields, private key or old answers."""
    if set(round_spec) != {'message', 'user_input', 'conditions'}:
        raise ValueError('每轮只允许消息、用户原始输入和共同条件')
    raw = copy.deepcopy(round_spec['user_input'])
    permitted = {'candidate_rows', 'original_order_lines', 'calculation_assumptions',
                 'user_provided_evidence', 'declared_core_coordinates', 'constructed_material'}
    if set(raw) - permitted:
        raise ValueError('原始输入夹带未声明字段')
    conditions = copy.deepcopy(round_spec['conditions'])
    fixed_plan(conditions)
    if not isinstance(round_spec['message'], str) or not 1 <= len(round_spec['message']) <= 2000:
        raise ValueError('需求消息长度不符合现有入口')
    return {'message': round_spec['message'], 'user_input': raw, 'conditions': conditions}


def effective_input(common):
    raw = common['user_input']
    rows = copy.deepcopy(raw.get('candidate_rows', []))
    if raw.get('calculation_assumptions'):
        if rows:
            raise ValueError('不得同时给候选行与另行转换的订购输入')
        rows = [calculation_candidate(raw['original_order_lines'], raw['calculation_assumptions'])]
    if not isinstance(rows, list) or len(rows) > 20:
        raise ValueError('当前计算入口最多20条候选')
    task = {'gene': 'VEGFA', 'species': 'Homo sapiens', 'state': 'Hypoxia', 'top_n': 2,
            'request': common['message'], 'expression_dataset_id': 'builtin',
            'allow_builtin_expression': common['conditions'].get('allow_builtin_expression', True),
            'evaluation_conditions': common['conditions'],
            'user_provided_evidence': raw.get('user_provided_evidence', {}),
            'declared_core_coordinates': raw.get('declared_core_coordinates', []),
            'original_order_lines': raw.get('original_order_lines', []),
            'shared_user_input': common}
    return {'task': task, 'candidates': rows, 'tool_mode': 'imported'}


def access_policy(case, resources):
    identity = input_sha256(resources)
    return {'resources_sha256': identity, 'resource_files': resources['files'],
            'scientific_tools_for_tool_arms': list(CHECKS.values()),
            'ordinary_model_scientific_tool_access': False, 'external_web': False,
            'reviewer_material_access': False, 'case_category': case['category'],
            'cache': 'COLD_SCIENTIFIC_SESSION_EACH_USER_ROUND; own history retained; no cross-arm state',
            'qa_comparable': False,
            'per_round_restrictions': [{'round': i + 1,
                'builtin_expression_allowed': spec['conditions'].get('allow_builtin_expression', True)}
                for i, spec in enumerate(case['rounds'])]}


def run_dialogue(group, case, cfg, root, transport=None, resources=None,*,
                 execution_mode='offline_stub',confirm_api_usage=False,http_opener=None,stop_requested=None):
    if group not in ('llm', 'workflow', 'agent'):
        raise ValueError('Unknown configuration')
    if execution_mode not in ('offline_stub','provider','http_fixture'):
        raise ValueError('Unknown execution mode')
    if execution_mode=='provider' and (confirm_api_usage is not True or transport is not None or http_opener is not None):
        raise ValueError('真实模型只允许已确认用量的官方适配路径，不能传入未标记替身')
    if execution_mode=='http_fixture' and (http_opener is None or transport is not None):
        raise ValueError('HTTP检查必须显式传入无网络替身')
    if execution_mode=='offline_stub' and http_opener is not None:raise ValueError('Use explicit HTTP fixture mode')
    if group != 'workflow' and transport is None and execution_mode=='offline_stub':
        raise ValueError('新两轮入口目前仅允许明确传入的无模型替身；尚未接入网页用量确认，不启动API')
    if case['category'] == 'literature_qa':
        raise ValueError('Q1/Q2资料问答尚未具备三组对等入口，单列未支持，不当作某组科研失败')
    if not 1 <= len(case['rounds']) <= 2:
        raise ValueError('当前开发协议仅支持一轮或预定两轮')
    root = Path(root)
    if root.exists() and any(root.iterdir()):
        raise ValueError('Use a new empty output directory; previous records are never overwritten')
    root.mkdir(parents=True, exist_ok=True)
    policy = access_policy(case, resources or {'files': {}})
    settings = evaluation_settings(cfg, dialogue=True)
    save_json(root / 'resource_access.json', policy)
    save_json(root / 'effective_settings.json', settings)
    save_json(root / 'planned_rounds.json', {'rounds': case['rounds'], 'failure_policy': settings['failure_policy']})
    history, records, requests = [], [], []
    start = time.monotonic()
    round_start, current_round = start, 1
    stopped = False
    audited=None
    def sanitized(value):
        text = json.dumps(value, ensure_ascii=False, default=str)
        if cfg.get('api_key'):
            text = text.replace(cfg['api_key'], '[REDACTED]')
        return json.loads(text)
    def error_info(exc, stage):
        evidence = {'stage': stage, 'exception_type': type(exc).__name__, 'message': str(exc)}
        if hasattr(exc, 'diagnostics'):
            evidence['diagnostics'] = exc.diagnostics()
        partial = getattr(exc, 'response_snapshot', None)
        if partial is not None:
            evidence['partial_response'] = partial
        return sanitized(evidence)
    def budget_check():
        if stop_requested and stop_requested():raise TaskError('用户已要求停止；已取得的内容保留，不启动后续轮次')
        now = time.monotonic()
        if now - start > settings['case_timeout_seconds']:
            raise TaskError('达到有效每题时限：' + str(settings['case_timeout_seconds']) + '秒；停止并保留记录')
        if now - round_start > settings['round_timeout_seconds']:
            raise TaskError('达到有效每轮时限：' + str(settings['round_timeout_seconds']) + '秒；停止并保留记录')
    def remaining_seconds():
        budget_check()
        return min(settings['case_timeout_seconds']-(time.monotonic()-start),
                   settings['round_timeout_seconds']-(time.monotonic()-round_start))
    if execution_mode!='offline_stub' and group!='workflow':
        from evaluation_transport import RecordedTransport
        audited=RecordedTransport(cfg,root/'model_transport',mode=execution_mode,
            opener=http_opener,remaining_seconds=remaining_seconds)
        transport=audited
    def recorded_transport(payload):
        budget_check()
        per_round = sum(r['round'] == current_round for r in requests)
        if per_round >= settings['max_model_requests_per_round'] or len(requests) >= settings['max_model_requests_per_case']:
            raise TaskError('达到有效模型逻辑请求上限；后续轮次不启动')
        kind={'offline_stub':'OFFLINE_MODEL_STUB_NOT_REAL_MODEL','provider':'REAL_PROVIDER_MODEL_REQUEST',
              'http_fixture':'SYNTHETIC_HTTP_FIXTURE_NOT_MODEL_RESULT'}[execution_mode]
        item = {'record_kind': kind, 'round': current_round,
                'payload': copy.deepcopy(payload), 'effective_settings': settings}
        requests.append(item)
        folder = root / ('test_transport' if execution_mode=='offline_stub' else 'model_requests') / str(len(requests)).zfill(3)
        save_json(folder / 'prepared_request.json', sanitized(item))
        try:
            response = transport(copy.deepcopy(payload))
            save_json(folder / ('stub_response.json' if execution_mode=='offline_stub' else 'response.json'), sanitized({'record_kind': item['record_kind'], 'response': response}))
            item['response_saved'] = True
            budget_check()
            return response
        except Exception as exc:
            item['transport_error'] = error_info(exc, 'model_transport')
            save_json(folder / 'transport_error.json', item['transport_error'])
            raise
    for number, spec in enumerate(case['rounds'], 1):
        current_round, round_start = number, time.monotonic()
        folder = root / ('round_' + str(number))
        before = copy.deepcopy(history)
        common, inputs = None, None
        plan, state, session, error = [], {}, None, ''
        raw_model_answer, error_record = None, None
        update_check = {'unchanged': {}, 'conflicts': {}}
        request_start, stage = len(requests), 'input_preparation'
        status, answer, answer_source = 'NOT_EXECUTED', '', 'NO_ANSWER'
        try:
            common = common_round(spec)
            save_json(folder / 'common_user_input.json', common)
            save_json(folder / 'own_history_before.json', before)
            if stopped:
                answer_source = 'PREVIOUS_ROUND_FAILED_NO_EXECUTION'
            else:
                inputs = effective_input(common)
                save_json(folder / 'resolved_input.json', inputs)
                inputs['task']['own_history'] = before
                budget_check()
                if group == 'llm':
                    stage = 'ordinary_model'
                    payload = {'model': cfg.get('model'), 'messages': [
                        {'role': 'system', 'content': '你是siRNA研究助手。无科学工具、无外网，不编造计算或实验结果。' + SCOPE + FINAL_ANSWER_STYLE + FIELD_INSTRUCTIONS},
                        {'role': 'user', 'content': json.dumps({'input': inputs, 'request': common['message'],
                            'shared_user_input': common, 'own_history': before,
                            'declared_resources': {'scientific_tools': False, 'external_web': False}}, ensure_ascii=False)}]}
                    response = recorded_transport(payload)
                    raw_model_answer = response['choices'][0]['message'].get('content') or ''
                    if not raw_model_answer.strip():raise TaskError('模型没有返回可读回答，原响应保留；不能当作已完成科研任务')
                    answer=raw_model_answer
                    status='ANSWERED_NO_TOOLS' if execution_mode=='provider' else 'TEST_STUB_ANSWER'
                    answer_source='REAL_MODEL_NO_TOOLS' if execution_mode=='provider' else 'OFFLINE_MODEL_STUB' if execution_mode=='offline_stub' else 'SYNTHETIC_HTTP_FIXTURE'
                else:
                    decision = 'ready'
                    if group == 'agent':
                        stage = 'planner'
                        proposed, _ = propose(common['message'], inputs, before, cfg, recorded_transport,
                            local_context={'own_history': before, 'resource_policy': policy})
                        decision, plan = proposed['decision'], proposed['tools']
                        stage = 'planner_update_validation'
                        for key, value in proposed.get('task_updates', {}).items():
                            bucket = 'unchanged' if key in inputs['task'] and inputs['task'][key] == value else 'conflicts'
                            update_check[bucket][key] = value
                        if update_check['conflicts']:
                            raise TaskError('规划条件与共同输入冲突，停止且不采用改写：' + json.dumps(update_check['conflicts'], ensure_ascii=False))
                        if decision != 'ready':
                            raw_model_answer = proposed['summary'] + ('\n' + proposed['question'] if proposed['question'] else '')
                            answer=raw_model_answer
                            status=('MODEL_' if execution_mode=='provider' else 'TEST_STUB_')+decision.upper()
                            answer_source='REAL_MODEL_PLANNER' if execution_mode=='provider' else 'OFFLINE_MODEL_STUB' if execution_mode=='offline_stub' else 'SYNTHETIC_HTTP_FIXTURE'
                    else:
                        stage = 'fixed_plan'
                        plan = fixed_plan(common['conditions'])
                    if decision == 'ready' and not plan:
                        answer = ('判定：只有订购原文，尚无供应商已确认的链角色。\n关键结果：' +
                            '\n'.join(common['user_input'].get('original_order_lines', [])) +
                            '\n证据：本轮原始订购两行与修饰注释；没有执行科学核查。'
                            '\n限制或下一步：可在明确计算链假设后继续；不自动删TT/N3，不据此生成可下单双链。')
                        status, answer_source = 'CLARIFICATION_NO_SCIENTIFIC_EXECUTION', 'FIXED_CONDITION_PRESENTATION'
                    elif decision == 'ready':
                        stage = 'session_initialization'
                        session = PlannedSession(plan, mode='workflow' if group == 'workflow' else 'agent',
                            cfg=cfg, run_root=folder / 'runs', **inputs)
                        stage = 'fixed_tools' if group == 'workflow' else 'executor'
                        if group == 'workflow':
                            session.execute_confirmed_subflow(budget_check)
                            result = session.result_for_plan()
                            status, answer_source = result['status'], 'DETERMINISTIC_EXISTING_TOOL_EVIDENCE'
                        else:
                            session.cancelled=lambda:bool(stop_requested and stop_requested())
                            result = session.run_agent(recorded_transport,test_only=execution_mode!='provider')
                            status = result['status']
                            raw_model_answer = result.get('model_summary_raw') or result.get('model_summary') or result.get('message', '')
                            answer_source = 'SHARED_VERIFIED_FIELD_PRESENTATION_WITH_MODEL_DIAGNOSTIC' if execution_mode=='provider' else 'OFFLINE_SHARED_PRESENTATION_MODEL_STUB' if execution_mode=='offline_stub' else 'SYNTHETIC_HTTP_FIXTURE_SHARED_PRESENTATION'
                        state = copy.deepcopy(session.state)
                        stage = 'presentation'
                        answer = result.get('model_summary_display') or workflow_answer(inputs,state)
                        if group == 'workflow' and number > 1:
                            old_tools = set(records[-1]['completed_tools'])
                            repeated = [n for n in state if n in old_tools]
                            added = [n for n in state if n not in old_tools]
                            answer += '\n轮次记录：首轮原文保留；本轮重新核对（不复用工具缓存）：' + '、'.join(repeated) + '；本轮新增：' + '、'.join(added)
                budget_check()
        except Exception as exc:
            error_record = error_info(exc, stage)
            error = error_record['message']
            save_json(folder / 'error.json', error_record)
            state = copy.deepcopy(session.state) if session else {}
            status = 'FAILED_WITH_RETAINED_PARTIAL_EVIDENCE'
            answer_source = 'SHARED_ERROR_PRESENTATION_NOT_MODEL_REASONING'
            from delivery import present_delivery
            answer = present_delivery(inputs or {'task': {}, 'candidates': []},state,error=error)['model_summary_display']
            stopped = True
        if status != 'NOT_EXECUTED':
            history.extend([{'role': 'user', 'content': common or spec}, {'role': 'assistant', 'content': answer}])
        if status in ('INCOMPLETE_OR_CLARIFICATION',):
            stopped = True
        record = {'round': number, 'execution': 'NOT_EXECUTED' if status == 'NOT_EXECUTED' else 'ATTEMPTED',
            'not_executed_reason': 'PREVIOUS_ROUND_FAILED' if status == 'NOT_EXECUTED' else None,
            'common_user_input': common or spec,
            'common_input_sha256': input_sha256(common or spec),
            'resolved_input_sha256_without_own_history': input_sha256({**inputs, 'task': {k: v for k, v in inputs['task'].items() if k != 'own_history'}}) if inputs else None,
            'history_before': before, 'history_after': copy.deepcopy(history),
            'status': status, 'answer': answer, 'answer_source': answer_source,
            'raw_model_answer':raw_model_answer,'raw_model_answer_TEST_ONLY':raw_model_answer if execution_mode=='offline_stub' else None, 'planned_tools': plan,
            'completed_tools': list(state), 'tool_results': state, 'error': error,
            'delivery_audit':__import__('delivery').requirement_audit(inputs or {'task':{}},state,plan),
            'error_record': error_record, 'planner_task_update_check': update_check,
            'resource_access': policy, 'effective_settings': settings,
            'test_stub_requests':len(requests)-request_start if execution_mode=='offline_stub' else 0,
            'real_model_requests':audited.summary(request_start)['real_model_requests'] if audited else 0,
            'usage_real_model':audited.summary(request_start) if audited and execution_mode=='provider' else None,
            'transport_summary':audited.summary(request_start) if audited else None,
            'tool_calls': session.tool_calls if session else 0,
            'run_id': session.id if session else None,
            'delivered_files': [str(p.relative_to(root)).replace('\\', '/') for p in (session.path.rglob('*') if session else []) if p.is_file()]}
        record = sanitized(record)
        save_json(folder / 'turn_record.json', record)
        records.append(record)
    last = next((r for r in reversed(records) if r['execution'] == 'ATTEMPTED'), records[-1])
    result = {'group': group, 'case_id': case['id'], 'execution_mode':execution_mode,
        'record_kind':{'offline_stub':'OFFLINE_ACCEPTANCE_NOT_REAL_MODEL_EVALUATION','provider':'REAL_EVALUATION_ATTEMPT_NOT_HUMAN_SCORED','http_fixture':'HTTP_FIXTURE_ACCEPTANCE_NOT_REAL_MODEL_EVALUATION'}[execution_mode],
        'status': last['status'], 'answer': last['answer'], 'rounds': records,
        'planned_rounds': len(records), 'attempted_rounds': sum(r['execution'] == 'ATTEMPTED' for r in records),
        'pending_rounds': sum(r['execution'] == 'NOT_EXECUTED' for r in records),
        'case_input': [r['common_user_input'] for r in records], 'input_sha256': input_sha256([r['common_user_input'] for r in records]),
        'tool_results': last['tool_results'], 'completed_tools': last['completed_tools'],
        'tool_calls': sum(r['tool_calls'] for r in records),
        'usage': [], 'total_tokens': 0 if group == 'workflow' else None, 'usage_complete': group == 'workflow',
        'real_model_requests': 0, 'test_stub_requests':len(requests) if execution_mode=='offline_stub' else 0, 'effective_settings': settings,
        'test_prepared_requests':sanitized(requests) if execution_mode=='offline_stub' else [],
        'model_request_records':sanitized(requests) if execution_mode!='offline_stub' else [],'seconds': round(time.monotonic() - start, 3),
        'quality_scored': False, 'resource_access': policy}
    if audited:
        result.update(audited.summary())
        result['transport_summary']=audited.summary()
    for record in records:
        diagnostics=(record.get('error_record') or {}).get('diagnostics')
        if diagnostics:result['provider_error']=diagnostics;break
    result = sanitized(result)
    save_json(root / 'case_input.json', {'rounds': result['case_input'], 'input_sha256': result['input_sha256']})
    save_json(root / 'result.json', result)
    return result
