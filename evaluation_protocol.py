"""Credential-free effective evaluation settings, shared by both launchers."""
import hashlib, json

def evaluation_settings(cfg, *, dialogue=False):
    # Defaults mirror model_client.request_completion and conversation.run_model.
    settings={'max_output_tokens': int(cfg.get('max_output_tokens', 1800)),
        'answer_contract': 'evaluation_contract.FINAL_ANSWER_STYLE / 20261022',
        'rubric': 'evaluation_rubric.json / 20261022_1310; seen development tasks',
        'input_policy': 'identical full raw candidate rows and task conditions; planner sees actual sequences',
        'thinking': cfg.get('thinking', 'disabled'),
        'request_timeout_seconds': int(cfg.get('request_timeout', 90)),
        'api_retries': max(0, min(int(cfg.get('api_retries', 1)), 2)),
        'max_model_turns': int(cfg.get('max_model_turns', 12)),
        'max_tool_calls': int(cfg.get('max_tool_calls', 18)),
        'case_timeout_seconds': 360,
        'external_web_enabled': False,
        'temperature_policy': 'not explicitly set; provider default',
        'response_policy': 'provider incomplete remains a failure; never silently extend or retry for a better answer',
        'budget_policy': 'same per-request output cap for both model arms; agent can make multiple requests'}
    if dialogue:
        settings.update(case_timeout_seconds=int(cfg.get('dialogue_case_timeout_seconds',720)),
            round_timeout_seconds=int(cfg.get('dialogue_round_timeout_seconds',360)),
            max_model_requests_per_round=int(cfg.get('max_model_turns',12))+1,
            max_model_requests_per_case=2*(int(cfg.get('max_model_turns',12))+1),
            ordinary_model_requests_per_round=1,
            failure_policy='Stop remaining user rounds after execution/transport/planning/budget failure; retain NOT_EXECUTED records',
            timeout_enforcement='Cooperative checks before/after calls; no claim of interrupting a blocking transport',
            physical_attempts_policy='API retries belong to each logical request; real API path remains disabled')
        if settings['round_timeout_seconds']<=0 or settings['case_timeout_seconds']<=0:
            raise ValueError('每轮和每题时限必须大于0')
    return settings

def settings_sha256(settings):
    return hashlib.sha256(json.dumps(settings, ensure_ascii=False, sort_keys=True,
        separators=(',', ':')).encode('utf-8')).hexdigest()
