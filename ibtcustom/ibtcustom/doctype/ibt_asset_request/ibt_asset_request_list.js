frappe.listview_settings['IBT Asset Request'] = {
	add_fields: ["workflow_state"],
	get_indicator: function(doc) {
		return [__(doc.workflow_state), {
			"Applied": "orange",
			"Approved": "blue",
			"Transferred": "yellow",
			"Acknowledged": "green",
			"Returned": "lightblue",
			"Received": "black",
			"Rejected": "red",
			"Cancelled": "red"
		}[doc.workflow_state], "workflow_state,=," + doc.workflow_state];

		// if(doc.workflow_state=="Applied") {
		// 	return [__(doc.workflow_state), "orange"];
		// }
		// else if(doc.workflow_state=="Approved"){
		// 	return [__(doc.workflow_state), "blue"];
		// }
		// else if(doc.workflow_state=="Transferred"){
		// 	return [__(doc.workflow_state), "yellow"];
		// }
		// else if(doc.workflow_state=="Acknowledged") {
		// 	return [__(doc.workflow_state), "green"];
		// }
		// else if(doc.workflow_state=="Returned"){
		// 	return [__(doc.workflow_state), "lightblue"];
		// }
		// else if(doc.workflow_state=="Received"){
		// 	return [__(doc.workflow_state), "black"];
		// }
		// else if(doc.workflow_state=="Rejected"){
		// 	return [__(doc.workflow_state), "red"];
		// }
		// else{
		// 	return [__(doc.workflow_state), "red"];
		// }
	}
};