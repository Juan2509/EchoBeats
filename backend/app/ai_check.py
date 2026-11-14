"""Prueba P20 voluntaria. Sin --live solo informa; nunca se ejecuta desde pytest."""
import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from uuid import uuid4
from app.config import Settings
from app.integrations.ai import AIError, OpenAIProvider, status

CONTROL_TEXT = 'Fragmento sintético: onda sinusoidal de 220 Hz, sin voces.'
CONTROL_QUERY = 'Describe únicamente los datos documentados y cita literalmente la evidencia.'


async def probe(settings):
    # --live es autorización explícita de esta ejecución, sin activar la app de forma permanente.
    config = settings.model_copy(update={'ai_enabled': True, 'ai_rate_limit_retries': 0})
    provider = OpenAIProvider(config)
    receipt = {'schema_version': 1, 'time_utc': datetime.now(timezone.utc).isoformat(),
        'provider': 'openai', 'real_api': True, 'status': 'started', 'calls': [],
        'input_sha256': hashlib.sha256(CONTROL_TEXT.encode()).hexdigest(),
        'input_kind': 'fixed_synthetic_text_only', 'audio_sent': False,
        'model_key': provider.model_key, 'generation_model': config.ai_generation_model,
        'automatic_retries': 0}
    if not config.openai_api_key.get_secret_value().strip():
        raise AIError('ai_not_configured')
    try:
        embedding = await provider.embed(CONTROL_TEXT)
        receipt['calls'].append({'operation': 'embedding', 'validated': True, 'dimensions': len(embedding['vector']), 'usage': embedding['usage']})
        generated = await provider.generate(CONTROL_QUERY, [{'source_id': 'p20-control', 'version': 1, 'text': CONTROL_TEXT}])
        receipt['calls'].append({'operation': 'generation', 'validated': True, 'model': generated['model'], 'usage': generated['usage'], 'prompt_version': generated['prompt_version']})
        receipt['status'] = 'verified'
    except AIError as exc:
        receipt['status'] = 'failed'
        receipt['error_code'] = exc.code
        receipt['provider_error_code'] = exc.provider_code
        receipt['notice'] = 'Una llamada fallida o sin respuesta confirmada podría tener consumo; no se repitió automáticamente.'
    destination = Path(settings.media_root).parent / 'ai_checks'
    destination.mkdir(parents=True, exist_ok=True)
    path = destination / f'p20_{datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")}_{uuid4().hex[:8]}.json'
    with path.open('x', encoding='utf-8') as stream:
        json.dump(receipt, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'status': receipt['status'], 'error_code': receipt.get('error_code'), 'validated_calls': len(receipt['calls']), 'receipt': str(path)}, ensure_ascii=False))
    return 0 if receipt['status'] == 'verified' else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true', help='Envía texto sintético fijo a OpenAI, hasta dos llamadas facturables sin reintento automático. No envía biblioteca ni audios.')
    args = parser.parse_args()
    settings = Settings()
    if not args.live:
        print(json.dumps(status(settings), ensure_ascii=False))
        return 0
    try:
        return asyncio.run(probe(settings))
    except AIError as exc:
        print(json.dumps({'status': 'not_run', 'error_code': exc.code, 'message': str(exc)}, ensure_ascii=False))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
