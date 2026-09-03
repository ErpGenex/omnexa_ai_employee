# Copyright (c) 2026, ErpGenEx
# Auto-generated Global Excellence report pack

import frappe
from frappe import _


def execute(filters=None):
	data = frappe.db.sql(
		"""
		SELECT `name`, `agent`, `agent_role`, `channel`, `status`
		FROM `tabAI Conversation`
		ORDER BY modified DESC
		LIMIT 500
		""",
		as_dict=True,
	)
	columns = [
		{"label": _("Name"), "fieldname": "name", "fieldtype": "Link", "width": 140},
		{"label": _("Agent"), "fieldname": "agent", "fieldtype": "Link", "width": 120},
		{"label": _("Agent Role"), "fieldname": "agent_role", "fieldtype": "Data", "width": 120},
		{"label": _("Channel"), "fieldname": "channel", "fieldtype": "Select", "width": 120},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Select", "width": 120}
	]
	return columns, data
