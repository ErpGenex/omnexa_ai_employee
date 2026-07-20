# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe


def execute():
	from omnexa_ai_employee.install import sync_agents_from_install

	sync_agents_from_install()
