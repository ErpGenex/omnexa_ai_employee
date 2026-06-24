# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe
from frappe.model.document import Document
from frappe.utils import get_url


class AIChannelAccount(Document):
	def validate(self):
		if self.channel_type == "WhatsApp":
			self.webhook_url = get_url(
				f"/api/method/omnexa_ai_employee.api.whatsapp_webhook?account={self.name}"
			)
