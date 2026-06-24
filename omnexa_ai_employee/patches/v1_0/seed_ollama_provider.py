# Copyright (c) 2026, Omnexa and contributors
# License: MIT

from omnexa_ai_employee.engine.providers.ollama_setup import bootstrap_ollama_provider


def execute():
	bootstrap_ollama_provider(save=True)
