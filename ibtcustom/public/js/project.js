frappe.ui.form.on("Project Task", {
    before_tasks_remove: function (frm, cdt, cdn) {
        let d = locals[cdt][cdn]
        if (d.task_id) {
            frappe.call({
                'method': 'ibtcustom.api.remove_project_reference',
                'args': {
                    'task_name': d.task_id
                }
            })
            // frappe.model.with_doc("Task", d.task_id, function () {
            //     var task_doc = frappe.model.get_doc("Task", d.task_id);
            //     console.log(task_doc)
                
            // });	
        }
    }
})
