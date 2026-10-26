"""Shared-round development entry. Model transports here MUST be explicit test stubs.

No paid API path or website launch is added. Existing scientific tools are reused
in imported mode, with per-round cold sessions and each arm's own history only.
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


def run_dialogue(group, case, cfg, root, transport=None, resources=None):
    if group not in ('llm', 'workflow', 'agent'):
        raise ValueError('Unknown configuration')
    if group != 'workflow' and transport is None:
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
    save_json(root / 'resource_access.json', policy)
    history, records, requests = [], [], []
    start = time.monotonic()
    settings = evaluation_settings(cfg)
    def recorded_transport(payload):
        if time.monotonic() - start > 720:
            raise TaskError('达到本开发入口每题720秒上限；停止并保留已完成记录')
        if len(requests) >= 26:
            raise TaskError('达到本开发入口每题26个替身请求上限')
        item = {'record_kind': 'OFFLINE_MODEL_STUB_NOT_REAL_MODEL', 'round': len(records) + 1,
                'payload': copy.deepcopy(payload), 'effective_settings': settings}
        requests.append(item)
        folder = root / 'test_transport' / str(len(requests)).zfill(3)
        save_json(folder / 'prepared_request.json', item)
        response = transport(copy.deepcopy(payload))
        save_json(folder / 'stub_response.json', {'record_kind': item['record_kind'], 'response': response})
        return response
    for number, spec in enumerate(case['rounds'], 1):
        common = common_round(spec)
        inputs = effective_input(common)
        before = copy.deepcopy(history)
        folder = root / ('round_' + str(number))
        save_json(folder / 'common_user_input.json', common)
        save_json(folder / 'resolved_input.json', inputs)
        save_json(folder / 'own_history_before.json', before)
        # Same complete user envelope and same history policy, not equal histories:
        # each configuration sees only its OWN previous actual output.
        inputs['task']['own_history'] = before
        plan, state, session, error = [], {}, None, ''
        raw_model_answer = None
        request_start = len(requests)
        if group == 'llm':
            payload = {'model': cfg.get('model'), 'messages': [
                {'role': 'system', 'content': '你是siRNA研究助手。无科学工具、无外网，不编造计算或实验结果。' + SCOPE + FINAL_ANSWER_STYLE + FIELD_INSTRUCTIONS},
                {'role': 'user', 'content': json.dumps({'input': inputs, 'request': common['message'],
                    'shared_user_input': common, 'own_history': before,
                    'declared_resources': {'scientific_tools': False, 'external_web': False}}, ensure_ascii=False)}]}
            response = recorded_transport(payload)
            raw_model_answer = response['choices'][0]['message'].get('content') or ''
            answer, status, answer_source = raw_model_answer, 'TEST_STUB_ANSWER', 'OFFLINE_MODEL_STUB'
        else:
            decision = 'ready'
            if group == 'agent':
                proposed, _ = propose(common['message'], inputs, before, cfg, recorded_transport,
                    local_context={'own_history': before, 'resource_policy': policy})
                decision, plan = proposed['decision'], proposed['tools']
                if proposed.get('task_updates'):
                    raise TaskError('本开发题用户条件已明确；不接受规划器改写共同条件')
                if decision != 'ready':
                    raw_model_answer = proposed['summary'] + ('\n' + proposed['question'] if proposed['question'] else '')
                    answer, status, answer_source = raw_model_answer, 'TEST_STUB_' + decision.upper(), 'OFFLINE_MODEL_STUB'
            else:
                plan = fixed_plan(common['conditions'])
            if decision == 'ready' and not plan:
                answer = ('判定：只有订购原文，尚无供应商已确认的链角色。\n关键结果：' +
                    '\n'.join(common['user_input'].get('original_order_lines', [])) +
                    '\n证据：本轮原始订购两行与修饰注释；没有执行科学核查。'
                    '\n限制或下一步：可在明确计算链假设后继续；不自动删TT/N3，不据此生成可下单双链。')
                status, answer_source = 'CLARIFICATION_NO_SCIENTIFIC_EXECUTION', 'FIXED_CONDITION_PRESENTATION'
            elif decision == 'ready':
                session = PlannedSession(plan, mode='workflow' if group == 'workflow' else 'agent',
                    cfg=cfg, run_root=folder / 'runs', **inputs)
                try:
                    if group == 'workflow':
                        for name in session.planned_tools:
                            got = session.call(name, {})
                            if got.get('status') == 'ERROR':
                                raise TaskError(got['message'])
                        result = session.result_for_plan()
                        status = result['status']
                        answer_source = 'DETERMINISTIC_EXISTING_TOOL_EVIDENCE'
                    else:
                        result = session.run_agent(recorded_transport)
                        status = result['status']
                        raw_model_answer = result.get('model_summary_raw') or result.get('model_summary') or result.get('message', '')
                        answer_source = 'OFFLINE_MODEL_STUB_WITH_SHARED_VALIDATION'
                except TaskError as exc:
                    error, status = str(exc), 'FAILED_WITH_RETAINED_PARTIAL_EVIDENCE'
                    answer_source = 'SHARED_ERROR_PRESENTATION_NOT_MODEL_REASONING'
                state = copy.deepcopy(session.state)
                answer = workflow_answer(inputs, state, error) if group == 'workflow' or error else result.get('model_summary_display') or raw_model_answer
                if group == 'workflow' and number > 1:
                    old_tools = set(records[-1]['completed_tools'])
                    repeated = [n for n in state if n in old_tools]
                    added = [n for n in state if n not in old_tools]
                    answer += '\n轮次记录：首轮原文保留；本轮重新核对（不复用工具缓存）：' + '、'.join(repeated) + '；本轮新增：' + '、'.join(added)
        history.extend([{'role': 'user', 'content': common}, {'role': 'assistant', 'content': answer}])
        record = {'round': number, 'common_user_input': common, 'common_input_sha256': input_sha256(common),
            'resolved_input_sha256_without_own_history': input_sha256(effective_input(common)),
            'history_before': before, 'history_after': copy.deepcopy(history),
            'status': status, 'answer': answer, 'answer_source': answer_source,
            'raw_model_answer_TEST_ONLY': raw_model_answer, 'planned_tools': plan,
            'completed_tools': list(state), 'tool_results': state, 'error': error,
            'resource_access': policy, 'test_stub_requests': len(requests) - request_start,
            'real_model_requests': 0, 'usage_real_model': None,
            'run_id': session.id if session else None,
            'delivered_files': [str(p.relative_to(root)).replace('\\', '/') for p in (session.path.rglob('*') if session else []) if p.is_file()]}
        save_json(folder / 'turn_record.json', record)
        records.append(record)
    result = {'group': group, 'case_id': case['id'], 'record_kind': 'OFFLINE_ACCEPTANCE_NOT_REAL_MODEL_EVALUATION',
        'status': records[-1]['status'], 'answer': records[-1]['answer'], 'rounds': records,
        'case_input': [r['common_user_input'] for r in records], 'input_sha256': input_sha256([r['common_user_input'] for r in records]),
        'tool_results': records[-1]['tool_results'], 'completed_tools': records[-1]['completed_tools'],
        'tool_calls': sum(len(r['completed_tools']) + bool(r['error']) for r in records),
        'usage': [], 'total_tokens': 0 if group == 'workflow' else None, 'usage_complete': group == 'workflow',
        'real_model_requests': 0, 'test_stub_requests': len(requests),
        'test_prepared_requests': requests, 'seconds': round(time.monotonic() - start, 3),
        'quality_scored': False, 'resource_access': policy}
    save_json(root / 'case_input.json', {'rounds': result['case_input'], 'input_sha256': result['input_sha256']})
    save_json(root / 'result.json', result)
    return result
