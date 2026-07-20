# Copyright (c) 2026, Omnexa and contributors
# License: MIT

from frappe.tests.utils import FrappeTestCase


class TestAiEmployee(FrappeTestCase):
	def test_routing_local_keyword(self):
		from omnexa_ai_employee.engine.router import resolve_route_target

		self.assertIn(resolve_route_target("product lookup for item ABC"), ("Local", "Cloud"))

	def test_ecosystem_audit(self):
		from omnexa_ai_employee.engine.audit.ecosystem_audit import run_ecosystem_audit

		result = run_ecosystem_audit()
		self.assertIn("installed_apps", result)
		self.assertIn("gaps", result)

	def test_pick_default_model(self):
		from omnexa_ai_employee.engine.providers.ollama_setup import pick_default_model

		self.assertEqual(pick_default_model(["llama3.2:latest", "mistral:7b"]), "llama3.2:latest")
		self.assertEqual(pick_default_model(["custom-model"]), "custom-model")
		self.assertEqual(pick_default_model([], preferred="llama3.2"), "llama3.2")
