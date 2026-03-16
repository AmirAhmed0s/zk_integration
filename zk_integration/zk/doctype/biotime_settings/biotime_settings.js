// Copyright (c) 2022, Peter and contributors
// For license information, please see license.txt

frappe.ui.form.on('BioTime Settings', {
	refresh: function(frm) {
		frm.add_custom_button(__("Test Connection"), function() {
			frappe.call({
				method: "zk_integration.zk.doctype.zk_device.bio_time.test_bio_connection",
				freeze: true,
				freeze_message: __("Testing BioTime connection..."),
				callback: function(r) {
					// Success message is shown by the server via frappe.msgprint
				},
				error: function(r) {
					// Error message is shown by the server via frappe.throw
				}
			});
		}, __("Actions"));
	}
});
