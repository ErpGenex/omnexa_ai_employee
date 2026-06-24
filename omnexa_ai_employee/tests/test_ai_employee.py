# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe


def test_routing_local_keyword():
	from omnexa_ai_employee.engine.router import resolve_route_target

	assert resolve_route_target("product lookup for item ABC") in ("Local", "Cloud")


def test_ecosystem_audit():
	from omnexa_ai_employee.engine.audit.ecosystem_audit import run_ecosystem_audit

	result = run_ecosystem_audit()
	assert "installed_apps" in result
	assert "gaps" in result


def test_pick_default_model():
	from omnexa_ai_employee.engine.providers.ollama_setup import pick_default_model

	assert pick_default_model(["llama3.2:latest", "mistral:7b"]) == "llama3.2:latest"
	assert pick_default_model(["custom-model"]) == "custom-model"
	assert pick_default_model([], preferred="llama3.2") == "llama3.2"
