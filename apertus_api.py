import openai
import json
import time
from typing import List, Dict, Any
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
import threading

class ApertusAPI:
    def __init__(self, config_path: str = "config.json"):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        self.api_keys = self.config['api_keys']
        self.base_url = self.config['api_base_url']
        self.model_name = self.config['model_name']
        self.current_key_index = 0
        self.key_lock = threading.Lock()

    def get_next_api_key(self) -> str:
        """Round-robin through API keys for load balancing"""
        with self.key_lock:
            key = self.api_keys[self.current_key_index]
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            return key

    def create_client(self, api_key: str = None) -> openai.OpenAI:
        """Create OpenAI client with specific API key"""
        if api_key is None:
            api_key = self.get_next_api_key()

        return openai.OpenAI(
            api_key=api_key,
            base_url=self.base_url
        )

    def call_model(self, messages: List[Dict[str, str]], api_key: str = None,
                   temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """Synchronous API call to Apertus model"""
        client = self.create_client(api_key)

        try:
            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error calling API: {e}")
            return None

    async def acall_model(self, messages: List[Dict[str, str]], api_key: str = None,
                          temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """Asynchronous API call to Apertus model"""
        if api_key is None:
            api_key = self.get_next_api_key()

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        url = f"{self.base_url}/chat/completions"

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result['choices'][0]['message']['content']
                    else:
                        print(f"Error: {response.status}")
                        return None
            except Exception as e:
                print(f"Error in async call: {e}")
                return None

    def translate_text(self, text: str, target_language: str, language_name: str) -> str:
        """Translate text to target language"""
        # Load translation prompt template
        try:
            with open('translation_prompt.txt', 'r', encoding='utf-8') as f:
                prompt_template = f.read()
        except FileNotFoundError:
            # Fallback to simple prompt
            prompt_template = """Translate the following text to {target_language}.
Only provide the translation without any explanation.

Text: {sentence}"""

        translation_prompt = prompt_template.format(
            original_language="English",
            target_language=language_name,
            sentence=text
        )

        messages = [
            {"role": "user", "content": translation_prompt}
        ]

        response = self.call_model(messages, temperature=0.3)

        # Parse translation from response
        if response and "Translation:" in response:
            translation = response.split("Translation:")[1].strip()
            return translation
        return response

    async def atranslate_text(self, text: str, target_language: str, language_name: str) -> str:
        """Async translate text to target language"""
        # Load translation prompt template
        try:
            with open('translation_prompt.txt', 'r', encoding='utf-8') as f:
                prompt_template = f.read()
        except FileNotFoundError:
            # Fallback to simple prompt
            prompt_template = """Translate the following text to {target_language}.
Only provide the translation without any explanation.

Text: {sentence}"""

        translation_prompt = prompt_template.format(
            original_language="English",
            target_language=language_name,
            sentence=text
        )

        messages = [
            {"role": "user", "content": translation_prompt}
        ]

        response = await self.acall_model(messages, temperature=0.3)

        # Parse translation from response
        if response and "Translation:" in response:
            translation = response.split("Translation:")[1].strip()
            return translation
        return response