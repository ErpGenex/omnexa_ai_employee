# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Activity registry — maps installed Omnexa apps to AI agents and ERP actions."""

from __future__ import annotations

import re

import frappe

AGENT_ROLE_OPTIONS = (
	"Sales\nCustomer Service\nHealthcare\nEducation\nTourism\nFinance\n"
	"Trading\nHR\nManufacturing\nProjects\nOperations\nAccounting\n"
	"Agriculture\nConstruction\nRestaurant\nLegal\nRisk"
)

ACTIVITY_DEFINITIONS: list[dict] = [
	{
		"activity_code": "sales",
		"app": "omnexa_customer_core",
		"title": "Sales & CRM",
		"agent_code": "sales",
		"agent_role": "Sales",
		"keywords": "quotation,quote,عرض سعر,sales order,order,طلب",
	},
	{
		"activity_code": "support",
		"app": "omnexa_services",
		"title": "Customer Service",
		"agent_code": "support",
		"agent_role": "Customer Service",
		"keywords": "ticket,complaint,شكوى,تذكرة,support,escalation",
	},
	{
		"activity_code": "healthcare",
		"app": "omnexa_healthcare",
		"title": "Healthcare",
		"agent_code": "healthcare",
		"agent_role": "Healthcare",
		"keywords": "appointment,موعد,حجز,patient,doctor,clinic",
	},
	{
		"activity_code": "education",
		"app": "omnexa_education",
		"title": "Education",
		"agent_code": "education",
		"agent_role": "Education",
		"keywords": "student,parent,class,enrollment,تسجيل,طالب",
	},
	{
		"activity_code": "tourism",
		"app": "omnexa_tourism",
		"title": "Tourism",
		"agent_code": "tourism",
		"agent_role": "Tourism",
		"keywords": "visa,flight,hotel,package,booking,سفر,فيزا",
	},
	{
		"activity_code": "finance",
		"app": "omnexa_consumer_finance",
		"title": "Finance & Lending",
		"agent_code": "finance",
		"agent_role": "Finance",
		"keywords": "loan,credit,installment,تمويل,قرض,ائتمان",
	},
	{
		"activity_code": "trading",
		"app": "omnexa_trading",
		"title": "Trading & Distribution",
		"agent_code": "trading",
		"agent_role": "Trading",
		"keywords": "van sales,distribution,dispatch,pharma,batch,توزيع,مبيعات",
	},
	{
		"activity_code": "hr",
		"app": "omnexa_hr",
		"title": "Human Resources",
		"agent_code": "hr",
		"agent_role": "HR",
		"keywords": "leave,إجازة,payroll,راتب,attendance,حضور,recruitment",
	},
	{
		"activity_code": "manufacturing",
		"app": "omnexa_manufacturing",
		"title": "Manufacturing",
		"agent_code": "manufacturing",
		"agent_role": "Manufacturing",
		"keywords": "work order,production,bom,تصنيع,أمر تشغيل",
	},
	{
		"activity_code": "projects",
		"app": "omnexa_projects_pm",
		"title": "Projects & PM",
		"agent_code": "projects",
		"agent_role": "Projects",
		"keywords": "project,issue,milestone,wbs,مشروع,مهمة",
	},
	{
		"activity_code": "accounting",
		"app": "omnexa_accounting",
		"title": "Accounting",
		"agent_code": "accounting",
		"agent_role": "Accounting",
		"keywords": "journal,payment,invoice,محاسبة,قيد,دفع",
	},
	{
		"activity_code": "agriculture",
		"app": "omnexa_agriculture",
		"title": "Agriculture",
		"agent_code": "agriculture",
		"agent_role": "Agriculture",
		"keywords": "farm,crop,harvest,زراعة,محصول",
	},
	{
		"activity_code": "construction",
		"app": "omnexa_construction",
		"title": "Construction",
		"agent_code": "construction",
		"agent_role": "Construction",
		"keywords": "construction,site,boq,مقاولات,موقع",
	},
	{
		"activity_code": "restaurant",
		"app": "omnexa_restaurant",
		"title": "Restaurant & F&B",
		"agent_code": "restaurant",
		"agent_role": "Restaurant",
		"keywords": "restaurant,menu,table,kitchen,مطعم,طلب طعام",
	},
	{
		"activity_code": "operations",
		"app": "omnexa_core",
		"title": "Core Operations",
		"agent_code": "operations",
		"agent_role": "Operations",
		"keywords": "branch,company,workflow,عمليات",
	},
]

ACTION_DEFINITIONS: list[dict] = [
	{
		"action": "sales_quotation",
		"pattern": r"\b(quotation|quote|عرض\s*سعر)\b",
		"roles": {"Sales", "Tourism", "Finance", "Trading"},
		"doctype": "Sales Quotation"
	},
	{
		"action": "support_ticket",
		"pattern": r"\b(ticket|complaint|شكوى|تذكرة)\b",
		"roles": {"Customer Service", "Sales", "Operations"},
		"doctypes": ["CRM Case Ticket", "Service Ticket"]},
	{
		"action": "healthcare_appointment",
		"pattern": r"\b(appointment|موعد|حجز)\b",
		"roles": {"Healthcare"
	},
		"doctype": "Healthcare Appointment"
	},
	{
		"action": "trading_van_sales",
		"pattern": r"\b(van\s*sales|mobile\s*sales|فاتورة\s*مندوب)\b",
		"roles": {"Trading", "Sales"},
		"doctype": "Trading Van Sales Invoice"
	},
	{
		"action": "trading_distribution",
		"pattern": r"\b(distribution\s*order|delivery\s*order|أمر\s*توزيع)\b",
		"roles": {"Trading", "Sales", "Operations"},
		"doctype": "Trading Distribution Order"
	},
	{
		"action": "hr_leave",
		"pattern": r"\b(leave\s*application|إجازة|طلب\s*إجازة)\b",
		"roles": {"HR"
	},
		"doctype": "HR Leave Application"
	},
	{
		"action": "hr_expense",
		"pattern": r"\b(expense\s*claim|مصروف|مطالبة\s*مصروف)\b",
		"roles": {"HR", "Finance", "Accounting"},
		"doctype": "HR Expense Claim"
	},
	{
		"action": "work_order",
		"pattern": r"\b(work\s*order|production\s*order|أمر\s*تشغيل)\b",
		"roles": {"Manufacturing", "Operations"},
		"doctype": "Work Order"
	},
	{
		"action": "pm_issue",
		"pattern": r"\b(project\s*issue|pm\s*issue|مشكلة\s*مشروع)\b",
		"roles": {"Projects", "Operations"},
		"doctype": "PM Issue Log"
	},
	{
		"action": "restaurant_order",
		"pattern": r"\b(restaurant\s*order|table\s*order|طلب\s*مطعم)\b",
		"roles": {"Restaurant", "Tourism"},
		"doctype": "Restaurant Order"
	},
	{
		"action": "loan_application",
		"pattern": r"\b(loan\s*application|طلب\s*قرض|تمويل)\b",
		"roles": {"Finance"
	},
		"doctype": "Consumer Loan Application"
	},
	{
		"action": "service_contract",
		"pattern": r"\b(service\s*contract|عقد\s*خدمة)\b",
		"roles": {"Customer Service", "Operations"},
		"doctype": "Service Contract"
	},
]

EXTENDED_AGENTS: list[dict] = [
	{
		"agent_code": "trading",
		"agent_name": "Trading Employee",
		"agent_role": "Trading",
		"description": "Van sales, distribution, pharma batches, warehouse dispatch.",
		"system_prompt": "You are a trading and distribution assistant for van sales, pharma compliance, and logistics.",
	},
	{
		"agent_code": "hr",
		"agent_name": "HR Employee",
		"agent_role": "HR",
		"description": "Leave, payroll, attendance, recruitment.",
		"system_prompt": "You are an HR assistant for leave requests, payroll questions, and employee services.",
	},
	{
		"agent_code": "manufacturing",
		"agent_name": "Manufacturing Employee",
		"agent_role": "Manufacturing",
		"description": "Work orders, BOM, production quality.",
		"system_prompt": "You are a manufacturing assistant for work orders, production planning, and quality checks.",
	},
	{
		"agent_code": "projects",
		"agent_name": "Projects Employee",
		"agent_role": "Projects",
		"description": "Project issues, milestones, WBS tasks.",
		"system_prompt": "You are a project management assistant for issues, milestones, and resource planning.",
	},
	{
		"agent_code": "accounting",
		"agent_name": "Accounting Employee",
		"agent_role": "Accounting",
		"description": "Payments, journals, GL inquiries.",
		"system_prompt": "You are an accounting assistant for payments, journals, and financial inquiries.",
	},
	{
		"agent_code": "agriculture",
		"agent_name": "Agriculture Employee",
		"agent_role": "Agriculture",
		"description": "Farm operations, crops, harvest planning.",
		"system_prompt": "You are an agriculture operations assistant."
	},
	{
		"agent_code": "construction",
		"agent_name": "Construction Employee",
		"agent_role": "Construction",
		"description": "Site operations, BOQ, subcontractor coordination.",
		"system_prompt": "You are a construction project assistant."
	},
	{
		"agent_code": "restaurant",
		"agent_name": "Restaurant Employee",
		"agent_role": "Restaurant",
		"description": "Orders, tables, kitchen tickets.",
		"system_prompt": "You are a restaurant operations assistant for orders and kitchen coordination."
	},
	{
		"agent_code": "operations",
		"agent_name": "Operations Employee",
		"agent_role": "Operations",
		"description": "Cross-module workflows and escalations.",
		"system_prompt": "You are an operations coordinator across ERPGENEX modules."
	},
]


def _installed_apps() -> set[str]:
	return set(frappe.get_installed_apps() or [])


def _doctype_available(spec: dict) -> bool:
	if spec.get("doctype"):
		return bool(frappe.db.exists("DocType", spec["doctype"]))
	for name in spec.get("doctypes") or []:
		if frappe.db.exists("DocType", name):
			return True
	return not spec.get("doctype") and not spec.get("doctypes")


def get_installed_activities() -> list[dict]:
	installed = _installed_apps()
	rows = []
	for row in ACTIVITY_DEFINITIONS:
		if row["app"] not in installed and row["app"] != "omnexa_core":
			continue
		rows.append(
			{
				**row,
				"installed": True,
				"agent_exists": bool(frappe.db.exists("AI Agent", row["agent_code"]))}
		)
	return rows


def get_activity_context_prompt() -> str:
	activities = get_installed_activities()
	if not activities:
		return "No vertical Omnexa apps detected."
	titles = ", ".join(a["title"] for a in activities)
	return (
		f"You operate inside ERPGENEX. Active business areas: {titles}. "
		"Create draft ERP documents when the user clearly requests an action."
	)


def resolve_agent_for_message(message: str, current_agent_code: str | None = None) -> str | None:
	if current_agent_code and frappe.db.exists("AI Agent", current_agent_code):
		return current_agent_code

	text = (message or "").lower()
	best_code = None
	best_score = 0
	for activity in get_installed_activities():
		keywords = [k.strip().lower() for k in (activity.get("keywords") or "").split(",") if k.strip()]
		score = sum(1 for keyword in keywords if keyword in text)
		if score > best_score:
			best_score = score
			best_code = activity["agent_code"]

	if best_code and frappe.db.exists("AI Agent", best_code):
		return best_code

	fallback = frappe.db.get_value("AI Agent", {"enabled": 1
	}, "name", order_by="modified desc")
	return fallback


def _agent_role(agent_code: str | None) -> str | None:
	if not agent_code:
		return None
	return frappe.db.get_value("AI Agent", agent_code, "agent_role")


def resolve_action(user_text: str, agent_code: str | None) -> str | None:
	role = _agent_role(agent_code)
	text = user_text or ""
	for spec in ACTION_DEFINITIONS:
		if not _doctype_available(spec):
			continue
		if not re.search(spec["pattern"], text, re.I):
			continue
		allowed = spec.get("roles") or set()
		if role and role not in allowed and role != "Operations":
			continue
		return spec["action"]
	return None


def list_action_capabilities() -> list[dict]:
	rows = []
	for spec in ACTION_DEFINITIONS:
		rows.append(
			{
				"action": spec["action"],
				"available": _doctype_available(spec),
				"roles": sorted(spec.get("roles") or []),
				"doctype": spec.get("doctype") or (spec.get("doctypes") or [None])[0]
	}
		)
	return rows


def sync_activity_agents() -> dict:
	"""Create agents for installed vertical apps (idempotent)."""
	stats = {"created": 0, "skipped": 0
	}
	installed = _installed_apps()
	for row in EXTENDED_AGENTS:
		activity = next((a for a in ACTIVITY_DEFINITIONS if a["agent_code"] == row["agent_code"]), None)
		if activity and activity["app"] not in installed and activity["app"] != "omnexa_core":
			stats["skipped"] += 1
			continue
		if frappe.db.exists("AI Agent", row["agent_code"]):
			stats["skipped"] += 1
			continue
		doc = frappe.get_doc({"doctype": "AI Agent", "enabled": 1, **row})
		doc.insert(ignore_permissions=True)
		stats["created"] += 1
	frappe.db.commit()
	return stats
