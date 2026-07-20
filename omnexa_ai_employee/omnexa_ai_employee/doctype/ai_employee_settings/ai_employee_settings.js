// Copyright (c) 2026, Omnexa and contributors
// License: MIT

frappe.ui.form.on("AI Employee Settings", {
	refresh(frm) {
		frm.add_custom_button(__("Discover Ollama Models"), () => discover_ollama_settings(frm));
	},
	ollama_base_url(frm) {
		if (!frm.doc.ollama_base_url) return;
		clearTimeout(frm._ollama_discover_timer);
		frm._ollama_discover_timer = setTimeout(() => discover_ollama_settings(frm, { quiet: true }), 500);
	},
});

async function discover_ollama_settings(frm, opts = {}) {
	const quiet = !!opts.quiet;
	if (!frm.doc.ollama_base_url) {
		if (!quiet) frappe.msgprint(__("Enter Ollama Base URL first."));
		return;
	}
	try {
		const r = await frappe.call({
			method: "omnexa_ai_employee.api.discover_provider_models",
			args: { base_url: frm.doc.ollama_base_url, provider_type: "Ollama" },
		});
		const data = r.message || {};
		const models = data.models || [];
		if (models.length) {
			if (!frm.doc.ollama_default_model || !models.includes(frm.doc.ollama_default_model)) {
				frm.set_value("ollama_default_model", data.recommended || models[0]);
			}
			if (!quiet) {
				frappe.msgprint({
					title: __("Ollama Models"),
					message: models.slice(0, 12).join("<br>") + (models.length > 12 ? `<br>...+${models.length - 12}` : ""),
					indicator: "green",
				});
			}
		} else if (!quiet) {
			frappe.msgprint({
				title: __("No models"),
				message: data.message || __("Ollama unreachable"),
				indicator: "orange",
			});
		}
	} catch (e) {
		if (!quiet) frappe.msgprint({ title: __("Discovery failed"), message: e.message || String(e), indicator: "red" });
	}
}
