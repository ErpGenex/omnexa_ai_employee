# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe
from frappe.model.document import Document

from omnexa_ai_employee.engine.providers.ollama_setup import pick_default_model, probe_ollama


class AIProvider(Document):
	def validate(self):
		if self.provider_type == "Ollama" and not self.base_url:
			settings_url = frappe.db.get_single_value("AI Employee Settings", "ollama_base_url")
			self.base_url = settings_url or "http://127.0.0.1:11434"
		if self.provider_type == "Ollama" and self.base_url and not self.model_name:
			result = probe_ollama(self.base_url)
			if result.get("ok") and result.get("models"):
				self.model_name = pick_default_model(result["models"])
		if self.is_default:
			frappe.db.sql(
				"""
				UPDATE `tabAI Provider`
				SET is_default = 0
				WHERE route_target = %s AND name != %s
				""",
				(self.route_target, self.name),
			)

