frappe.ui.form.on("Project Task", {
    before_project_tasks_remove: function (frm, cdt, cdn) {
        let d = locals[cdt][cdn]
        if (d.task_id) {
            frappe.call({
                'method': 'ibtcustom.api.remove_project_reference',
                'args': {
                    'task_name': d.task_id
                }
            })
           	
        }
    }
})
