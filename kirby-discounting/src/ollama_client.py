"""Thin wrapper around the Ollama HTTP API.

Handles generation, retries/timeouts, and explicit keep_alive control so that
only one model needs to stay resident in memory at a time on an 8GB machine.

(Identical to ../temporal-discounting/src/ollama_client.py -- kept as a
separate copy so this project has no cross-directory import dependency.)
"""

import time
import requests


class OllamaClient:
    def __init__(self, base_url, request_timeout_s, max_retries, retry_backoff_s):
        self.base_url = base_url.rstrip("/")
        self.request_timeout_s = request_timeout_s
        self.max_retries = max_retries
        self.retry_backoff_s = retry_backoff_s

    def generate(self, model_name, system_prompt, user_prompt, temperature, num_predict, keep_alive):
        """Single-turn completion. Returns the raw response text (str).

        Raises requests.RequestException if all retries are exhausted.
        """
        request_payload = {
            "model": model_name,
            "system": system_prompt,
            "prompt": user_prompt,
            "stream": False,
            "keep_alive": keep_alive,
            # Top-level (not options): disables thinking for qwen3:8b etc.
            "think": False,
            "options": {
                "temperature": temperature,
                "num_predict": num_predict,
            },
        }

        last_error = None
        for attempt_index in range(self.max_retries):
            try:
                http_response = requests.post(
                    f"{self.base_url}/api/generate",
                    json=request_payload,
                    timeout=self.request_timeout_s,
                )
                http_response.raise_for_status()
                response_json = http_response.json()
                return response_json.get("response", "")
            except requests.RequestException as request_error:
                last_error = request_error
                sleep_seconds = self.retry_backoff_s * (2 ** attempt_index)
                time.sleep(sleep_seconds)

        raise last_error

    def chat(self, model_name, system_prompt, messages, temperature, num_predict, keep_alive):
        """Multi-turn completion via /api/chat. `messages` is a list of
        {"role": "user"|"assistant", "content": str} turns (e.g. one-shot/
        two-shot worked examples followed by the real trial); the system
        prompt is passed separately and always placed first. Returns the raw
        text (str) of the final assistant turn.

        Raises requests.RequestException if all retries are exhausted.
        """
        full_messages = [{"role": "system", "content": system_prompt}] + list(messages)
        request_payload = {
            "model": model_name,
            "messages": full_messages,
            "stream": False,
            "keep_alive": keep_alive,
            # Top-level (not options): disables thinking for qwen3:8b etc.
            "think": False,
            "options": {
                "temperature": temperature,
                "num_predict": num_predict,
            },
        }

        last_error = None
        for attempt_index in range(self.max_retries):
            try:
                http_response = requests.post(
                    f"{self.base_url}/api/chat",
                    json=request_payload,
                    timeout=self.request_timeout_s,
                )
                http_response.raise_for_status()
                response_json = http_response.json()
                return response_json.get("message", {}).get("content", "")
            except requests.RequestException as request_error:
                last_error = request_error
                sleep_seconds = self.retry_backoff_s * (2 ** attempt_index)
                time.sleep(sleep_seconds)

        raise last_error

    def unload_model(self, model_name):
        """Evicts a model from memory immediately (keep_alive=0) before switching models."""
        requests.post(
            f"{self.base_url}/api/generate",
            json={"model": model_name, "prompt": "", "keep_alive": 0},
            timeout=self.request_timeout_s,
        )
