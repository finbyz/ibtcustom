// Copyright (c) 2020, Finbyz Tech Pvt Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on('Role Restriction', {
	apply_to_all_doctypes: function (frm) {
		if (frm.doc.apply_to_all_doctypes){
			cur_frm.set_df_property("applicable_for", "reqd", 0);
		}
		else {
			cur_frm.set_df_property("applicable_for", "reqd", 1);
		}
	},
	allow: function (frm) {
		if (frm.doc.allow != "Employee" || frm.doc.allow != "User"){
			cur_frm.set_df_property("for_value", "reqd", 1);
		}
		else {
			cur_frm.set_df_property("for_value", "reqd", 0);
		}
	}
});
