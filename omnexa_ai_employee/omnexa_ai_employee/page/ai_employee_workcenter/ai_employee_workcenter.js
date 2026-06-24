frappe.pages["ai-employee-workcenter"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({ parent: wrapper, title: __("AI Employee Workcenter"), single_column: true });
	const $body = $(page.body);
	$body.addClass("ai-employee-workcenter");

	async function render() {
		$body.html(`<div class="text-muted">${__("Loading AI Employee dashboard...")}</div>`);
		try {
			const data = await frappe.call({
				method: "omnexa_ai_employee.api.get_dashboard",
			});
			const d = data.message || {};
			const kpis = d.kpis || {};
			const agents = d.agents || [];
			const gaps = (d.audit_summary && d.audit_summary.gaps) || [];
			$body.html(`
				<div class="row">
					<div class="col-sm-3"><div class="widget"><h4>${kpis.active_conversations || 0}</h4><p>${__("Active Conversations")}</p></div></div>
					<div class="col-sm-3"><div class="widget"><h4>${kpis.orders_generated || 0}</h4><p>${__("Orders Generated")}</p></div></div>
					<div class="col-sm-3"><div class="widget"><h4>${kpis.appointments_created || 0}</h4><p>${__("Appointments")}</p></div></div>
					<div class="col-sm-3"><div class="widget"><h4">${kpis.ai_providers || 0}</h4><p>${__("AI Providers")}</p></div></div>
				</div>
				<div class="row" style="margin-top:16px">
					<div class="col-sm-6">
						<h5>${__("AI Agents")}</h5>
						<ul class="list-unstyled">${agents.map((a) => `<li><strong>${frappe.utils.escape_html(a.agent_name)}</strong> — ${frappe.utils.escape_html(a.agent_role)}</li>`).join("")}</ul>
					</div>
					<div class="col-sm-6">
						<h5>${__("Gap Analysis")}</h5>
						<ul>${gaps.map((g) => `<li><span class="indicator ${g.severity === "High" ? "red" : "orange"}"></span> ${frappe.utils.escape_html(g.area)}: ${frappe.utils.escape_html(g.detail)}</li>`).join("") || `<li class="text-muted">${__("No critical gaps")}</li>`}</ul>
						<button class="btn btn-primary btn-sm ai-run-audit">${__("Run Ecosystem Audit")}</button>
					</div>
				</div>
				<div class="row" style="margin-top:16px">
					<div class="col-sm-12">
						<h5>${__("Chat Console")}</h5>
						<div class="form-inline" style="gap:8px;margin-bottom:8px">
							<select class="form-control ai-agent-select">${agents.map((a) => `<option value="${a.name}">${frappe.utils.escape_html(a.agent_name)}</option>`).join("")}</select>
							<input class="form-control ai-chat-input" style="min-width:320px" placeholder="${__("Type a message...")}" />
							<button class="btn btn-primary ai-chat-send">${__("Send")}</button>
						</div>
						<pre class="ai-chat-log" style="min-height:120px;background:#f8fafc;padding:12px;border-radius:8px"></pre>
					</div>
				</div>
			`);
			let conversation = null;
			$body.find(".ai-chat-send").on("click", async () => {
				const message = ($body.find(".ai-chat-input").val() || "").trim();
				const agent_code = $body.find(".ai-agent-select").val();
				if (!message) return;
				const $log = $body.find(".ai-chat-log");
				$log.append(`\n> ${message}`);
				const r = await frappe.call({
					method: "omnexa_ai_employee.api.chat",
					args: { message, agent_code, conversation },
				});
				conversation = r.message.conversation;
				$log.append(`\n${r.message.reply || ""}\n[route: ${(r.message.route || {}).route_target || ""}]`);
				$body.find(".ai-chat-input").val("");
			});
			$body.find(".ai-run-audit").on("click", async () => {
				const r = await frappe.call({ method: "omnexa_ai_employee.api.run_audit" });
				frappe.msgprint({ message: __("Audit complete. Installed apps: {0}", [r.message.installed_apps]), indicator: "green" });
				render();
			});
		} catch (e) {
			$body.html(`<div class="text-danger">${__("Failed to load dashboard")}</div>`);
		}
	}

	render();
};
