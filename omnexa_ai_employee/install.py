# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Bootstrap AI Employee defaults."""

from __future__ import annotations

import frappe

DEFAULT_AGENTS = [
	{
		"agent_code": "sales",
		"agent_name": "Sales Employee",
		"agent_role": "Sales",
		"description": "Product recommendations, quotations, orders, upselling.",
		"system_prompt": "You are an ERPGENEX sales employee. Help customers choose products, create quotations, and follow up on orders.",
	},
	{
		"agent_code": "support",
		"agent_name": "Customer Service Employee",
		"agent_role": "Customer Service",
		"description": "Tickets, complaints, follow-up, escalation.",
		"system_prompt": "You are a customer service agent. Create tickets, resolve complaints, and escalate when needed.",
	},
	{
		"agent_code": "healthcare",
		"agent_name": "Healthcare Employee",
		"agent_role": "Healthcare",
		"description": "Symptoms, doctor matching, appointments.",
		"system_prompt": "You are a healthcare assistant. Collect symptoms, suggest doctors, and book appointments.",
	},
	{
		"agent_code": "education",
		"agent_name": "Education Employee",
		"agent_role": "Education",
		"description": "Parent support, student inquiries, scheduling.",
		"system_prompt": "You are an education portal assistant for parents, students, and teachers.",
	},
	{
		"agent_code": "tourism",
		"agent_name": "Tourism Employee",
		"agent_role": "Tourism",
		"description": "Visa, flights, hotels, packages.",
		"system_prompt": "You are a tourism consultant for visas, flights, hotels, and travel packages.",
	},
	{
		"agent_code": "finance",
		"agent_name": "Finance Employee",
		"agent_role": "Finance",
		"description": "Loans, credit scoring, document collection.",
		"system_prompt": "You are a finance assistant for loan applications, credit checks, and installment simulation.",
	},
]


def bootstrap_defaults() -> dict:
	stats = {"settings": 0, "agents": 0, "routing_rules": 0
	}
	if not frappe.db.exists("AI Employee Settings", "AI Employee Settings"):
		doc = frappe.new_doc("AI Employee Settings")
		doc.enabled = 1
		doc.default_routing_strategy = "Hybrid"
		doc.audit_on_startup = 1
		doc.save(ignore_permissions=True)
		stats["settings"] = 1

	for row in DEFAULT_AGENTS:
		if frappe.db.exists("AI Agent", row["agent_code"]):
			continue
		doc = frappe.get_doc({"doctype": "AI Agent", "enabled": 1, **row})
		doc.insert(ignore_permissions=True)
		stats["agents"] += 1

	rules = [
		("simple_lookup", "Simple ERP Lookup", "Local", 10, "product lookup,stock balance,customer balance"),
		("document_summary", "Document Summary", "Local", 20, "summarize,short answer"),
		("legal_analysis", "Legal Analysis", "Cloud", 30, "legal,contract,compliance"),
		("large_context", "Large Context", "Cloud", 40, "full report,all transactions"),
	]
	for code, title, route, priority, keywords in rules:
		if frappe.db.exists("AI Routing Rule", code):
			continue
		frappe.get_doc(
			{
				"doctype": "AI Routing Rule",
				"rule_code": code,
				"title": title,
				"route_target": route,
				"priority": priority,
				"match_keywords": keywords,
				"enabled": 1
	}
		).insert(ignore_permissions=True)
		stats["routing_rules"] += 1

	frappe.db.commit()
	return stats


def bootstrap_ollama() -> dict:
	from omnexa_ai_employee.engine.providers.ollama_setup import bootstrap_ollama_provider

	return bootstrap_ollama_provider(save=True)


def bootstrap_whatsapp_channel() -> dict:
	"""Ensure a template WhatsApp channel account exists (configure tokens in Desk)."""
	if frappe.db.exists("AI Channel Account", "whatsapp-main"):
		doc = frappe.get_doc("AI Channel Account", "whatsapp-main")
		if not doc.default_agent:
			doc.default_agent = frappe.db.get_value("AI Agent", {"enabled": 1, "agent_code": "support"
	}, "name") or frappe.db.get_value("AI Agent", {"enabled": 1
	}, "name")
			doc.save(ignore_permissions=True)
		return {"created": False, "name": doc.name, "webhook_url": doc.webhook_url
	}

	agent = frappe.db.get_value("AI Agent", {"enabled": 1, "agent_code": "support"
	}, "name") or frappe.db.get_value("AI Agent", {"enabled": 1
	}, "name")
	doc = frappe.get_doc(
		{
			"doctype": "AI Channel Account",
			"account_name": "whatsapp-main",
			"channel_type": "WhatsApp",
			"enabled": 1,
			"default_agent": agent,
			"verify_token": frappe.generate_hash(length=24),
			"api_version": "v21.0"
	}
	)
	doc.insert(ignore_permissions=True)
	return {"created": True, "name": doc.name, "webhook_url": doc.webhook_url, "verify_token": doc.verify_token
	}


def sync_agents_from_install() -> dict:
	try:
		from omnexa_ai_employee.engine.activities.registry import sync_activity_agents

		return sync_activity_agents()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "AI Employee: sync activity agents")
		return {"created": 0, "skipped": 0
	}


def after_install():
	try:
		bootstrap_defaults()
		sync_agents_from_install()
		bootstrap_ollama()
		bootstrap_whatsapp_channel()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "AI Employee: after_install")


def after_migrate():
	try:
		from omnexa_ai_employee.engine.providers.ollama_setup import bootstrap_ollama_provider

		bootstrap_ollama_provider(save=True)
		bootstrap_whatsapp_channel()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "AI Employee: ollama bootstrap")
	try:
		sync_agents_from_install()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "AI Employee: sync activity agents")
	try:
		from omnexa_ai_employee.workspace.ai_employee_workspace import sync_ai_employee_workspace

		sync_ai_employee_workspace(save=True, rebuild=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "AI Employee: workspace sync")
