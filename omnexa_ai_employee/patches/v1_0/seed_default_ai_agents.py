# Copyright (c) 2026, Omnexa
import frappe


def execute():
	from omnexa_ai_employee.install import bootstrap_defaults

	bootstrap_defaults()
