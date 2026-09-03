# Copyright (c) 2026, ErpGenEx
# Auto-generated Global Excellence report pack

import frappe
from frappe import _


def execute(filters=None):
	data = frappe.db.sql(
		"""
		SELECT `name`, `agent_name`, `agent_role`
		FROM `tabAI Agent`
		ORDER BY modified DESC
		LIMIT 500
		""",
		as_dict=True,
	)
	columns = [
		{"label": _("Name"), "fieldname": "name", "fieldtype": "Link", "width": 140},
		{"label": _("Agent Name"), "fieldname": "agent_name", "fieldtype": "Data", "width": 120},
		{"label": _("Agent Role"), "fieldname": "agent_role", "fieldtype": "Select", "width": 120}
	]
	return columns, data
