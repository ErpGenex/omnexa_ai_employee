# Copyright (c) 2026, Omnexa and contributors
# License: MIT

from __future__ import annotations

import frappe

from omnexa_ai_employee.engine.providers.base import BaseAIProvider
from omnexa_ai_employee.engine.providers.ollama import OllamaProvider
from omnexa_ai_employee.engine.providers.openai_client import OpenAICompatibleProvider

_PROVIDER_MAP = {
	"Ollama": OllamaProvider,
	"OpenAI": OpenAICompatibleProvider,
	"Claude": OpenAICompatibleProvider,
	"Gemini": OpenAICompatibleProvider,
	"DeepSeek": OpenAICompatibleProvider,
	"Kimi": OpenAICompatibleProvider,
	"Azure OpenAI": OpenAICompatibleProvider,
	"Open WebUI": OpenAICompatibleProvider,
	"LM Studio": OpenAICompatibleProvider,
	"vLLM": OpenAICompatibleProvider
	}


def get_provider_client(provider_name: str) -> BaseAIProvider:
	doc = frappe.get_doc("AI Provider", provider_name)
	if not doc.enabled:
		frappe.throw(frappe._("AI Provider {0} is disabled").format(provider_name))
	cls = _PROVIDER_MAP.get(doc.provider_type)
	if not cls:
		frappe.throw(frappe._("Unsupported provider type: {0}").format(doc.provider_type))
	return cls(doc)


def list_enabled_providers(route_target: str | None = None) -> list[dict]:
	filters = {"enabled": 1
	}
	if route_target:
		filters["route_target"] = route_target
	return frappe.get_all(
		"AI Provider",
		filters=filters,
		fields=["name", "provider_name", "provider_type", "route_target", "model_name", "is_default"],
		order_by="is_default desc, modified desc",
	)
