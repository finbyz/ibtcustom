
frappe.ui.form.on("Leave Allocation", {
    onload: function(frm) {
        frm.set_query("leave_type", function() {
			return {
				filters: [
				    // 'is_lwp': 0,
				   // 'name': "Annual Leave"
				  ['is_lwp', 'in',['0','1'] ]
				    
				]
			}
		})
    }
});