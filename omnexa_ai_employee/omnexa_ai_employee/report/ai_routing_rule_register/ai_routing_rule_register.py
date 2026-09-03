# Copyright (c) 2026, ErpGenEx
# Auto-generated Global Excellence report pack

import frappe
from frappe import _


def execute(filters=None):
	data = frappe.db.sql(
		"""
		SELECT `name`, `title`, `route_target`
		FROM `tabAI Routing Rule`
		ORDER BY modified DESC
		LIMIT 500
		""",
		as_dict=True,
	)
	columns = [
		{"label": _("Name"), "fieldname": "name", "fieldtype": "Link", "width": 140},
		{"label": _("Title"), "fieldname": "title", "fieldtype": "Data", "width": 120},
		{"label": _("Route Target"), "fieldname": "route_target", "fieldtype": "Select", "width": 120}
	]
	return columns, data
