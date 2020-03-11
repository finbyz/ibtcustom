// Copyright (c) 2017, FinByz Tech Pvt Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on('Meeting', {
	refresh: function(frm) {

	}
});



frappe.ui.form.on('Meeting Customer', {
	contact: function(frm,cdt,cdn) {
		var d = locals[cdt][cdn]; 
		frappe.call({
			method: "ibtcustom.api.set_person_name",
			args: {
				contact: d.contact
			},
			callback: function(r){
				frappe.model.set_value(cdt, cdn, "person_name", r.message[0]);
				frappe.model.set_value(cdt, cdn, "email_id", r.message[1]);
			}
		});
	}
});