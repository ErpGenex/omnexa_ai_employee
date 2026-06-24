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
