# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Route inbound channel messages to AI orchestrator + ERP actions."""

from __future__ import annotations

import frappe

from omnexa_ai_employee.engine.channels.whatsapp import send_whatsapp_text
from omnexa_ai_employee.engine.orchestrator import process_chat


def _resolve_channel_account(channel_type: str, account_name: str | None = None):
	filters = {"enabled": 1, "channel_type": channel_type}
	if account_name:
		filters["name"] = account_name
	rows = frappe.get_all("AI Channel Account", filters=filters, fields=["name", "default_agent"], limit=1)
	return rows[0] if rows else None


def handle_inbound_message(
	*,
	channel: str,
	text: str,
	sender_id: str,
	account_name: str | None = None,
	profile_name: str | None = None,
) -> dict:
	if not (text or "").strip():
		return {"ok": False, "message": "Empty message"}

	account = _resolve_channel_account(channel, account_name)
	agent_code = account.default_agent if account else None
	customer = _resolve_customer(channel, sender_id, profile_name)

	result = process_chat(
		message=text.strip(),
		agent_code=agent_code,
		channel=channel,
		customer=customer,
	)

	reply = result.get("reply") or ""

	outbound = None
	if channel == "WhatsApp" and sender_id:
		try:
			outbound = send_whatsapp_text(to_phone=sender_id, message=reply, account_name=account.name if account else None)
		except Exception as exc:
			outbound = {"ok": False, "message": str(exc)}

	return {
		"ok": True,
		"conversation": result.get("conversation"),
		"reply": reply,
		"route": result.get("route"),
		"outbound": outbound,
		"erp_action": result.get("erp_action"),
	}


def _resolve_customer(channel: str, sender_id: str, profile_name: str | None) -> str | None:
	"""Link WhatsApp phone to Customer when possible."""
	phone = "".join(ch for ch in (sender_id or "") if ch.isdigit())
	if not phone or not frappe.db.exists("DocType", "Customer"):
		return profile_name if profile_name and frappe.db.exists("Customer", profile_name) else None

	candidate_fields = [f for f in ("mobile_no", "phone", "contact_mobile") if frappe.db.has_column("Customer", f)]
	for field in candidate_fields:
		name = frappe.db.get_value("Customer", {field: ["like", f"%{phone[-9:]}%"]}, "name")
		if name:
			return name
	if profile_name and frappe.db.exists("Customer", profile_name):
		return profile_name
	return None
