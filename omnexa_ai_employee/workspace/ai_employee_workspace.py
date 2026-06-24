# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""AI Employee workspace."""

from __future__ import annotations

import json

import frappe

from omnexa_core.omnexa_core.vertical_workspace_sync import build_link_rows_for_app

WORKSPACE_NAME = "AI Employee"

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


def sync_ai_employee_workspace(*, save: bool = True, rebuild: bool = True) -> dict:
	if not frappe.db.exists("Workspace", WORKSPACE_NAME):
		ws = frappe.get_doc(
			{
				"doctype": "Workspace",
				"label": WORKSPACE_NAME,
				"title": WORKSPACE_NAME,
				"module": "Omnexa AI Employee",
				"public": 1,
				"icon": "cpu",
			}
		)
		ws.insert(ignore_permissions=True)

	rows = build_link_rows_for_app("omnexa_ai_employee", WORKSPACE_SECTIONS)
	ws = frappe.get_doc("Workspace", WORKSPACE_NAME)
	if rebuild:
		ws.set("links", [])
	for row in rows:
		ws.append("links", row)
	content = [{"id": "ai-title", "type": "header", "data": {"text": "<b>AI Employee</b>", "col": 12}}]
	idx = 0
	for row in rows:
		if row.get("type") == "Link":
			content.append({"id": f"ai-lnk-{idx}", "type": "shortcut", "data": {"shortcut_name": row["label"], "col": 4}})
			idx += 1
	ws.content = json.dumps(content)
	if save:
		ws.flags.ignore_permissions = True
		ws.save()
		frappe.clear_cache(doctype="Workspace")
	return {"links": len([r for r in rows if r.get("type") == "Link"])}
