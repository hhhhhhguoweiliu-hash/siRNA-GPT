"""Credential-free effective evaluation settings, shared by both launchers."""
import hashlib, json

def evaluation_settings(cfg):
    # Defaults mirror model_client.request_completion and conversation.run_model.
    return {'max_output_tokens': int(cfg.get('max_output_tokens', 1800)),
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

def settings_sha256(settings):
    return hashlib.sha256(json.dumps(settings, ensure_ascii=False, sort_keys=True,
        separators=(',', ':')).encode('utf-8')).hexdigest()
