// Copyright (c) 2026, Enterprise Platform and contributors
// For license information, please see license.txt

// Guided Demo Mode (master plan §16) — real "Start Demo" UI. This is a DocType client script
// (loaded live from disk per-request, same mechanism every other custom hook in this codebase
// relies on — needs `bench clear-cache` after an edit, not a `bench build`), not a Frappe Page:
// deliberately chosen because the `frontend` container in this stack does not currently receive
// enterprise_core's source via bind mount (only backend/queue/scheduler/websocket/configurator
// do — see frappe_docker_demo/overrides/compose.enterprise-core-dev.yaml), so a Page's JS/asset
// bundle would need a manual `bench build` step this environment isn't wired for. A doctype
// client script needs no such step, matching this codebase's own established, low-risk pattern.

frappe.ui.form.on("Guided Demo Scenario", {
	refresh(frm) {
		frm.page.set_primary_action(__("Start Demo"), () => start_guided_demo(frm));

		if (!frm.is_new()) {
			frm.dashboard.clear_headline();
			const badge = frm.doc.is_active
				? `<span class="indicator-pill green">${__("Active")}</span>`
				: `<span class="indicator-pill gray">${__("Inactive")}</span>`;
			frm.dashboard.set_headline(
				`${badge} ${__("Golden Demo")}: ${frappe.utils.escape_html(frm.doc.golden_demo_reference || "—")} &middot; ${(frm.doc.steps || []).length} ${__("steps")}`
			);
		}
	},
});

function start_guided_demo(frm) {
	if (frm.is_dirty()) {
		frappe.msgprint(__("Please save before starting the demo."));
		return;
	}

	const steps = (frm.doc.steps || []).slice().sort((a, b) => (a.step_no || 0) - (b.step_no || 0));

	const steps_html = steps.length
		? `<ol class="guided-demo-steps" style="padding-left: 1.4em;">${steps
				.map((s) => {
					const role_bits = [];
					if (s.login_as_role) role_bits.push(`<strong>${__("Login as")}:</strong> ${frappe.utils.escape_html(s.login_as_role)}`);
					if (s.login_as_user) role_bits.push(`<span class="text-muted">(${frappe.utils.escape_html(s.login_as_user)})</span>`);
					const role_line = role_bits.length ? `<div class="text-muted small">${role_bits.join(" ")}</div>` : "";

					let link_html = "";
					if (s.direct_link && s.target_doctype && s.target_document) {
						link_html = `<div style="margin-top: 4px;">
							<a href="#" class="btn btn-xs btn-default guided-demo-open-record" data-link="${frappe.utils.escape_html(s.direct_link)}">
								${frappe.utils.escape_html("Open " + s.target_doctype + ": " + s.target_document)} &rarr;
							</a>
						</div>`;
					}
					const notes_line = s.notes ? `<div class="text-muted small" style="margin-top: 2px;">${frappe.utils.escape_html(s.notes)}</div>` : "";

					return `<li style="margin-bottom: 14px;">
						<div><strong>${frappe.utils.escape_html(s.instruction || "")}</strong></div>
						${role_line}
						${link_html}
						${notes_line}
					</li>`;
				})
				.join("")}</ol>`
		: `<p class="text-muted">${__("No steps defined for this scenario.")}</p>`;

	const body = `
		<div class="guided-demo-dialog">
			<div style="margin-bottom: 16px;">
				<h6>${__("Objective")}</h6>
				<p>${frappe.utils.escape_html(frm.doc.objective || "")}</p>
				${
					frm.doc.primary_login_role
						? `<p class="text-muted small"><strong>${__("Primary login")}:</strong> ${frappe.utils.escape_html(frm.doc.primary_login_role)}${
								frm.doc.primary_login_user ? " (" + frappe.utils.escape_html(frm.doc.primary_login_user) + ")" : ""
						  }</p>`
						: ""
				}
			</div>
			<div style="margin-bottom: 16px;">
				<h6>${__("Steps")}</h6>
				${steps_html}
			</div>
			<div style="margin-bottom: 8px; padding: 10px; background: var(--subtle-fg, #f5f5f5); border-radius: 6px;">
				<h6>${__("What This Demonstrates")}</h6>
				<p style="margin-bottom: 0;">${frappe.utils.escape_html(frm.doc.what_this_demonstrates || "")}</p>
			</div>
		</div>
	`;

	const dialog = new frappe.ui.Dialog({
		title: __("Start Demo: {0}", [frm.doc.title]),
		size: "large",
		fields: [{ fieldtype: "HTML", fieldname: "walkthrough_html", options: body }],
	});

	// Clicking a step's "Open record" link navigates Desk to that record directly, without
	// closing the walkthrough dialog behind it (opens in the SAME tab via frappe.set_route so
	// the salesperson can use the browser back button to return here — a new tab was considered
	// but a live sales demo is more often shown on a single shared screen).
	dialog.$wrapper.on("click", ".guided-demo-open-record", (e) => {
		e.preventDefault();
		const link = $(e.currentTarget).attr("data-link");
		if (link) frappe.set_route(link.replace(/^\/app\//, "").split("/"));
	});

	if (frm.doc.allow_reset && frm.doc.reset_function_path) {
		dialog.set_secondary_action_label(__("Reset Scenario"));
		dialog.set_secondary_action(() => {
			frappe.confirm(
				__("This re-asserts the scenario's real golden-demo data (safe, idempotent) — it does not undo anything a viewer clicked. Continue?"),
				() => {
					frappe.call({
						method: "enterprise_core.enterprise_core.guided_demo.reset_guided_demo_scenario",
						args: { scenario_code: frm.doc.name },
						freeze: true,
						freeze_message: __("Resetting..."),
						callback: (r) => {
							const res = r.message || {};
							if (res.status === "ok") {
								frappe.show_alert({ message: __("Reset complete."), indicator: "green" });
							} else {
								frappe.msgprint({
									title: __("Reset Not Available"),
									message: frappe.utils.escape_html(res.message || __("Unknown response.")),
									indicator: "orange",
								});
							}
						},
					});
				}
			);
		});
	} else {
		// Honest, visible "not available" state rather than silently omitting the button —
		// master plan explicitly forbids faking a working reset.
		dialog.set_secondary_action_label(__("Reset Scenario (Not Available)"));
		dialog.set_secondary_action(() => {
			frappe.msgprint({
				title: __("Reset Not Available"),
				message: frappe.utils.escape_html(
					frm.doc.reset_instructions || __("No reset mechanism has been built for this scenario.")
				),
				indicator: "orange",
			});
		});
	}

	dialog.show();
}
