# Copyright (c) 2026, Omnexa and contributors
# License: MIT

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AICompletionResult:
	text: str
	provider: str
	model: str
	route: str
	usage: dict | None = None
	raw: dict | None = None


class BaseAIProvider:
	provider_type: str = "base"

	def __init__(self, provider_doc):
		self.doc = provider_doc

	def complete(self, *, messages: list[dict], temperature: float | None = None, max_tokens: int | None = None) -> AICompletionResult:
		raise NotImplementedError

	def health_check(self) -> dict:
		return {"ok": False, "message": "Not implemented"}
