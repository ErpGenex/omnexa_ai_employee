# Copyright (c) 2026, Omnexa and contributors
# License: MIT

from __future__ import annotations

import json

import frappe
import requests

from omnexa_ai_employee.engine.providers.base import AICompletionResult, BaseAIProvider


class OpenAICompatibleProvider(BaseAIProvider):
	"""OpenAI, DeepSeek, Kimi, Azure OpenAI (OpenAI-compatible chat API)."""

	provider_type = "OpenAI Compatible"

	def _headers(self) -> dict:
		api_key = self.doc.get_password("api_key") if self.doc.api_key else None
		if not api_key:
			frappe.throw(frappe._("API key is required for provider {0}").format(self.doc.name))
		headers = {"Authorization": f"Bearer {api_key
	}", "Content-Type": "application/json"
	}
		if self.doc.api_version:
			headers["api-version"] = self.doc.api_version
		return headers

	def _endpoint(self) -> str:
		base = (self.doc.base_url or "https://api.openai.com/v1").rstrip("/")
		if base.endswith("/chat/completions"):
			return base
		return f"{base}/chat/completions"

	def complete(self, *, messages: list[dict], temperature: float | None = None, max_tokens: int | None = None) -> AICompletionResult:
		model = self.doc.model_name or "gpt-4o-mini"
		payload = {
			"model": model,
			"messages": messages,
			"temperature": float(temperature if temperature is not None else self.doc.temperature or 0.2),
			"max_tokens": int(max_tokens or self.doc.max_tokens or 1024)
	}
		resp = requests.post(
			self._endpoint(),
			headers=self._headers(),
			data=json.dumps(payload),
			timeout=int(self.doc.timeout_seconds or 90),
		)
		resp.raise_for_status()
		data = resp.json()
		choice = (data.get("choices") or [{}])[0]
		text = ((choice.get("message") or {}).get("content") or "").strip()
		return AICompletionResult(
			text=text,
			provider=self.doc.name,
			model=model,
			route="Cloud",
			usage=data.get("usage"),
			raw=data,
		)

	def health_check(self) -> dict:
		if not self.doc.api_key:
			return {"ok": False, "message": "API key not configured"
	}
		return {"ok": True, "endpoint": self._endpoint(), "model": self.doc.model_name
	}
