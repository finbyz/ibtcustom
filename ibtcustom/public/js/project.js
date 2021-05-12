cur_frm.fields_dict.project_type.get_query = function(doc) {
	return {
        "filters": [
            ["project_type", "in", ["IT Hardware / Software", "IT Infrastructure", "Cloud Computing", "Axira Business Solutions", "Annual Maintenance Contract", "IT Outsourcing - Part Time", "IT Outsourcing- Full-time", "One Time  Support", "Call Center Outsourcing","Business Process Outsourcing"]]
        ]
    };
};

frappe.ui.form.on("Project", {
    project_type: function (frm) {
        frappe.db.get_value("Project Template",{'project_type': frm.doc.project_type}, 'name', (r) => {
            frm.set_value('project_template', r.name);
        });
    },
    before_save: function (frm) {
        if (frm.doc.sales_order && (!frm.doc.project_type || frm.doc.project_type == "External")) {
            frappe.db.get_value("Sales Order", frm.doc.sales_order, 'project_type', (r) => {
                frm.set_value('project_type', r.project_type);
            });
        }
        if (frm.doc.__islocal) {
            frappe.db.get_value("Project Template", { 'project_type': frm.doc.project_type }, 'name', (m) => {
                frm.set_value('project_template', m.name);
            });
        }
        
    }
});

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
});
