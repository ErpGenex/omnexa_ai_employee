frappe.pages["ai-employee-workcenter"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({ parent: wrapper, title: __("AI Employee Workcenter"), single_column: true });
	const $body = $(page.body);
	$body.addClass("ai-employee-workcenter");

	function providerStatusHtml(ollama, providerHealth) {
		const ok = ollama && ollama.ok;
		const indicator = ok ? "green" : "red";
		const models = (ollama && ollama.models) || [];
		const modelText = models.length ? models.slice(0, 5).join(", ") : __("No models pulled");
		let rows = (providerHealth || [])
			.map((p) => {
				const h = p.health || {};
				const cls = h.ok ? "green" : "orange";
				return `<li><span class="indicator ${cls}"></span> <strong>${frappe.utils.escape_html(p.provider_name || p.name)}</strong> — ${frappe.utils.escape_html(p.model_name || "")} ${h.ok ? __("online") : frappe.utils.escape_html(h.message || __("offline"))}</li>`;
			})
			.join("");
		return `
			<div class="panel panel-default" style="margin-bottom:16px">
				<div class="panel-heading"><strong>${__("Ollama (Local AI)")}</strong></div>
				<div class="panel-body">
					<p><span class="indicator ${indicator}"></span> ${ok ? __("Connected") : __("Not reachable")} — <code>${frappe.utils.escape_html((ollama && ollama.base_url) || "")}</code></p>
					<p class="text-muted">${__("Models")}: ${frappe.utils.escape_html(modelText)}</p>
					${!ok ? `<p class="text-muted">${__("Install Ollama on the server, run")} <code>ollama pull llama3.2</code>, ${__("or set Ollama Base URL in AI Employee Settings for a remote host.")}</p>` : ""}
					<ul class="list-unstyled">${rows || `<li class="text-muted">${__("No providers configured")}</li>`}</ul>
					<button class="btn btn-default btn-sm ai-refresh-ollama">${__("Refresh Status")}</button>
					<button class="btn btn-default btn-sm ai-bootstrap-ollama">${__("Sync Ollama Provider")}</button>
				</div>
			</div>
		`;
	}

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
				${providerStatusHtml(d.ollama, d.provider_health)}
				<div class="row">
					<div class="col-sm-3"><div class="widget"><h4>${kpis.active_conversations || 0}</h4><p>${__("Active Conversations")}</p></div></div>
					<div class="col-sm-3"><div class="widget"><h4>${kpis.orders_generated || 0}</h4><p>${__("Orders Generated")}</p></div></div>
					<div class="col-sm-3"><div class="widget"><h4>${kpis.appointments_created || 0}</h4><p>${__("Appointments")}</p></div></div>
					<div class="col-sm-3"><div class="widget"><h4>${kpis.ai_providers || 0}</h4><p>${__("AI Providers")}</p></div></div>
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
						<div class="form-inline" style="gap:8px;margin-bottom:8px;display:flex;flex-wrap:wrap">
							<select class="form-control ai-agent-select">${agents.map((a) => `<option value="${a.name}">${frappe.utils.escape_html(a.agent_name)}</option>`).join("")}</select>
							<input class="form-control ai-chat-input" style="min-width:320px;flex:1" placeholder="${__("Type a message...")}" />
							<button class="btn btn-primary ai-chat-send">${__("Send")}</button>
						</div>
						<pre class="ai-chat-log" style="min-height:160px;max-height:360px;overflow:auto;background:#f8fafc;padding:12px;border-radius:8px;white-space:pre-wrap"></pre>
					</div>
				</div>
			`);
			let conversation = null;
			const $log = $body.find(".ai-chat-log");

			async function sendChat() {
				const message = ($body.find(".ai-chat-input").val() || "").trim();
				const agent_code = $body.find(".ai-agent-select").val();
				if (!message) return;
				$log.append(`\n> ${message}`);
				$body.find(".ai-chat-send").prop("disabled", true);
				try {
					const r = await frappe.call({
						method: "omnexa_ai_employee.api.chat",
						args: { message, agent_code, conversation },
					});
					conversation = r.message.conversation;
					const route = (r.message.route || {}).route_target || "";
					const provider = r.message.provider || "";
					const model = r.message.model || "";
					$log.append(`\n${r.message.reply || ""}\n[${route}${provider ? ` · ${provider}` : ""}${model ? ` · ${model}` : ""}]`);
				} catch (e) {
					$log.append(`\n${__("Error")}: ${e.message || e}`);
				} finally {
					$body.find(".ai-chat-send").prop("disabled", false);
					$body.find(".ai-chat-input").val("").focus();
				}
			}

			$body.find(".ai-chat-send").on("click", sendChat);
			$body.find(".ai-chat-input").on("keydown", (ev) => {
				if (ev.key === "Enter" && !ev.shiftKey) {
					ev.preventDefault();
					sendChat();
				}
			});
			$body.find(".ai-refresh-ollama").on("click", () => render());
			$body.find(".ai-bootstrap-ollama").on("click", async () => {
				await frappe.call({ method: "omnexa_ai_employee.api.bootstrap_ollama" });
				frappe.show_alert({ message: __("Ollama provider synced"), indicator: "green" });
				render();
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
