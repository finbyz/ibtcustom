cur_frm.fields_dict.project_type.get_query = function(doc) {
	return {
        "filters": [
            ["project_type", "in", ["IT Hardware/Software","IT Infrastructure","Cloud Computing","Axira Business Solutions","IT Outsourcing – Part Time","IT Outsourcing – Full Time","One Time Support","Call Center Outsourcing","Business Process Outsourcing"]]
        ]
    };
};

frappe.ui.form.on("Project Task", {
    before_project_tasks_remove: function (frm, cdt, cdn) {
        let d = locals[cdt][cdn]
        if (d.task_id) {
            frappe.call({
                'method': 'ibtcustom.api.remove_project_reference',
                'args': {
                    'task_name': d.task_id
                }
            });
           	
        }
    }
})