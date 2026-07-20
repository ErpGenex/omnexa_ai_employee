# Copyright (c) 2026, Omnexa and contributors
# License: MIT

from __future__ import annotations

import json

import frappe
import requests

from omnexa_ai_employee.engine.providers.base import AICompletionResult, BaseAIProvider
from omnexa_ai_employee.engine.providers.ollama_setup import resolve_ollama_base_url


class OllamaProvider(BaseAIProvider):
	provider_type = "Ollama"

	def complete(self, *, messages: list[dict], temperature: float | None = None, max_tokens: int | None = None) -> AICompletionResult:
		base_url = resolve_ollama_base_url(self.doc.base_url)
		model = self.doc.model_name or "llama3"
		payload = {
			"model": model,
			"messages": messages,
			"stream": False,
			"options": {
				"temperature": float(temperature if temperature is not None else self.doc.temperature or 0.2),
				"num_predict": int(max_tokens or self.doc.max_tokens or 1024)}
	}
		timeout = int(self.doc.timeout_seconds or 60)
		resp = requests.post(f"{base_url}/api/chat", json=payload, timeout=timeout)
		resp.raise_for_status()
		data = resp.json()
		text = (data.get("message") or {}).get("content") or data.get("response") or ""
		return AICompletionResult(text=text.strip(), provider=self.doc.name, model=model, route="Local", raw=data)

	def health_check(self) -> dict:
		base_url = resolve_ollama_base_url(self.doc.base_url)
		try:
			resp = requests.get(f"{base_url}/api/tags", timeout=5)
			resp.raise_for_status()
			models = [m.get("name") for m in (resp.json().get("models") or [])]
			return {"ok": True, "models": models[:20]
	}
		except Exception as exc:
			return {"ok": False, "message": str(exc)
	}
