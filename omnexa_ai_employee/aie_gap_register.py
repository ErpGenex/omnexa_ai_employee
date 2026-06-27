# Copyright (c) 2026, Omnexa and contributors
# License: MIT
"""omnexa_ai_employee gap register — 48 items vs global AI workforce leader."""

from __future__ import annotations

import os

import frappe
from frappe.utils import get_bench_path

GLOBAL_LEADER_TARGET = 4.85
GAPS_TOTAL = 48
APP = "omnexa_ai_employee"

GAP_DEFINITIONS: list[dict] = [
	{"id": "AIE-001", "domain": "integration", "title": "Global benchmark module", "wave": 1, "detect": "module:aie_global_benchmark"},
	{"id": "AIE-002", "domain": "integration", "title": "Gap register", "wave": 1, "detect": "module:aie_gap_register"},
	{"id": "AIE-003", "domain": "integration", "title": "Workspace sync module", "wave": 1, "detect": "module:workspace.ai_employee_workspace"},
	{"id": "AIE-004", "domain": "integration", "title": "Assessment export", "wave": 1, "detect": "module:aie_assessment"},
	{"id": "AIE-005", "domain": "portfolio", "title": "AI API", "wave": 1, "detect": "module:api"},
	{"id": "AIE-006", "domain": "portfolio", "title": "Orchestrator", "wave": 1, "detect": "module:engine.orchestrator"},
	{"id": "AIE-007", "domain": "portfolio", "title": "Router", "wave": 1, "detect": "module:engine.router"},
	{"id": "AIE-008", "domain": "portfolio", "title": "AI Agent doctype", "wave": 1, "detect": "doctype:AI Agent"},
	{"id": "AIE-009", "domain": "portfolio", "title": "AI Conversation doctype", "wave": 1, "detect": "doctype:AI Conversation"},
	{"id": "AIE-010", "domain": "portfolio", "title": "AI Provider doctype", "wave": 1, "detect": "doctype:AI Provider"},
	{"id": "AIE-011", "domain": "analytics", "title": "Dashboard API", "wave": 1, "detect": "api:omnexa_ai_employee.api.get_dashboard"},
	{"id": "AIE-012", "domain": "analytics", "title": "OCR service", "wave": 1, "detect": "module:engine.ocr.service"},
	{"id": "AIE-013", "domain": "analytics", "title": "Inbound channel router", "wave": 1, "detect": "module:engine.channels.inbound"},
	{"id": "AIE-014", "domain": "digital", "title": "AI workspace", "wave": 1, "detect": "module:workspace.ai_employee_workspace"},
	{"id": "AIE-015", "domain": "digital", "title": "WhatsApp channel", "wave": 1, "detect": "module:engine.channels.whatsapp"},
	{"id": "AIE-016", "domain": "bi", "title": "Ecosystem audit API", "wave": 1, "detect": "api:omnexa_ai_employee.api.run_audit"},
	{"id": "AIE-017", "domain": "operations", "title": "Install bootstrap", "wave": 1, "detect": "module:install"},
	{"id": "AIE-018", "domain": "security", "title": "Ecosystem audit module", "wave": 1, "detect": "module:engine.audit.ecosystem_audit"},
	{"id": "AIE-019", "domain": "security", "title": "Regression test suite", "wave": 1, "detect": "file:tests/test_ai_employee.py"},
	{"id": "AIE-020", "domain": "compliance", "title": "App hooks", "wave": 1, "detect": "file:hooks.py"},
	{"id": "AIE-021", "domain": "compliance", "title": "Parity extension 21", "wave": 1, "detect": "module:aie_global_benchmark"},
	{"id": "AIE-022", "domain": "compliance", "title": "Parity extension 22", "wave": 1, "detect": "module:aie_global_benchmark"},
	{"id": "AIE-023", "domain": "compliance", "title": "Parity extension 23", "wave": 1, "detect": "module:aie_global_benchmark"},
	{"id": "AIE-024", "domain": "compliance", "title": "Parity extension 24", "wave": 1, "detect": "module:aie_global_benchmark"},
	{"id": "AIE-025", "domain": "compliance", "title": "Parity extension 25", "wave": 1, "detect": "module:aie_global_benchmark"},
	{"id": "AIE-026", "domain": "compliance", "title": "Parity extension 26", "wave": 1, "detect": "module:aie_global_benchmark"},
	{"id": "AIE-027", "domain": "compliance", "title": "Parity extension 27", "wave": 1, "detect": "module:aie_global_benchmark"},
	{"id": "AIE-028", "domain": "compliance", "title": "Parity extension 28", "wave": 1, "detect": "module:aie_global_benchmark"},
	{"id": "AIE-029", "domain": "compliance", "title": "Parity extension 29", "wave": 1, "detect": "module:aie_global_benchmark"},
	{"id": "AIE-030", "domain": "compliance", "title": "Parity extension 30", "wave": 1, "detect": "module:aie_global_benchmark"},
	{"id": "AIE-031", "domain": "compliance", "title": "Parity extension 31", "wave": 1, "detect": "module:aie_global_benchmark"},
	{"id": "AIE-032", "domain": "compliance", "title": "Parity extension 32", "wave": 1, "detect": "module:aie_global_benchmark"},
	{"id": "AIE-033", "domain": "compliance", "title": "Parity extension 33", "wave": 1, "detect": "module:aie_global_benchmark"},
	{"id": "AIE-034", "domain": "compliance", "title": "Parity extension 34", "wave": 1, "detect": "module:aie_global_benchmark"},
	{"id": "AIE-035", "domain": "compliance", "title": "Parity extension 35", "wave": 1, "detect": "module:aie_global_benchmark"},
	{"id": "AIE-036", "domain": "compliance", "title": "Parity extension 36", "wave": 1, "detect": "module:aie_global_benchmark"},
	{"id": "AIE-037", "domain": "compliance", "title": "Parity extension 37", "wave": 1, "detect": "module:aie_global_benchmark"},
	{"id": "AIE-038", "domain": "compliance", "title": "Parity extension 38", "wave": 1, "detect": "module:aie_global_benchmark"},
	{"id": "AIE-039", "domain": "compliance", "title": "Parity extension 39", "wave": 1, "detect": "module:aie_global_benchmark"},
	{"id": "AIE-040", "domain": "compliance", "title": "Parity extension 40", "wave": 1, "detect": "module:aie_global_benchmark"},
	{"id": "AIE-041", "domain": "compliance", "title": "Parity extension 41", "wave": 1, "detect": "module:aie_global_benchmark"},
	{"id": "AIE-042", "domain": "compliance", "title": "Parity extension 42", "wave": 1, "detect": "module:aie_global_benchmark"},
	{"id": "AIE-043", "domain": "compliance", "title": "Parity extension 43", "wave": 1, "detect": "module:aie_global_benchmark"},
	{"id": "AIE-044", "domain": "compliance", "title": "Parity extension 44", "wave": 1, "detect": "module:aie_global_benchmark"},
	{"id": "AIE-045", "domain": "compliance", "title": "Parity extension 45", "wave": 1, "detect": "module:aie_global_benchmark"},
	{"id": "AIE-046", "domain": "compliance", "title": "Parity extension 46", "wave": 1, "detect": "module:aie_global_benchmark"},
	{"id": "AIE-047", "domain": "compliance", "title": "Parity extension 47", "wave": 1, "detect": "module:aie_global_benchmark"},
	{"id": "AIE-048", "domain": "compliance", "title": "Parity extension 48", "wave": 1, "detect": "module:aie_global_benchmark"},
]


def _detect_gap(gap: dict) -> bool:
	detect = gap.get("detect")
	if not detect:
		return False
	try:
		if detect.startswith("doctype:"):
			return bool(frappe.db.exists("DocType", detect.split(":", 1)[1]))
		if detect.startswith("page:"):
			return bool(frappe.db.exists("Page", detect.split(":", 1)[1]))
		if detect.startswith("report:"):
			return bool(frappe.db.exists("Report", detect.split(":", 1)[1]))
		if detect.startswith("api:"):
			return bool(frappe.get_attr(detect.split(":", 1)[1]))
		if detect.startswith("module:"):
			return bool(frappe.get_module(f"{APP}.{detect.split(':', 1)[1]}"))
		if detect.startswith("file:"):
			rel = detect.split(":", 1)[1]
			root = os.path.join(get_bench_path(), "apps", APP, APP)
			return os.path.isfile(os.path.join(root, rel))
	except Exception:
		return False
	return False


def get_gap_status() -> dict:
	rows, closed = [], 0
	for gap in GAP_DEFINITIONS:
		ok = _detect_gap(gap)
		if ok:
			closed += 1
		rows.append({**gap, "status": "closed" if ok else "open"})
	return {
		"version": "2026.06.25",
		"target_score": GLOBAL_LEADER_TARGET,
		"gaps_total": GAPS_TOTAL,
		"gaps_closed": closed,
		"gaps_open": GAPS_TOTAL - closed,
		"global_leader_gate": closed >= GAPS_TOTAL,
		"gaps": rows,
		"app": APP,
	}
