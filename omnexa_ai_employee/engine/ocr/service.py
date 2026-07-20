# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Configurable OCR service (provider plugins)."""

from __future__ import annotations

import frappe


def run_ocr(*, provider: str | None = None, document_type: str | None = None, file_url: str | None = None) -> dict:
	"""Dispatch OCR to configured provider. Returns structured extraction stub until engine wired."""
	if not file_url:
		frappe.throw(frappe._("file_url is required"))

	name = provider or frappe.db.get_value("AI OCR Provider", {"enabled": 1, "is_default": 1
	}, "name")
	if not name:
		name = frappe.db.get_value("AI OCR Provider", {"enabled": 1
	}, "name")
	if not name:
		frappe.throw(frappe._("No OCR provider configured. Create AI OCR Provider."))

	doc = frappe.get_doc("AI OCR Provider", name)
	return {
		"ok": True,
		"provider": doc.name,
		"engine": doc.engine,
		"document_type": document_type or "General",
		"file_url": file_url,
		"extracted_text": "",
		"structured_fields": {
	},
		"message": frappe._("OCR provider {0} registered. Wire engine SDK in deployment.").format(doc.engine)
	}
