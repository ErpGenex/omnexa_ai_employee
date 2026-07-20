# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Ollama discovery, model selection, and provider bootstrap."""

from __future__ import annotations

import frappe
import requests

DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
DEFAULT_OLLAMA_PROVIDER = "ollama-local"
PREFERRED_MODELS = (
	"llama3.2",
	"llama3.1",
	"llama3",
	"mistral",
	"qwen2.5",
	"gemma2",
	"phi3",
)


def _candidate_ollama_urls(explicit: str | None = None) -> list[str]:
	urls: list[str] = []
	if explicit:
		urls.append(explicit.rstrip("/"))
	site_url = (frappe.conf.get("ollama_base_url") or "").strip()
	if site_url:
		urls.append(site_url.rstrip("/"))
	settings_url = frappe.db.get_single_value("AI Employee Settings", "ollama_base_url")
	if settings_url:
		urls.append(str(settings_url).rstrip("/"))
	for row in frappe.get_all("AI Provider", filters={"provider_type": "Ollama"
	}, fields=["base_url"]):
		if row.base_url:
			urls.append(str(row.base_url).rstrip("/"))
	urls.append(DEFAULT_OLLAMA_URL)
	seen: set[str] = set()
	ordered: list[str] = []
	for url in urls:
		if url and url not in seen:
			seen.add(url)
			ordered.append(url)
	return ordered


def resolve_ollama_base_url(explicit: str | None = None) -> str:
	candidates = _candidate_ollama_urls(explicit)
	return candidates[0] if candidates else DEFAULT_OLLAMA_URL


def probe_ollama(base_url: str | None = None, *, timeout: int = 5) -> dict:
	if base_url:
		url = base_url.rstrip("/")
		try:
			resp = requests.get(f"{url}/api/tags", timeout=timeout)
			resp.raise_for_status()
			models = [m.get("name") for m in (resp.json().get("models") or []) if m.get("name")]
			return {"ok": True, "base_url": url, "models": models
	}
		except Exception as exc:
			return {"ok": False, "base_url": url, "message": str(exc), "models": []
	}

	last_error = ""
	for url in _candidate_ollama_urls():
		try:
			resp = requests.get(f"{url}/api/tags", timeout=timeout)
			resp.raise_for_status()
			models = [m.get("name") for m in (resp.json().get("models") or []) if m.get("name")]
			return {"ok": True, "base_url": url, "models": models
	}
		except Exception as exc:
			last_error = str(exc)
	return {"ok": False, "base_url": _candidate_ollama_urls()[0], "message": last_error, "models": []
	}


def pick_default_model(models: list[str], preferred: str | None = None) -> str:
	if preferred and preferred in models:
		return preferred
	if preferred:
		for model in models:
			if model == preferred or model.startswith(f"{preferred}:"):
				return model
	for candidate in PREFERRED_MODELS:
		for model in models:
			base = model.split(":", 1)[0]
			if base == candidate or model.startswith(f"{candidate}:"):
				return model
	return models[0] if models else preferred or "llama3.2"


def bootstrap_ollama_provider(*, save: bool = True) -> dict:
	"""Ensure default Local Ollama provider exists and auto-pick an installed model when reachable."""
	probe = probe_ollama()
	base_url = probe["base_url"] if probe.get("ok") else resolve_ollama_base_url()
	model = pick_default_model(probe.get("models") or [])
	settings_model = frappe.db.get_single_value("AI Employee Settings", "ollama_default_model")
	if settings_model:
		model = pick_default_model(probe.get("models") or [], preferred=settings_model)

	# Prefer upgrading an existing Ollama provider on the same reachable host.
	existing_name = None
	if probe.get("ok"):
		for row in frappe.get_all(
			"AI Provider",
			filters={"provider_type": "Ollama", "enabled": 1
	},
			fields=["name", "base_url"],
		):
			if (row.base_url or "").rstrip("/") == base_url.rstrip("/"):
				existing_name = row.name
				break
		if not existing_name and frappe.db.exists("AI Provider", "ollama"):
			existing_name = "ollama"

	target_name = existing_name or DEFAULT_OLLAMA_PROVIDER
	if frappe.db.exists("AI Provider", target_name):
		doc = frappe.get_doc("AI Provider", target_name)
		changed = False
		if doc.base_url != base_url:
			doc.base_url = base_url
			changed = True
		if probe.get("ok") and doc.model_name != model:
			doc.model_name = model
			changed = True
		if not doc.enabled:
			doc.enabled = 1
			changed = True
		if not doc.is_default:
			doc.is_default = 1
			changed = True
		if changed and save:
			doc.save(ignore_permissions=True)
		if save and frappe.db.get_single_value("AI Employee Settings", "ollama_base_url") != base_url:
			frappe.db.set_single_value("AI Employee Settings", "ollama_base_url", base_url)
		return {
			"created": False,
			"provider": doc.name,
			"base_url": doc.base_url,
			"model_name": doc.model_name,
			"ollama_reachable": probe.get("ok"),
			"models": probe.get("models") or []
	}

	doc = frappe.get_doc(
		{
			"doctype": "AI Provider",
			"provider_name": DEFAULT_OLLAMA_PROVIDER,
			"provider_type": "Ollama",
			"route_target": "Local",
			"enabled": 1,
			"is_default": 1,
			"base_url": base_url,
			"model_name": model,
			"temperature": 0.2,
			"max_tokens": 1024,
			"timeout_seconds": 120
	}
	)
	if save:
		doc.insert(ignore_permissions=True)
	return {
		"created": True,
		"provider": doc.name,
		"base_url": base_url,
		"model_name": model,
		"ollama_reachable": probe.get("ok"),
		"models": probe.get("models") or []
	}
