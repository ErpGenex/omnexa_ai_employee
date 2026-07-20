# Copyright (c) 2026, Omnexa and contributors
# License: MIT

from omnexa_ai_employee.workspace.ai_employee_workspace import sync_ai_employee_workspace


def execute():
	sync_ai_employee_workspace(save=True, rebuild=True)
