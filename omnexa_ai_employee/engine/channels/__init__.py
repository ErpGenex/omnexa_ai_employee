# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Outbound + inbound channel handlers."""

from omnexa_ai_employee.engine.channels.inbound import handle_inbound_message
from omnexa_ai_employee.engine.channels.whatsapp import send_whatsapp_text, verify_whatsapp_webhook

__all__ = ["handle_inbound_message", "send_whatsapp_text", "verify_whatsapp_webhook"]
