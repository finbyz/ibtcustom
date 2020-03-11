// Copyright (c) 2016, Finbyz Tech Pvt Ltd and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Comparison of Supplier Quotation"] = {
	"filters": [
		{
			"fieldname": 'name',
			"label": __("ID"),
			"fieldtype": "Data"
		},
		{
			"fieldname": 'supplier',
			"label": __("Supplier"),
			"fieldtype": "Link",
			"options": "Supplier"
		},
		{
			"fieldname": 'material_request',
			"label": __("Material Request"),
			"fieldtype": "Link",
			"options": "Material Request"
		},
		{
			"fieldname": 'item_code',
			"label": __("Item Code"),
			"fieldtype": "Link",
			"options": "Item"
		},
	]
}
