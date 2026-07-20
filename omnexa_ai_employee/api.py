# Copyright (c) 2026, Omnexa and contributors
# License: MIT

from __future__ import annotations

import frappe
from frappe import _

from omnexa_ai_employee.engine.activities.registry import (
	get_installed_activities,
	list_action_capabilities,
	sync_activity_agents,
)
from omnexa_ai_employee.engine.audit.ecosystem_audit import run_ecosystem_audit
from omnexa_ai_employee.engine.ocr.service import run_ocr
from omnexa_ai_employee.engine.orchestrator import process_chat
from omnexa_ai_employee.engine.providers import get_provider_client, list_enabled_providers
from omnexa_ai_employee.engine.providers.ollama_setup import bootstrap_ollama_provider, pick_default_model, probe_ollama
from omnexa_ai_employee.engine.router import route_request


def _verify_webhook_token(account_name: str | None = None) -> bool:
	header_token = (
		frappe.get_request_header("X-Omnexa-Webhook-Token")
		or frappe.get_request_header("X-Verify-Token")
		or ""
	).strip()
	if not header_token:
		return False
	account = account_name
	if not account:
		row = frappe.get_all(
			"AI Channel Account",
			filters={"enabled": 1, "channel_type": "WhatsApp"},
			fields=["name"],
			limit=1,
		)
		account = row[0].name if row else None
	if not account:
		return False
	doc = frappe.get_doc("AI Channel Account", account, ignore_permissions=True)
	return header_token == (doc.verify_token or "").strip()


def _provider_health() -> list[dict]:
	health = []
	for row in list_enabled_providers():
		try:
			status = get_provider_client(row["name"]).health_check()
		except Exception as exc:
			status = {"ok": False, "message": str(exc)}
		health.append({**row, "health": status})
	return health


@frappe.whitelist()
def get_dashboard() -> dict:
	open_conversations = frappe.db.count("AI Conversation", {"status": ["in", ["Open", "Escalated"]]})
	orders_generated = frappe.db.count(
		"AI Conversation",
		{"status": "Closed", "agent_role": ["in", ["Sales", "Tourism", "Finance"]]},
	)
	audit = run_ecosystem_audit()
	ollama = probe_ollama()
	provider_health = _provider_health()
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
		"provider_health": provider_health,
		"activities": get_installed_activities(),
		"erp_actions": list_action_capabilities(),
		"ollama": ollama,
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
def list_activities() -> dict:
	frappe.only_for(("System Manager", "AI Employee User"))
	return {
		"activities": get_installed_activities(),
		"erp_actions": list_action_capabilities(),
	}


@frappe.whitelist()
def sync_agents() -> dict:
	frappe.only_for("System Manager")
	return sync_activity_agents()


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
def get_ollama_status() -> dict:
	frappe.only_for(("System Manager", "AI Employee User"))
	return probe_ollama()


@frappe.whitelist()
def bootstrap_ollama() -> dict:
	frappe.only_for("System Manager")
	return bootstrap_ollama_provider(save=True)


@frappe.whitelist()
def discover_provider_models(base_url: str, provider_type: str = "Ollama") -> dict:
	frappe.only_for("System Manager")
	ptype = (provider_type or "Ollama").strip()
	if ptype == "Ollama":
		result = probe_ollama(base_url)
		models = result.get("models") or []
		return {
			"ok": bool(result.get("ok")),
			"base_url": result.get("base_url") or base_url,
			"models": models,
			"recommended": pick_default_model(models) if models else None,
			"message": result.get("message"),
		}
	return {"ok": False, "models": [], "message": _("Model discovery not implemented for {0}").format(ptype)}


@frappe.whitelist(allow_guest=True, methods=["GET", "POST"])
def whatsapp_webhook(account: str | None = None):
	"""Meta WhatsApp webhook — GET verify, POST inbound messages."""
	from omnexa_ai_employee.engine.channels.inbound import handle_inbound_message
	from omnexa_ai_employee.engine.channels.whatsapp import parse_whatsapp_webhook_payload, verify_whatsapp_webhook

	if frappe.request.method == "GET":
		args = frappe.form_dict
		mode = args.get("hub.mode") or args.get("hub_mode") or ""
		token = args.get("hub.verify_token") or args.get("hub_verify_token") or ""
		challenge = args.get("hub.challenge") or args.get("hub_challenge") or ""
		if mode == "subscribe" and token and challenge:
			verified = verify_whatsapp_webhook(
				mode=mode,
				token=token,
				challenge=challenge,
				account_name=account,
			)
			if verified is not None:
				frappe.local.response.type = "text"
				frappe.local.response.http_status_code = 200
				return verified
		# Browser / health-check without Meta params — do not return 403
		return {
			"ok": True,
			"service": "ERPGENEX AI Employee WhatsApp Webhook",
			"account": account or "whatsapp-main",
			"hint": "Meta verification requires hub.mode=subscribe, hub.verify_token, hub.challenge",
		}

	if not _verify_webhook_token(account):
		frappe.throw(_("Unauthorized webhook call"), frappe.PermissionError)
	frappe.set_user("Administrator")
	payload = frappe.request.get_json(silent=True) or {}
	results = []
	for msg in parse_whatsapp_webhook_payload(payload):
		if not msg.get("text"):
			continue
		results.append(
			handle_inbound_message(
				channel="WhatsApp",
				text=msg["text"],
				sender_id=msg.get("from_phone"),
				account_name=account,
				profile_name=msg.get("profile_name"),
			)
		)
	frappe.db.commit()
	return {"ok": True, "processed": len(results), "results": results}


@frappe.whitelist()
def ocr_document(provider: str | None = None, document_type: str | None = None, file_url: str | None = None) -> dict:
	frappe.only_for(("System Manager", "AI Employee User"))
	return run_ocr(provider=provider, document_type=document_type, file_url=file_url)


@frappe.whitelist()
def process_voice_transcript(transcript: str, agent_code: str | None = None, conversation: str | None = None) -> dict:
	"""Voice → text → intent → ERP action (phase 1: routes transcript to chat)."""
	return chat(message=transcript, agent_code=agent_code, conversation=conversation, channel="Voice")
