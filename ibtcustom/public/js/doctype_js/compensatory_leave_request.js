frappe.ui.form.on('Compensatory Leave Request', {
	onload: function(frm) {
		if (frm.doc.__islocal){
			frappe.db.get_value("Employee",{user_id: frappe.session.user},'name',function(d){
				if(d.name){
					frm.set_value("employee",d.name)
				}
				
			});
		}
	},
    validate: function(frm){
        if(frm.doc.leave_approver && frm.doc.__islocal && frm.doc.workflow_state == "Approved") {
            var msg = "Email sent to "+ frm.doc.leave_approver
    	    frappe.msgprint(msg);
		}
		if(frm.doc.status == "Approved") {
			// console.log("not approved");
			console.log("Status changed");
			var msg = "Email sent to "+ frm.doc.owner
			frappe.msgprint(msg);
		}
	},
	status: function(frm) {
		if(frm.doc.status == "Approved") {
			console.log("Status changed");
			var msg = "Email sent to "+ frm.doc.owner
			frappe.msgprint(msg);
		}
	}
});