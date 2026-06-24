# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""WhatsApp Business Cloud API adapter."""

from __future__ import annotations

import frappe
import requests
from frappe.utils.password import get_decrypted_password


def _channel_doc(account_name: str | None = None):
	name = account_name or frappe.flags.get("ai_whatsapp_account")
	if not name:
		rows = frappe.get_all(
			"AI Channel Account",
			filters={"enabled": 1, "channel_type": "WhatsApp"},
			fields=["name"],
			limit=1,
		)
		name = rows[0].name if rows else None
	if not name or not frappe.db.exists("AI Channel Account", name):
		frappe.throw(frappe._("No enabled WhatsApp channel account configured."))
	return frappe.get_doc("AI Channel Account", name, ignore_permissions=True)


def verify_whatsapp_webhook(*, mode: str, token: str, challenge: str, account_name: str | None = None) -> str | None:
	"""Meta webhook verification (GET)."""
	doc = _channel_doc(account_name)
	expected = (doc.verify_token or "").strip()
	if mode == "subscribe" and token and expected and token == expected:
		return challenge
	return None


def send_whatsapp_text(*, to_phone: str, message: str, account_name: str | None = None) -> dict:
	"""Send text via Meta Graph API."""
	doc = _channel_doc(account_name)
	phone_number_id = (doc.phone_number_id or "").strip()
	api_key = ""
	try:
		api_key = get_decrypted_password("AI Channel Account", doc.name, "api_key")
	except Exception:
		api_key = doc.get_password("api_key") if doc.get("api_key") else ""

	if not phone_number_id or not api_key:
		return {"ok": False, "message": "phone_number_id and api_key required on AI Channel Account"}

	version = (doc.api_version or "v21.0").strip()
	url = f"https://graph.facebook.com/{version}/{phone_number_id}/messages"
	payload = {
		"messaging_product": "whatsapp",
		"to": _normalize_phone(to_phone),
		"type": "text",
		"text": {"body": (message or "")[:4096]},
	}
	resp = requests.post(url, json=payload, headers={"Authorization": f"Bearer {api_key}"}, timeout=30)
	try:
		data = resp.json()
	except Exception:
		data = {"raw": resp.text}
	if resp.ok:
		return {"ok": True, "response": data}
	return {"ok": False, "status_code": resp.status_code, "response": data}


def parse_whatsapp_webhook_payload(payload: dict) -> list[dict]:
	"""Extract normalized inbound messages from Meta webhook JSON."""
	messages: list[dict] = []
	for entry in payload.get("entry") or []:
		for change in entry.get("changes") or []:
			value = change.get("value") or {}
			for msg in value.get("messages") or []:
				text = ""
				if msg.get("type") == "text":
					text = ((msg.get("text") or {}).get("body") or "").strip()
				messages.append(
					{
						"from_phone": msg.get("from"),
						"message_id": msg.get("id"),
						"text": text,
						"timestamp": msg.get("timestamp"),
						"profile_name": ((value.get("contacts") or [{}])[0].get("profile") or {}).get("name"),
					}
				)
	return messages


def _normalize_phone(phone: str) -> str:
	return "".join(ch for ch in (phone or "") if ch.isdigit())
