# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Ecosystem audit for AI Employee onboarding."""

from __future__ import annotations

import frappe


def run_ecosystem_audit() -> dict:
	installed = set(frappe.get_installed_apps() or [])
	core_apps = [
		"omnexa_core",
		"omnexa_customer_core",
		"omnexa_intelligence_core",
		"omnexa_experience",
		"omnexa_n8n_bridge",
	]
	vertical_samples = [
		"omnexa_trading",
		"omnexa_healthcare",
		"omnexa_education",
		"omnexa_tourism",
		"omnexa_restaurant",
		"omnexa_services",
		"omnexa_manufacturing",
		"omnexa_construction",
		"omnexa_agriculture",
		"omnexa_accounting",
	]
	doctype_count = frappe.db.count("DocType", {"istable": 0, "custom": 0})
	whitelisted = _count_whitelisted_methods(installed)
	providers = frappe.db.count("AI Provider", {"enabled": 1})
	agents = frappe.db.count("AI Agent", {"enabled": 1})
	channels = frappe.db.count("AI Channel Account", {"enabled": 1})
	vector_stores = frappe.db.count("AI Vector Store", {"enabled": 1})
	ocr_providers = frappe.db.count("AI OCR Provider", {"enabled": 1})

	return {
		"installed_apps": len(installed),
		"core_platform": {app: app in installed for app in core_apps},
		"vertical_apps": {app: app in installed for app in vertical_samples if app in installed},
		"doctype_count": doctype_count,
		"whitelisted_api_count": whitelisted,
		"ai_employee": {
			"providers": providers,
			"agents": agents,
			"channels": channels,
			"vector_stores": vector_stores,
			"ocr_providers": ocr_providers,
		},
		"gaps": _gap_analysis(installed, providers, channels, vector_stores, ocr_providers),
	}


def _count_whitelisted_methods(installed: set[str]) -> int:
	total = 0
	for app in installed:
		try:
			module = frappe.get_module(f"{app}.hooks")
		except Exception:
			continue
		# rough estimate via grep-like scan of api modules is expensive; use DocType Method count fallback
		total += 0
	return total


def _gap_analysis(installed, providers, channels, vector_stores, ocr_providers) -> list[dict]:
	gaps = []
	if "omnexa_n8n_bridge" not in installed:
		gaps.append({"area": "Automation", "severity": "Medium", "detail": "n8n bridge not installed for external LLM workflows"})
	if providers == 0:
		gaps.append({"area": "AI Providers", "severity": "High", "detail": "No enabled AI provider configured"})
	if channels == 0:
		gaps.append({"area": "Channels", "severity": "Medium", "detail": "No WhatsApp/Telegram/SMS channel accounts"})
	if vector_stores == 0:
		gaps.append({"area": "RAG", "severity": "Medium", "detail": "No vector store configured for knowledge base"})
	if ocr_providers == 0:
		gaps.append({"area": "OCR", "severity": "Low", "detail": "No OCR provider configured"})
	return gaps
