# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""ERP action execution triggered from AI conversations."""

from __future__ import annotations

import frappe
from frappe.utils import add_days, flt, now_datetime, today

from omnexa_ai_employee.engine.activities.registry import resolve_action

_ACTION_HANDLERS: dict[str, callable] = {}


def _register(action: str):
	def decorator(func):
		_ACTION_HANDLERS[action] = func
		return func

	return decorator


def maybe_execute_erp_action(
	*,
	user_text: str,
	agent_code: str | None,
	customer: str | None,
	conversation: str | None,
) -> str | None:
	action = resolve_action(user_text, agent_code)
	if not action:
		return None
	handler = _ACTION_HANDLERS.get(action)
	if not handler:
		return None
	try:
		return handler(customer=customer, note=user_text)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "AI Employee ERP action")
		return frappe._("Could not complete ERP action for {0}").format(action)


@_register("sales_quotation")
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
			"valid_till": add_days(today(), 30)}
	)
	doc.append("items", {"item_code": _default_item(), "qty": 1, "rate": 0
	})
	doc.insert(ignore_permissions=True)
	return frappe._("Created draft Sales Quotation {0}").format(doc.name)


@_register("support_ticket")
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
				"details": note
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
			"status": "Open"
	}
		if profile:
			payload["customer_profile"] = profile
		doc = frappe.get_doc(payload)
		doc.insert(ignore_permissions=True)
		return frappe._("Created Service Ticket {0}").format(doc.name)

	return frappe._("No support ticket DocType available or missing Customer Profile.")


@_register("healthcare_appointment")
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
			"notes": note
	}
	)
	doc.insert(ignore_permissions=True)
	return frappe._("Created Healthcare Appointment {0}").format(doc.name)


@_register("trading_van_sales")
def _create_trading_van_sales(*, customer: str | None, note: str) -> str:
	if not frappe.db.exists("DocType", "Trading Van Sales Invoice"):
		return frappe._("Trading Van Sales Invoice DocType not available.")
	company, branch = _default_company_branch()
	if not company or not branch:
		return frappe._("Company and Branch are required for van sales.")
	profile = _resolve_customer_profile(customer, company)
	sales_rep = frappe.db.get_value("Trading Sales Representative", {"company": company, "branch": branch
	}, "name")
	if not profile or not sales_rep:
		return frappe._("Customer Profile and Sales Representative are required for van sales.")
	doc = frappe.get_doc(
		{
			"doctype": "Trading Van Sales Invoice",
			"company": company,
			"branch": branch,
			"customer_profile": profile,
			"sales_representative": sales_rep,
			"posting_date": today(),
			"payment_type": "Cash",
			"items": [{"item": _default_item(), "qty": 1, "rate": 0}]
	}
	)
	doc.insert(ignore_permissions=True)
	return frappe._("Created draft Trading Van Sales Invoice {0}").format(doc.name)


@_register("trading_distribution")
def _create_trading_distribution(*, customer: str | None, note: str) -> str:
	if not frappe.db.exists("DocType", "Trading Distribution Order"):
		return frappe._("Trading Distribution Order DocType not available.")
	company, branch = _default_company_branch()
	profile = _resolve_customer_profile(customer, company)
	route_plan = frappe.db.get_value("Trading Route Plan", {"company": company
	}, "name")
	sales_rep = frappe.db.get_value("Trading Sales Representative", {"company": company, "branch": branch
	}, "name")
	if not all([company, branch, route_plan, sales_rep, profile]):
		return frappe._("Route Plan, Sales Representative, and Customer Profile are required for distribution orders.")
	doc = frappe.get_doc(
		{
			"doctype": "Trading Distribution Order",
			"company": company,
			"branch": branch,
			"route_plan": route_plan,
			"sales_representative": sales_rep,
			"customer_profile": profile,
			"planned_delivery_date": today(),
			"status": "Draft",
			"items": [{"item": _default_item(), "qty": 1, "rate": 0}]
	}
	)
	doc.insert(ignore_permissions=True)
	return frappe._("Created draft Trading Distribution Order {0}").format(doc.name)


@_register("hr_leave")
def _create_hr_leave(*, customer: str | None, note: str) -> str:
	if not frappe.db.exists("DocType", "HR Leave Application"):
		return frappe._("HR Leave Application DocType not available.")
	company, branch = _default_company_branch()
	employee = _default_employee(company)
	leave_type = frappe.db.get_value("HR Leave Type", {}, "name") or "Annual Leave"
	if not employee:
		return frappe._("No Employee found for leave application.")
	doc = frappe.get_doc(
		{
			"doctype": "HR Leave Application",
			"employee": employee,
			"company": company,
			"branch": branch,
			"leave_type": leave_type,
			"from_date": today(),
			"to_date": add_days(today(), 1),
			"reason": (note or "")[:500],
			"status": "Draft"
	}
	)
	doc.insert(ignore_permissions=True)
	return frappe._("Created draft HR Leave Application {0}").format(doc.name)


@_register("hr_expense")
def _create_hr_expense(*, customer: str | None, note: str) -> str:
	if not frappe.db.exists("DocType", "HR Expense Claim"):
		return frappe._("HR Expense Claim DocType not available.")
	company, branch = _default_company_branch()
	employee = _default_employee(company)
	if not employee:
		return frappe._("No Employee found for expense claim.")
	doc = frappe.get_doc(
		{
			"doctype": "HR Expense Claim",
			"employee": employee,
			"company": company,
			"branch": branch,
			"posting_date": today(),
			"description": (note or "AI expense claim")[:500],
			"status": "Draft"
	}
	)
	doc.insert(ignore_permissions=True)
	return frappe._("Created draft HR Expense Claim {0}").format(doc.name)


@_register("work_order")
def _create_work_order(*, customer: str | None, note: str) -> str:
	if not frappe.db.exists("DocType", "Work Order"):
		return frappe._("Work Order DocType not available.")
	company, branch = _default_company_branch()
	item = _default_item()
	doc = frappe.get_doc(
		{
			"doctype": "Work Order",
			"company": company,
			"branch": branch,
			"item": item,
			"qty_to_produce": 1,
			"planned_start_date": today(),
			"status": "Draft"
	}
	)
	doc.insert(ignore_permissions=True)
	return frappe._("Created draft Work Order {0}").format(doc.name)


@_register("pm_issue")
def _create_pm_issue(*, customer: str | None, note: str) -> str:
	if not frappe.db.exists("DocType", "PM Issue Log"):
		return frappe._("PM Issue Log DocType not available.")
	company, branch = _default_company_branch()
	project = frappe.db.get_value("Project Contract", {"company": company
	}, "name") if company else None
	if not project:
		project = frappe.db.get_value("Project Contract", {}, "name")
	if not project:
		return frappe._("No Project Contract found for PM Issue Log.")
	doc = frappe.get_doc(
		{
			"doctype": "PM Issue Log",
			"project": project,
			"company": company,
			"branch": branch,
			"issue_title": (note or "AI project issue")[:140],
			"description": note,
			"severity": "Medium",
			"status": "Open"
	}
	)
	doc.insert(ignore_permissions=True)
	return frappe._("Created PM Issue Log {0}").format(doc.name)


@_register("restaurant_order")
def _create_restaurant_order(*, customer: str | None, note: str) -> str:
	if not frappe.db.exists("DocType", "Restaurant Order"):
		return frappe._("Restaurant Order DocType not available.")
	company, branch = _default_company_branch()
	profile = _resolve_customer_profile(customer, company)
	doc = frappe.get_doc(
		{
			"doctype": "Restaurant Order",
			"order_type": "Dine-in",
			"company": company,
			"branch": branch,
			"customer_profile": profile,
			"customer": customer if customer and frappe.db.exists("Customer", customer) else None,
			"status": "Open"
	}
	)
	doc.insert(ignore_permissions=True)
	return frappe._("Created Restaurant Order {0}").format(doc.name)


@_register("loan_application")
def _create_loan_application(*, customer: str | None, note: str) -> str:
	if not frappe.db.exists("DocType", "Consumer Loan Application"):
		return frappe._("Consumer Loan Application DocType not available.")
	customer_name = customer
	if customer and frappe.db.exists("Customer", customer):
		customer_name = frappe.db.get_value("Customer", customer, "customer_name") or customer
	doc = frappe.get_doc(
		{
			"doctype": "Consumer Loan Application",
			"customer_name": customer_name or "AI Applicant",
			"principal": flt(1000),
			"term_months": 12,
			"application_channel": "MOBILE",
			"application_status": "SUBMITTED"
	}
	)
	doc.insert(ignore_permissions=True)
	return frappe._("Created Consumer Loan Application {0}").format(doc.name)


@_register("service_contract")
def _create_service_contract(*, customer: str | None, note: str) -> str:
	if not frappe.db.exists("DocType", "Service Contract"):
		return frappe._("Service Contract DocType not available.")
	company, branch = _default_company_branch()
	profile = _resolve_customer_profile(customer, company)
	doc = frappe.get_doc(
		{
			"doctype": "Service Contract",
			"company": company,
			"branch": branch,
			"customer_profile": profile,
			"start_date": today(),
			"status": "Draft"
	}
	)
	doc.insert(ignore_permissions=True)
	return frappe._("Created draft Service Contract {0}").format(doc.name)


def _default_item() -> str:
	item = frappe.db.get_value("Item", {"disabled": 0, "is_sales_item": 1
	}, "name")
	if item:
		return item
	item = frappe.db.get_value("Item", {"disabled": 0
	}, "name")
	if item:
		return item
	frappe.throw(frappe._("No Item found for document line."))


def _default_company_branch() -> tuple[str | None, str | None]:
	company = (frappe.defaults.get_user_default("Company") or "").strip()
	branch = (frappe.defaults.get_user_default("Branch") or "").strip()
	if not company:
		company = (frappe.db.get_single_value("Global Defaults", "default_company") or "").strip()
	if not branch and company:
		branch = frappe.db.get_value("Branch", {"company": company
	}, "name")
	return company or None, branch or None


def _default_employee(company: str | None) -> str | None:
	filters = {"company": company} if company else {
	}
	return frappe.db.get_value("Employee", filters, "name", order_by="creation desc")


def _resolve_customer_profile(customer: str | None, company: str | None) -> str | None:
	if not frappe.db.exists("DocType", "Customer Profile"):
		return None
	if customer and frappe.db.exists("Customer Profile", customer):
		return customer
	if customer and frappe.db.exists("Customer", customer):
		profile = frappe.db.get_value("Customer Profile", {"linked_customer": customer
	}, "name")
		if profile:
			return profile
	filters = {"company": company} if company else {
	}
	profile = frappe.db.get_value("Customer Profile", filters, "name")
	if profile:
		return profile
	return frappe.db.get_value("Customer Profile", {}, "name")
