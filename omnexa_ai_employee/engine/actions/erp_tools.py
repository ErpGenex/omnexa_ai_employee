# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""ERP action execution triggered from AI conversations."""

from __future__ import annotations

import re

import frappe
from frappe.utils import now_datetime, today

_ACTION_PATTERNS: list[tuple[re.Pattern, str]] = [
	(re.compile(r"\b(quotation|quote|عرض\s*سعر)\b", re.I), "sales_quotation"),
	(re.compile(r"\b(ticket|complaint|شكوى|تذكرة)\b", re.I), "support_ticket"),
	(re.compile(r"\b(appointment|موعد|حجز)\b", re.I), "healthcare_appointment"),
]


def maybe_execute_erp_action(
	*,
	user_text: str,
	agent_code: str | None,
	customer: str | None,
	conversation: str | None,
) -> str | None:
	action = _detect_action(user_text, agent_code)
	if not action:
		return None
	try:
		if action == "sales_quotation":
			return _create_sales_quotation(customer=customer, note=user_text)
		if action == "support_ticket":
			return _create_service_ticket(customer=customer, note=user_text)
		if action == "healthcare_appointment":
			return _create_healthcare_appointment(customer=customer, note=user_text)
	except Exception as exc:
		frappe.log_error(frappe.get_traceback(), "AI Employee ERP action")
		return frappe._("Could not complete ERP action: {0}").format(str(exc))
	return None


def _detect_action(text: str, agent_code: str | None) -> str | None:
	role = frappe.db.get_value("AI Agent", agent_code, "agent_role") if agent_code else None
	for pattern, action in _ACTION_PATTERNS:
		if not pattern.search(text or ""):
			continue
		if action == "sales_quotation" and role not in (None, "Sales", "Tourism", "Finance"):
			continue
		if action == "support_ticket" and role not in (None, "Customer Service", "Sales"):
			continue
		if action == "healthcare_appointment" and role not in (None, "Healthcare"):
			continue
		return action
	return None


def _create_sales_quotation(*, customer: str | None, note: str) -> str:
	if not frappe.db.exists("DocType", "Sales Quotation"):
		return frappe._("Sales Quotation DocType not available.")
	company, branch = _default_company_branch()
	doc = frappe.get_doc(
		{
			"doctype": "Sales Quotation",
			"company": company,
			"customer": customer,
			"transaction_date": today(),
			"valid_till": today(),
		}
	)
	doc.append("items", {"item_code": _default_item(), "qty": 1, "rate": 0})
	doc.insert(ignore_permissions=True)
	return frappe._("Created draft Sales Quotation {0}").format(doc.name)


def _create_service_ticket(*, customer: str | None, note: str) -> str:
	company, branch = _default_company_branch()
	profile = _resolve_customer_profile(customer, company)
	subject = (note or "AI support request")[:140]

	if frappe.db.exists("DocType", "CRM Case Ticket") and profile:
		doc = frappe.get_doc(
			{
				"doctype": "CRM Case Ticket",
				"title": subject,
				"company": company,
				"branch": branch,
				"customer_profile": profile,
				"status": "Open",
				"creation_date": today(),
				"details": note,
			}
		)
		doc.insert(ignore_permissions=True)
		return frappe._("Created CRM Case Ticket {0}").format(doc.name)

	if frappe.db.exists("DocType", "Service Ticket"):
		payload = {
			"doctype": "Service Ticket",
			"subject": subject,
			"company": company,
			"branch": branch,
			"channel": "WhatsApp",
			"status": "Open",
		}
		if profile:
			payload["customer_profile"] = profile
		doc = frappe.get_doc(payload)
		doc.insert(ignore_permissions=True)
		return frappe._("Created Service Ticket {0}").format(doc.name)

	return frappe._("No support ticket DocType available or missing Customer Profile.")


def _create_healthcare_appointment(*, customer: str | None, note: str) -> str:
	if not frappe.db.exists("DocType", "Healthcare Appointment"):
		return frappe._("Healthcare Appointment DocType not available.")
	doc = frappe.get_doc(
		{
			"doctype": "Healthcare Appointment",
			"patient": customer,
			"appointment_date": today(),
			"appointment_time": now_datetime().strftime("%H:%M:%S"),
			"status": "Scheduled",
			"notes": note,
		}
	)
	doc.insert(ignore_permissions=True)
	return frappe._("Created Healthcare Appointment {0}").format(doc.name)


def _default_item() -> str:
	item = frappe.db.get_value("Item", {"disabled": 0, "is_sales_item": 1}, "name")
	if item:
		return item
	item = frappe.db.get_value("Item", {"disabled": 0}, "name")
	if item:
		return item
	frappe.throw(frappe._("No Item found for quotation line."))


def _default_company_branch() -> tuple[str | None, str | None]:
	company = (frappe.defaults.get_user_default("Company") or "").strip()
	branch = (frappe.defaults.get_user_default("Branch") or "").strip()
	if not company:
		company = (frappe.db.get_single_value("Global Defaults", "default_company") or "").strip()
	if not branch:
		branch = frappe.db.get_value("Branch", {"company": company}, "name") if company else None
	return company or None, branch or None


def _resolve_customer_profile(customer: str | None, company: str | None) -> str | None:
	if not frappe.db.exists("DocType", "Customer Profile"):
		return None
	if customer and frappe.db.exists("Customer Profile", customer):
		return customer
	filters = {"company": company} if company else {}
	profile = frappe.db.get_value("Customer Profile", filters, "name")
	if profile:
		return profile
	return frappe.db.get_value("Customer Profile", {}, "name")
