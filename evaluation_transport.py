"""Audited provider adapter; HTTP fixtures never count as real model usage."""
import json
import re
from pathlib import Path
from core import save_json
from model_client import request_completion,model_error_evidence,extract_model


def sanitized(value,cfg):
    raw=json.dumps(value,ensure_ascii=False,default=str)
    if cfg.get('api_key'):raw=raw.replace(str(cfg['api_key']),'[REDACTED]')
    raw=re.sub(r'(?i)(Bearer\s+)[^\s"\']+',r'\1[REDACTED]',raw)
    return json.loads(raw)


class RecordedTransport:
    def __init__(self,cfg,root,*,mode,opener=None,remaining_seconds=None):
        if mode not in ('provider','http_fixture'):raise ValueError('Unknown audited transport mode')
        if (mode=='http_fixture') != (opener is not None):raise ValueError('HTTP fixture requires explicit opener; provider forbids fixture injection')
        self.cfg,self.root,self.mode=cfg,Path(root),mode
        self.opener,self.remaining_seconds=opener,remaining_seconds
        self.requests=[]

    def __call__(self,payload):
        folder=self.root/str(len(self.requests)+1).zfill(3)
        item={'mode':self.mode,'configured_model':extract_model(self.cfg.get('model')),
            'api_mode':self.cfg.get('api_mode','chat'),'attempts':[],'normalized_usage':None,'returned_model':None,
            'record_kind':'REAL_PROVIDER_REQUEST' if self.mode=='provider' else 'SYNTHETIC_HTTP_FIXTURE_NOT_MODEL_RESULT'}
        self.requests.append(item)
        save=lambda name,data:save_json(folder/name,sanitized(data,self.cfg))
        save('prepared_request.json',payload)
        def audit(event):
            attempt=event['attempt']
            if event['event']=='attempt_started':
                entry={'attempt':attempt,'events':[]};item['attempts'].append(entry)
            entry=item['attempts'][attempt-1]
            entry['events'].append(sanitized(event,self.cfg))
            if event['event']=='response_received':
                response=event['response']
                if isinstance(response,dict):item['returned_model']=response.get('model')
            if event['event']=='attempt_finished':entry['status']=event['status']
            save('http_attempt_'+str(attempt).zfill(2)+'.json',entry)
        try:
            response=request_completion(self.cfg,payload,opener=self.opener,audit=audit,remaining_seconds=self.remaining_seconds)
            item.update(status='SUCCEEDED',normalized_usage=response.get('usage') or {},returned_model=response.get('model') or item['returned_model'])
            save('response.json',response)
            return response
        except Exception as exc:
            partial=getattr(exc,'response_snapshot',None)
            item.update(status=getattr(exc,'code','TRANSPORT_ERROR'),normalized_usage=(partial or {}).get('usage',{}) if isinstance(partial,dict) else {})
            if isinstance(partial,dict):item['returned_model']=partial.get('model') or item['returned_model']
            if item['attempts'] and 'status' not in item['attempts'][-1]:
                attempt=item['attempts'][-1]
                attempt['status']='UNEXPECTED_TRANSPORT_ERROR'
                attempt['events'].append(sanitized({'event':'attempt_finished','status':attempt['status'],'message':str(exc)},self.cfg))
                save('http_attempt_'+str(attempt['attempt']).zfill(2)+'.json',attempt)
            save('error.json',model_error_evidence(exc,self.cfg,payload) if hasattr(exc,'diagnostics') else {'message':str(exc),'partial_response':partial})
            raise
        finally:save('request_record.json',item)

    def summary(self,start=0):
        records=self.requests[start:]
        attempts=[a for r in records for a in r['attempts']]
        # Count each physical response once, including usage supplied with an
        # error before a retry. Never add normalized and raw copies twice.
        usages=[]
        for attempt in attempts:
            response=next((e['response'] for e in attempt['events']
                if e.get('event')=='response_received' and isinstance(e.get('response'),dict)),None)
            if response is None:response=next((e['response'] for e in attempt['events'] if isinstance(e.get('response'),dict)),{})
            usages.append(response.get('usage') or {})
        known=[u['total_tokens'] for u in usages if isinstance(u,dict) and type(u.get('total_tokens')) is int]
        complete=all(r['attempts'] for r in records) and all(isinstance(u,dict) and type(u.get('total_tokens')) is int for u in usages) and all(a.get('status')=='SUCCEEDED' for a in attempts)
        provider=self.mode=='provider'
        return {'mode':self.mode,'logical_model_requests':len(records),'http_attempts':len(attempts),
            'http_retries':sum(max(0,len(r['attempts'])-1) for r in records),
            'real_model_requests':len(attempts) if provider else 0,
            'synthetic_http_attempts':len(attempts) if not provider else 0,
            'provider_model_versions':list(dict.fromkeys(r['returned_model'] for r in records if r['returned_model'])),
            'usage':usages if provider else [],'synthetic_usage':usages if not provider else [],
            'logical_response_usage':[r['normalized_usage'] for r in records],
            'usage_scope':'Physical attempts, one actual provider response per attempt; raw and normalized copies are not double counted',
            'total_tokens':sum(known) if complete and provider else None,
            'known_token_subtotal':sum(known) if provider and known else None,
            'usage_complete':complete if provider else False,
            'configured_model':extract_model(self.cfg.get('model')),
            'model_version_limit':'Actual returned model retained when supplied; missing provider version is not inferred from configured alias'}
