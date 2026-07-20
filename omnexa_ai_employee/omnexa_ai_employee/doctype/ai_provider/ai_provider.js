// Copyright (c) 2026, Omnexa and contributors
// License: MIT

frappe.ui.form.on("AI Provider", {
	refresh(frm) {
		if (frm.doc.provider_type === "Ollama") {
			frm.add_custom_button(__("Discover Models"), () => discover_models(frm));
		}
		if (frm.doc.provider_type === "Ollama" && frm.doc.base_url && !frm._models_loaded) {
			discover_models(frm, { quiet: true });
		}
	},
	provider_type(frm) {
		frm._models_loaded = false;
		if (frm.doc.provider_type === "Ollama" && frm.doc.base_url) {
			discover_models(frm, { quiet: true });
		}
	},
	base_url(frm) {
		if (frm.doc.provider_type !== "Ollama" || !frm.doc.base_url) {
			return;
		}
		clearTimeout(frm._model_discover_timer);
		frm._model_discover_timer = setTimeout(() => discover_models(frm, { quiet: true }), 500);
	},
});

async function discover_models(frm, opts = {}) {
	const quiet = !!opts.quiet;
	if (!frm.doc.base_url) {
		if (!quiet) frappe.msgprint(__("Enter a Base URL first."));
		return;
	}
	if (!quiet) frappe.show_alert({ message: __("Discovering models..."), indicator: "blue" });
	try {
		const r = await frappe.call({
			method: "omnexa_ai_employee.api.discover_provider_models",
			args: {
				base_url: frm.doc.base_url,
				provider_type: frm.doc.provider_type,
			},
		});
		const data = r.message || {};
		const models = data.models || [];
		frm._models_loaded = true;
		if (models.length) {
			frm.set_df_property("model_name", "options", models.join("\n"));
			if (!frm.doc.model_name || !models.includes(frm.doc.model_name)) {
				frm.set_value("model_name", data.recommended || models[0]);
			}
			if (!quiet) {
				frappe.show_alert({
					message: __("Found {0} models", [models.length]),
					indicator: "green",
				});
			}
		} else if (!quiet) {
			frappe.msgprint({
				title: __("No models found"),
				message: data.message || __("Could not reach Ollama or no models are installed."),
				indicator: "orange",
			});
		}
	} catch (e) {
		if (!quiet) frappe.msgprint({ title: __("Discovery failed"), message: e.message || String(e), indicator: "red" });
	}
}
