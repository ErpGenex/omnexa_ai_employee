# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""AI Employee workspace — focused desk (no global ERP catalog padding)."""

from __future__ import annotations

import json
from typing import Any

import frappe

from omnexa_core.omnexa_core.vertical_workspace_sync import (
	build_content_from_link_rows,
	build_shortcuts_from_link_rows,
	drop_missing_workspace_dashboard_links,
)

WORKSPACE_NAME = "AI Employee"
WORKSPACE_ICON = "es-line-zap"

WORKSPACE_SECTIONS = [
	(
		"🤖 AI Employee",
		[
			("Page", "ai-employee-workcenter", "AI Workcenter"),
			("DocType", "AI Agent", "AI Agents"),
			("DocType", "AI Conversation", "Conversations"),
		],
	),
	(
		"🧠 Providers & Routing",
		[
			("DocType", "AI Provider", "AI Providers"),
			("DocType", "AI Routing Rule", "Routing Rules"),
			("DocType", "AI Vector Store", "Vector Stores"),
			("DocType", "AI OCR Provider", "OCR Providers"),
		],
	),
	(
		"📡 Channels",
		[
			("DocType", "AI Channel Account", "Channel Accounts"),
		],
	),
	(
		"⚙️ Settings",
		[
			("DocType", "AI Employee Settings", "AI Employee Settings"),
		],
	),
]


def _link_exists(link_type: str, link_to: str) -> bool:
	if link_type == "DocType":
		return bool(frappe.db.exists("DocType", link_to))
	if link_type == "Report":
		return bool(frappe.db.exists("Report", link_to))
	if link_type == "Page":
		return bool(frappe.db.exists("Page", link_to))
	return False


def _build_link_rows() -> list[dict[str, Any]]:
	"""Curated AI Employee links only — skip global ERP catalog merge."""
	rows: list[dict[str, Any]] = []
	seen: set[tuple[str, str]] = set()
	for section_label, items in WORKSPACE_SECTIONS:
		valid = [(t, to, label) for t, to, label in items if _link_exists(t, to)]
		if not valid:
			continue
		rows.append({"label": section_label, "type": "Card Break", "link_type": "DocType"})
		for link_type, link_to, label in valid:
			key = (link_type, link_to)
			if key in seen:
				continue
			seen.add(key)
			row: dict[str, Any] = {
				"type": "Link",
				"label": label,
				"link_type": link_type,
				"link_to": link_to,
				"is_query_report": 1 if link_type == "Report" else 0,
			}
			if link_type == "Report":
				row["report_ref_doctype"] = frappe.db.get_value("Report", link_to, "ref_doctype")
			rows.append(row)
	return rows


def sync_ai_employee_workspace(*, save: bool = True, rebuild: bool = True) -> dict:
	stats = {"sections": 0, "links": 0, "shortcuts": 0}
	if not frappe.db.exists("Workspace", WORKSPACE_NAME):
		ws = frappe.get_doc(
			{
				"doctype": "Workspace",
				"label": WORKSPACE_NAME,
				"title": WORKSPACE_NAME,
				"module": "Omnexa AI Employee",
				"public": 1,
				"icon": WORKSPACE_ICON,
			}
		)
		ws.insert(ignore_permissions=True)

	rows = _build_link_rows()
	link_rows = [r for r in rows if r.get("type") == "Link"]
	new_shortcuts = build_shortcuts_from_link_rows(rows)
	ws = frappe.get_doc("Workspace", WORKSPACE_NAME)
	ws.icon = WORKSPACE_ICON
	if rebuild:
		ws.set("links", [])
		ws.set("shortcuts", [])
	for row in rows:
		if row["type"] == "Card Break":
			stats["sections"] += 1
		else:
			stats["links"] += 1
		ws.append("links", row)
	for sc in new_shortcuts:
		ws.append("shortcuts", sc)
	stats["shortcuts"] = len(new_shortcuts)
	drop_missing_workspace_dashboard_links(ws)
	ws.content = build_content_from_link_rows(
		rows,
		ws,
		title="AI Employee",
		slug="ai-emp",
	)
	stats["content_blocks"] = len(json.loads(ws.content))
	if save:
		ws.flags.ignore_permissions = True
		ws.flags.ignore_version = True
		latest = frappe.db.get_value("Workspace", WORKSPACE_NAME, "modified")
		if latest:
			ws._original_modified = latest
		ws.save()
		frappe.clear_cache(doctype="Workspace")
		try:
			from omnexa_core.omnexa_core.workspace_icon_enricher import enrich_workspace_visual_icons

			enrich_workspace_visual_icons(WORKSPACE_NAME, save=True)
		except Exception:
			pass
	stats["total_links"] = len(link_rows)
	return stats
