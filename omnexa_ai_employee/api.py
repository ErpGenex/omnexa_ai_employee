# Copyright (c) 2026, Omnexa and contributors
# License: MIT

from __future__ import annotations

import frappe
from frappe import _

from omnexa_ai_employee.engine.audit.ecosystem_audit import run_ecosystem_audit
from omnexa_ai_employee.engine.ocr.service import run_ocr
from omnexa_ai_employee.engine.orchestrator import process_chat
from omnexa_ai_employee.engine.providers import get_provider_client, list_enabled_providers
from omnexa_ai_employee.engine.router import route_request


@frappe.whitelist()
def get_dashboard() -> dict:
	open_conversations = frappe.db.count("AI Conversation", {"status": ["in", ["Open", "Escalated"]]})
	orders_generated = frappe.db.count(
		"AI Conversation",
		{"status": "Closed", "agent_role": ["in", ["Sales", "Tourism", "Finance"]]},
	)
	audit = run_ecosystem_audit()
	return {
		"kpis": {
			"active_conversations": open_conversations,
			"orders_generated": orders_generated,
			"appointments_created": frappe.db.count("AI Conversation", {"agent_role": "Healthcare", "status": "Closed"}),
			"ai_providers": audit["ai_employee"]["providers"],
			"escalation_rate": _escalation_rate(),
		},
		"agents": frappe.get_all(
			"AI Agent",
			filters={"enabled": 1},
			fields=["name", "agent_name", "agent_role", "description"],
			order_by="agent_role asc",
		),
		"providers": list_enabled_providers(),
		"audit_summary": audit,
	}


def _escalation_rate() -> float:
	total = frappe.db.count("AI Conversation")
	if not total:
		return 0.0
	escalated = frappe.db.count("AI Conversation", {"status": "Escalated"})
	return round(escalated * 100.0 / total, 1)


@frappe.whitelist()
def chat(message: str, agent_code: str | None = None, conversation: str | None = None, channel: str = "Desk", customer: str | None = None, company: str | None = None) -> dict:
	frappe.only_for(("System Manager", "AI Employee User"))
	return process_chat(
		message=message,
		agent_code=agent_code,
		conversation=conversation,
		channel=channel,
		customer=customer,
		company=company or frappe.defaults.get_user_default("Company"),
	)


@frappe.whitelist()
def preview_route(message: str, agent_code: str | None = None) -> dict:
	role = frappe.db.get_value("AI Agent", agent_code, "agent_role") if agent_code else None
	return route_request(user_text=message, agent_role=role)


@frappe.whitelist()
def run_audit() -> dict:
	frappe.only_for("System Manager")
	return run_ecosystem_audit()


@frappe.whitelist()
def test_provider(provider: str) -> dict:
	frappe.only_for("System Manager")
	client = get_provider_client(provider)
	return client.health_check()


@frappe.whitelist()
def ocr_document(provider: str | None = None, document_type: str | None = None, file_url: str | None = None) -> dict:
	frappe.only_for(("System Manager", "AI Employee User"))
	return run_ocr(provider=provider, document_type=document_type, file_url=file_url)


@frappe.whitelist()
def process_voice_transcript(transcript: str, agent_code: str | None = None, conversation: str | None = None) -> dict:
	"""Voice → text → intent → ERP action (phase 1: routes transcript to chat)."""
	return chat(message=transcript, agent_code=agent_code, conversation=conversation, channel="Voice")
