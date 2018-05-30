frappe.listview_settings['IBT Asset Return'] = {
	add_fields: ["workflow_state"],
	get_indicator: function(doc) {
		return [__(doc.workflow_state), {
			"Returned": "lightblue",
			"Received": "black",
			"Cancelled": "red"
		}[doc.workflow_state], "workflow_state,=," + doc.workflow_state];
	}
};