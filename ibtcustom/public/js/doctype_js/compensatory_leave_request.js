frappe.ui.form.on('Compensatory Leave Request', {
	onload: function(frm) {
		if (frm.doc.__islocal){
			frappe.db.get_value("Employee",{user_id: frappe.session.user},'name',function(d){
				frm.set_value("employee",d.name)
			});
		}
	},
    before_save: function(frm){
        if(frm.doc.leave_approver && frm.doc.__islocal) {
            var msg = "Email sent to "+ frm.doc.leave_approver
    	    frappe.msgprint(msg);
        }
	},
	on_submit: function(frm){
	     var msg = "Email sent to "+ frm.doc.owner
	     frappe.msgprint(msg);
	}
});