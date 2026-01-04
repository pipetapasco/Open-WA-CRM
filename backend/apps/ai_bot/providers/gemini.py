"""
Google Gemini AI Provider.

Implementación del proveedor de IA para Google Gemini Pro
usando la API REST v1beta.
"""

from typing import Any

import httpx

from .base import AIProviderError, BaseAIProvider, ChatMessage


class GeminiProvider(BaseAIProvider):
    API_BASE_URL = 'https://generativelanguage.googleapis.com/v1beta'
    MODEL = 'gemini-2.5-flash'
    TIMEOUT = 60.0

    def generate_response(self, history: list[ChatMessage]) -> str:
        try:
            payload = self._build_payload(history)

            url = f'{self.API_BASE_URL}/models/{self.MODEL}:generateContent'

            headers = {
                'Content-Type': 'application/json',
            }

            params = {'key': self.api_key}

            with httpx.Client(timeout=self.TIMEOUT) as client:
                response = client.post(url, json=payload, headers=headers, params=params)

            if response.status_code != 200:
                error_detail = self._parse_error(response)
                raise AIProviderError(f'API returned {response.status_code}: {error_detail}', provider='gemini')

            data = response.json()
            text = self._extract_response_text(data)

            if not text:
                raise AIProviderError('Empty response from Gemini', provider='gemini')

            return text

        except httpx.TimeoutException as e:
            raise AIProviderError('Request timeout', provider='gemini', original_error=e)

        except httpx.RequestError as e:
            raise AIProviderError(f'Request failed: {e}', provider='gemini', original_error=e)

        except AIProviderError:
            raise

        except Exception as e:
            raise AIProviderError(f'Unexpected error: {e}', provider='gemini', original_error=e)

    def _build_payload(self, history: list[ChatMessage]) -> dict[str, Any]:
        contents = []

        if self.system_prompt:
            contents.append({'role': 'user', 'parts': [{'text': f'[System Instructions]: {self.system_prompt}'}]})
            contents.append({'role': 'model', 'parts': [{'text': 'Entendido. Seguiré estas instrucciones.'}]})

        for msg in history:
            role = msg.get('role', 'user')
            content = msg.get('content', '')

            gemini_role = 'user' if role == 'user' else 'model'

            if content.strip():
                contents.append({'role': gemini_role, 'parts': [{'text': content}]})

        payload = {
            'contents': contents,
            'generationConfig': {
                'temperature': 0.7,
                'topP': 0.95,
                'topK': 40,
                'maxOutputTokens': 1024,
            },
            'safetySettings': [
                {'category': 'HARM_CATEGORY_HARASSMENT', 'threshold': 'BLOCK_MEDIUM_AND_ABOVE'},
                {'category': 'HARM_CATEGORY_HATE_SPEECH', 'threshold': 'BLOCK_MEDIUM_AND_ABOVE'},
                {'category': 'HARM_CATEGORY_SEXUALLY_EXPLICIT', 'threshold': 'BLOCK_MEDIUM_AND_ABOVE'},
                {'category': 'HARM_CATEGORY_DANGEROUS_CONTENT', 'threshold': 'BLOCK_MEDIUM_AND_ABOVE'},
            ],
        }

        return payload

    def _extract_response_text(self, data: dict[str, Any]) -> str:
        try:
            candidates = data.get('candidates', [])
            if not candidates:
                return ''

            content = candidates[0].get('content', {})
            parts = content.get('parts', [])

            if not parts:
                return ''

            text_parts = [part.get('text', '') for part in parts if 'text' in part]
            return ''.join(text_parts).strip()

        except (KeyError, IndexError, TypeError):
            return ''

    def _parse_error(self, response: httpx.Response) -> str:
        try:
            data = response.json()
            error = data.get('error', {})
            return error.get('message', response.text[:200])
        except Exception:
            return response.text[:200] if response.text else 'Unknown error'
