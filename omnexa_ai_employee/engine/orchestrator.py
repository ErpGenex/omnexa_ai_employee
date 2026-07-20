# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Conversation orchestration: route → complete → persist → optional ERP action."""

from __future__ import annotations

import json

import frappe
from frappe.utils import now_datetime

from omnexa_ai_employee.engine.actions.erp_tools import maybe_execute_erp_action
from omnexa_ai_employee.engine.activities.registry import get_activity_context_prompt, resolve_agent_for_message
from omnexa_ai_employee.engine.providers import get_provider_client
from omnexa_ai_employee.engine.router import route_request


def _settings_enabled() -> bool:
	return bool(frappe.get_single("AI Employee Settings").enabled)


def _agent_doc(agent_code: str | None):
	if not agent_code:
		return None
	if not frappe.db.exists("AI Agent", agent_code):
		frappe.throw(frappe._("AI Agent {0} not found").format(agent_code))
	return frappe.get_doc("AI Agent", agent_code)


def _conversation_doc(conversation: str | None, *, agent_code: str | None, channel: str, customer: str | None):
	if conversation and frappe.db.exists("AI Conversation", conversation):
		return frappe.get_doc("AI Conversation", conversation)
	agent = _agent_doc(agent_code)
	doc = frappe.get_doc(
		{
			"doctype": "AI Conversation",
			"agent": agent.name if agent else None,
			"agent_role": agent.agent_role if agent else None,
			"channel": channel or "Desk",
			"customer": customer,
			"status": "Open",
		}
	)
	doc.insert(ignore_permissions=True)
	return doc


def _append_message(conversation: str, role: str, content: str, meta: dict | None = None) -> str:
	msg = frappe.get_doc(
		{
			"doctype": "AI Conversation Message",
			"conversation": conversation,
			"role": role,
			"content": content,
			"meta_json": json.dumps(meta or {}, ensure_ascii=False),
		}
	)
	msg.insert(ignore_permissions=True)
	return msg.name


def _history_messages(conversation: str, limit: int = 20) -> list[dict]:
	rows = frappe.get_all(
		"AI Conversation Message",
		filters={"conversation": conversation},
		fields=["role", "content"],
		order_by="creation asc",
		limit=limit,
	)
	return [{"role": r.role.lower(), "content": r.content} for r in rows]


def process_chat(
	*,
	message: str,
	agent_code: str | None = None,
	conversation: str | None = None,
	channel: str = "Desk",
	customer: str | None = None,
	company: str | None = None,
) -> dict:
	if not _settings_enabled():
		frappe.throw(frappe._("AI Employee is disabled in settings."))

	agent_code = resolve_agent_for_message(message, agent_code)
	agent = _agent_doc(agent_code)
	conv = _conversation_doc(conversation, agent_code=agent.name if agent else None, channel=channel, customer=customer)
	_append_message(conv.name, "User", message)

	route = route_request(user_text=message, agent_role=agent.agent_role if agent else None)
	if not route.get("provider"):
		reply = frappe._(
			"No AI provider configured for route {0}. Add an AI Provider record."
		).format(route.get("route_target"))
		_append_message(conv.name, "Assistant", reply, {"route": route})
		return {"conversation": conv.name, "reply": reply, "route": route, "provider": None}

	messages = []
	if agent and agent.system_prompt:
		messages.append({"role": "system", "content": agent.system_prompt})
	messages.append({"role": "system", "content": get_activity_context_prompt()})
	if company:
		messages.append({"role": "system", "content": f"Company context: {company}"})
	messages.extend(_history_messages(conv.name))

	client = get_provider_client(route["provider"])
	try:
		result = client.complete(messages=messages)
	except Exception as exc:
		frappe.log_error(frappe.get_traceback(), "AI Employee chat")
		reply = frappe._("AI provider error: {0}").format(str(exc))
		_append_message(conv.name, "Assistant", reply, {"route": route, "error": str(exc)})
		conv.db_set({"status": "Error", "last_activity": now_datetime()})
		return {"conversation": conv.name, "reply": reply, "route": route, "error": str(exc)}

	_append_message(
		conv.name,
		"Assistant",
		result.text,
		{"route": route, "provider": result.provider, "model": result.model},
	)
	action_note = maybe_execute_erp_action(
		user_text=message,
		agent_code=agent.name if agent else None,
		customer=customer,
		conversation=conv.name,
	)
	final_reply = result.text
	if action_note:
		final_reply = f"{result.text}\n\n{action_note}"
		_append_message(conv.name, "System", action_note, {"erp_action": True})
	conv.db_set({"status": "Open", "last_activity": now_datetime(), "last_provider": result.provider})
	frappe.db.commit()

	return {
		"conversation": conv.name,
		"reply": final_reply,
		"route": route,
		"provider": result.provider,
		"model": result.model,
		"erp_action": action_note,
	}
