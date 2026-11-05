"""PET Circular Web v0.4 — REST local, presentation independent of deterministic engine.

Start with `python server.py`. The API binds to 127.0.0.1 only.
No PDF bytes or API keys are persisted. This is a single-user local prototype,
NOT a multi-tenant web service and NOT a recyclability certification.
"""
from __future__ import annotations

import json
import os
import secrets
import time
import webbrowser
from copy import deepcopy
from pathlib import Path
from threading import Timer
from uuid import uuid4
from typing import Any

from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Form, Header
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

import storage
from comparison_v04 import compare_reports, parse_report, validate_report
from document_ai import MAX_PDF_BYTES, check_candidate, read_pdf_bytes, local_candidates, llm_candidates, review_apply
from ecodesign_assistant import offline_answer, llm_answer
from pet_circular.engine import assess, validate
from ui_helpers import (KINDS, KIND_LABELS, fields_catalog, fresh, import_case,
                        set_components, source_catalog, rule_catalog, upsert_fact,
                        upsert_document, remove_fact)

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / 'web'
app = FastAPI(title='PET Circular Web', version='0.4.0', docs_url=None, redoc_url=None)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=['localhost', '127.0.0.1', 'testserver'])
app.mount('/static', StaticFiles(directory=FRONTEND), name='static')
_TOKEN = secrets.token_urlsafe(32)
# Short-lived extraction cache; only metadata/candidates and extracted page text held in RAM.
_EXTRACTED: dict[str, dict[str, Any]] = {}
MAX_JSON = 2_000_000


@app.middleware('http')
async def local_request_guard(request: Request, call_next):
    origin = request.headers.get('origin')
    if origin and origin.rstrip('/') != 'http://' + request.headers.get('host', 'localhost'):
        return JSONResponse(status_code=403, content={'detail': 'Origem externa não autorizada.'})
    if request.url.path.startswith('/api/') and request.method not in {'GET', 'HEAD', 'OPTIONS'}:
        if request.headers.get('x-pet-session') != _TOKEN:
            return JSONResponse(status_code=403, content={'detail': 'Sessão local não autorizada.'})
        raw_len = request.headers.get('content-length', '0')
        try:
            if int(raw_len) > MAX_PDF_BYTES + 1_000_000:
                return JSONResponse(status_code=413, content={'detail': 'Envio maior do que o limite permitido.'})
        except ValueError:
            return JSONResponse(status_code=400, content={'detail': 'Tamanho de envio inválido.'})
    return await call_next(request)


@app.exception_handler(ValueError)
async def handle_value_error(_request: Request, exc: ValueError):
    return JSONResponse(status_code=422, content={'detail': str(exc)})


@app.get('/')
def index():
    return FileResponse(FRONTEND / 'index.html')


@app.get('/api/bootstrap')
def bootstrap():
    return {
        'session_token': _TOKEN,
        'new_case': fresh(),
        'fields': fields_catalog(),
        'component_labels': KIND_LABELS,
        'sources': source_catalog(),
        'rules': {k: {'title': v.get('Título v0.3', ''),
                      'recommendation': v.get('Recomendação de ecodesign', ''),
                      'limitation': v.get('Ressalva / limite', '')} for k, v in rule_catalog().items()},
        'matrix_version': '0.3.3',
        'app_version': '0.4.0-web',
    }


def _case(value: Any) -> dict:
    if not isinstance(value, dict):
        raise ValueError('Produto inválido. Importe um arquivo de projeto válido.')
    validate(value)
    if value['matrix_version'] != '0.3.3':
        raise ValueError('A matriz do projeto é diferente da matriz 0.3.3 desta versão.')
    return value


@app.post('/api/projects/import')
async def import_project(request: Request):
    data = await request.body()
    try:
        decoded = json.loads(data)
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError('JSON inválido. Importe um projeto exportado em Projetos → Exportar entrada.') from exc
    if not isinstance(decoded, dict) or not {'project_id', 'product_id', 'product_name', 'facts', 'components', 'documents', 'matrix_version'}.issubset(decoded):
        raise ValueError('Este JSON não é um projeto PET Circular. Relatórios, listas e documentos genéricos não podem ser importados como projeto. Use Projetos → Exportar entrada.')
    return {'case': import_case(data)}


@app.post('/api/projects/update')
async def update_project(payload: dict):
    original = _case(payload.get('case'))
    result = deepcopy(original)
    changes = payload.get('details', {})
    for key in ('product_name', 'product_id', 'project_id', 'design_version', 'free_description'):
        if key in changes:
            value = str(changes[key]).strip() if key != 'free_description' else str(changes[key])
            if not value and key != 'free_description':
                raise ValueError(f'O campo {key} não pode ficar vazio.')
            result[key] = value
    if 'phase' in changes:
        result['phase'] = changes['phase']
    if 'components' in payload:
        result = set_components(result, payload['components'])
    fields = payload.get('basic_facts', {})
    permitted = {'material_corpo', 'transparencia_corpo', 'cor_corpo', 'capacidade_ml'}
    if any(k not in permitted for k in fields):
        raise ValueError('Campo básico não autorizado.')
    for key, proposed in fields.items():
        old = next((x for x in result['facts'] if x['key'] == key), None)
        if proposed in (None, ''):
            if old is not None:
                result = remove_fact(result, key)
            continue
        # Preserve confirmation only if unchanged. A new or altered UI value is DECLARADO.
        if old is not None and str(old['value']) == str(proposed):
            continue
        result = upsert_fact(result, key, str(proposed), status='DECLARADO', unit='mL' if key == 'capacidade_ml' else '')
    validate(result)
    return {'case': result, 'notice': 'Embalagem atualizada. Dados alterados ficam declarados até revisão.'}


@app.post('/api/projects/fact')
async def set_fact(payload: dict):
    project = _case(payload.get('case'))
    key = str(payload.get('key', '')).strip()
    if key not in fields_catalog():
        raise ValueError('Este campo não pertence ao catálogo técnico.')
    if payload.get('remove'):
        return {'case': remove_fact(project, key)}
    status = 'CONFIRMADO' if payload.get('confirm') else 'DECLARADO'
    reviewer = str(payload.get('reviewer') or '').strip()[:120]
    if status == 'CONFIRMADO' and (not reviewer or not payload.get('acknowledged')):
        raise ValueError('Para confirmar, identifique a pessoa revisora e confirme explicitamente a conferência.')
    doc_id = str(payload.get('doc_id') or '').strip()
    if doc_id and doc_id not in {d['id'] for d in project['documents']}:
        raise ValueError('A evidência selecionada não está cadastrada.')
    new = upsert_fact(project, key, str(payload.get('value') or ''), status=status,
                      reviewer=reviewer if status == 'CONFIRMADO' else '',
                      evidence_ids=[doc_id] if doc_id else [],
                      unit=str(payload.get('unit') or '')[:24],
                      observation=str(payload.get('observation') or '')[:700])
    return {'case': new}


@app.post('/api/documents/extract')
async def extract_pdf(file: UploadFile = File(...), product: str = Form(...),
                      mode: str = Form('local'), consent: str = Form('false'),
                      api_key: str = Form(''), model: str = Form('gpt-4.1-mini')):
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise ValueError('Selecione uma ficha técnica em PDF.')
    if len(product.encode('utf-8')) > MAX_JSON:
        raise ValueError('Projeto excede 2 MB.')
    case = _case(json.loads(product))
    data = await file.read(MAX_PDF_BYTES + 1)
    doc = read_pdf_bytes(data, Path(file.filename).name)
    if mode == 'local':
        candidates, rejected = local_candidates(doc), []
    elif mode == 'api':
        if consent != 'true' or not api_key.strip():
            raise ValueError('Para usar a API externa, confirme o consentimento e forneça sua chave.')
        candidates, rejected = llm_candidates(doc, api_key.strip(), model)
    else:
        raise ValueError('Método de extração inválido.')
    # No file bytes saved, and no external calls in the local mode.
    doc_id = 'DOC-' + uuid4().hex[:12].upper()
    for c in candidates:
        c['doc_id'] = doc_id
    new = upsert_document(case, {'id': doc_id, 'filename': doc.filename,
                                 'sha256': doc.digest, 'source_type': 'upload',
                                 'version': 'não informada'})
    now = time.monotonic()
    for key, cached in list(_EXTRACTED.items()):
        if now - cached['created'] > 3600:
            del _EXTRACTED[key]
    token = secrets.token_urlsafe(24)
    _EXTRACTED[token] = {'doc': doc, 'doc_id': doc_id, 'candidates': candidates,
                         'product_id': new['product_id'], 'created': now}
    return {'case': new, 'extraction_token': token, 'candidates': candidates,
            'rejected': rejected, 'pages': doc.total_pages,
            'truncated': doc.truncated, 'document': {'id': doc_id, 'filename': doc.filename, 'sha256': doc.digest}}


@app.post('/api/documents/review')
async def review_document(payload: dict):
    token = payload.get('extraction_token')
    stored = _EXTRACTED.get(token)
    if not stored or time.monotonic() - stored['created'] > 3600:
        raise ValueError('A sessão de extração expirou. Envie o documento novamente.')
    case = _case(payload.get('case'))
    if case['product_id'] != stored['product_id']:
        raise ValueError('O projeto ativo mudou após a extração. Reenvie o PDF.')
    doc_meta = next((d for d in case['documents'] if d['id'] == stored['doc_id']), None)
    if not doc_meta or doc_meta.get('sha256') != stored['doc'].digest:
        raise ValueError('A evidência documental não corresponde à extração original.')
    decisions = payload.get('decisions')
    if not isinstance(decisions, list) or len(decisions) != len(stored['candidates']):
        raise ValueError('Decisões de revisão incompletas.')
    for candidate, decision in zip(stored['candidates'], decisions):
        if not isinstance(decision, dict):
            raise ValueError('Decisão de revisão inválida.')
        if decision.get('accept'):
            # Revalidate the immutable, server-held source fragment before using it.
            check_candidate(candidate, stored['doc'])
    updated, accepted, skipped = review_apply(case, stored['doc_id'], stored['candidates'], decisions,
                                               str(payload.get('reviewer') or '').strip()[:120])
    del _EXTRACTED[token]
    return {'case': updated, 'accepted': accepted, 'skipped': skipped}


@app.post('/api/assessment')
async def assess_project(payload: dict):
    case = _case(payload.get('case'))
    return {'report': assess(case)}


@app.post('/api/assistant')
async def explain(payload: dict):
    case = _case(payload.get('case'))
    query = str(payload.get('question') or '')
    report = assess(case)  # NEVER trust client-provided statuses.
    if payload.get('mode') == 'api':
        if not payload.get('consent') or not str(payload.get('api_key') or '').strip():
            raise ValueError('Confirme o consentimento e informe uma chave API para enviar os resultados ao provedor.')
        response = llm_answer(query, report, str(payload['api_key']),
                              model=str(payload.get('model') or 'gpt-4.1-mini'))
    else:
        response = offline_answer(query, report)
    return {'response': response}


@app.get('/api/examples/{design}')
async def demo_case(design: str):
    if design not in ('A', 'B'):
        raise HTTPException(404, 'Exemplo não encontrado.')
    case = json.loads((ROOT / f'examples/integrated/Design_{design}_Entrada.json').read_text(encoding='utf-8'))
    return {'case': case, 'report': assess(case), 'synthetic': True}


@app.get('/api/snapshots')
async def snapshots():
    return {'items': storage.history()}


@app.get('/api/snapshots/{snapshot_id}')
async def open_snapshot(snapshot_id: int):
    case, report = storage.load(snapshot_id)
    return {'case': case, 'report': report}


@app.post('/api/snapshots')
async def save_snapshot(payload: dict):
    case = _case(payload.get('case'))
    # Recompute on the server, so historical saved result cannot be fabricated.
    report = assess(case) if payload.get('include_report') else None
    sid = storage.save(case, report)
    return {'id': sid, 'saved': True}


@app.post('/api/compare')
async def compare(payload: dict):
    if 'before' not in payload or 'after' not in payload:
        raise ValueError('Escolha dois relatórios para comparação.')
    return {'comparison': compare_reports(validate_report(payload['before']), validate_report(payload['after']))}


if __name__ == '__main__':
    import uvicorn
    port = int(os.environ.get('PET_CIRCULAR_PORT', '8501'))
    if os.environ.get('PET_CIRCULAR_NO_BROWSER') != '1':
        Timer(1.3, lambda: webbrowser.open(f'http://127.0.0.1:{port}')).start()
    uvicorn.run(app, host='127.0.0.1', port=port, log_level='warning')
