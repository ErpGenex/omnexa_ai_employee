# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Hybrid AI routing engine."""

from __future__ import annotations

import frappe
from frappe.utils import cint


def resolve_route_target(user_text: str, agent_role: str | None = None) -> str:
	"""Return Local or Cloud based on configurable routing rules."""
	text = (user_text or "").lower()
	rules = frappe.get_all(
		"AI Routing Rule",
		filters={"enabled": 1},
		fields=["route_target", "match_keywords", "agent_role", "priority"],
		order_by="priority asc",
	)
	for rule in rules:
		if rule.agent_role and agent_role and rule.agent_role != agent_role:
			continue
		keywords = [k.strip().lower() for k in (rule.match_keywords or "").split(",") if k.strip()]
		if not keywords:
			continue
		if any(k in text for k in keywords):
			return rule.route_target or "Local"
	return _default_route()


def _default_route() -> str:
	settings = frappe.get_single("AI Employee Settings")
	return settings.default_route_target or "Local"


def pick_provider(route_target: str) -> str | None:
	rows = frappe.get_all(
		"AI Provider",
		filters={"enabled": 1, "route_target": route_target},
		fields=["name", "is_default"],
		order_by="is_default desc, modified desc",
		limit=1,
	)
	if rows:
		return rows[0].name
	any_row = frappe.get_all("AI Provider", filters={"enabled": 1}, pluck="name", limit=1)
	return any_row[0] if any_row else None


def route_request(*, user_text: str, agent_role: str | None = None) -> dict:
	target = resolve_route_target(user_text, agent_role)
	provider = pick_provider(target)
	return {
		"route_target": target,
		"provider": provider,
		"strategy": frappe.get_single("AI Employee Settings").default_routing_strategy or "Hybrid",
	}
