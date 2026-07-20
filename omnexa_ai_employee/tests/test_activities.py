# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe
from frappe.tests.utils import FrappeTestCase


class TestActivities(FrappeTestCase):
	def test_installed_activities(self):
		from omnexa_ai_employee.engine.activities.registry import get_installed_activities

		activities = get_installed_activities()
		self.assertIsInstance(activities, list)
		if activities:
			self.assertIn("activity_code", activities[0])
			self.assertIn("agent_role", activities[0])

	def test_resolve_agent_for_trading_message(self):
		from omnexa_ai_employee.engine.activities.registry import resolve_agent_for_message

		agent = resolve_agent_for_message("create van sales invoice for customer")
		if agent:
			role = frappe.get_value("AI Agent", agent, "agent_role")
			self.assertIn(role, ("Trading", "Sales", "Operations", "Customer Service", "Healthcare", "Education", "Tourism", "Finance", "HR", "Manufacturing", "Projects", "Accounting", "Agriculture", "Construction", "Restaurant", "Legal", "Risk"))

	def test_resolve_action_patterns(self):
		from omnexa_ai_employee.engine.activities.registry import resolve_action

		self.assertEqual(resolve_action("please create a quotation", "sales"), "sales_quotation")
		self.assertEqual(resolve_action("open a support ticket", "support"), "support_ticket")
		self.assertEqual(resolve_action("book appointment", "healthcare"), "healthcare_appointment")

	def test_list_action_capabilities(self):
		from omnexa_ai_employee.engine.activities.registry import list_action_capabilities

		rows = list_action_capabilities()
		self.assertGreater(len(rows), 3)
		self.assertIn("action", rows[0])
		self.assertIn("available", rows[0])

	def test_sync_activity_agents_idempotent(self):
		from omnexa_ai_employee.engine.activities.registry import sync_activity_agents

		first = sync_activity_agents()
		second = sync_activity_agents()
		self.assertIsInstance(first, dict)
		self.assertGreaterEqual(second.get("skipped", 0), 0)
