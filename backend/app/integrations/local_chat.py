"""Chat en Ollama, accesible solo en la red privada de Compose."""
import asyncio
import json

import httpx
from pydantic import ValidationError

from app.integrations.ai import AIError, CHAT_INSTRUCTIONS, ConversationPlan, MAX_RESPONSE_BYTES, conversation_schema

MODEL = 'qwen3:4b-instruct'
OLLAMA_URL = 'http://ollama:11434'


class OllamaChat:
    def __init__(self, transport=None):
        self.transport = transport
        self.busy = False

    async def ready(self):
        try:
            async with httpx.AsyncClient(transport=self.transport, trust_env=False, timeout=2) as client:
                response = await client.get(f'{OLLAMA_URL}/api/tags')
                response.raise_for_status()
                return any(item['name'] == MODEL for item in response.json()['models'])
        except (httpx.HTTPError, ValueError, TypeError, KeyError):
            return False

    async def conversation_plan(self, context):
        if self.busy:
            raise AIError('ai_busy')
        self.busy = True
        try:
            async with asyncio.timeout(110):
                async with httpx.AsyncClient(transport=self.transport, trust_env=False, timeout=110) as client:
                    async with client.stream('POST', f'{OLLAMA_URL}/api/chat', json={
                        'model': MODEL,
                        'stream': False,
                        'format': conversation_schema(context['library_requested'], suggestion_limit=2),
                        'options': {'num_ctx': 8192, 'num_predict': 1100, 'temperature': 0.5},
                        'messages': [
                            {'role': 'system', 'content': CHAT_INSTRUCTIONS + ' Para este chat, da como máximo dos sugerencias y expresa cada razón en una frase breve.'},
                            {'role': 'user', 'content': json.dumps(context, ensure_ascii=False)},
                        ],
                    }) as response:
                        if response.status_code == 404:
                            raise AIError('local_model_missing')
                        response.raise_for_status()
                        raw = bytearray()
                        async for chunk in response.aiter_bytes():
                            raw.extend(chunk)
                            if len(raw) > MAX_RESPONSE_BYTES:
                                raise AIError('ai_invalid_response')
                payload = json.loads(raw)
                if payload.get('done') is not True:
                    raise AIError('ai_invalid_response')
                return ConversationPlan.model_validate_json(payload['message']['content']).model_dump()
        except (TimeoutError, httpx.TimeoutException):
            raise AIError('ai_timeout') from None
        except httpx.HTTPError:
            raise AIError('local_model_unavailable') from None
        except (AttributeError, ValueError, TypeError, KeyError, ValidationError):
            raise AIError('ai_invalid_response') from None
        finally:
            self.busy = False
