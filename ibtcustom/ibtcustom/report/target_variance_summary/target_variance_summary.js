// Copyright (c) 2016, FinByz Tech Pvt Ltd and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Target Variance Summary"] = {
	"filters": [
		{
			fieldname: 'item_group',
			label: __("Item Group"),
			fieldtype: "Select",
			options: "\nAll Item Groups\ndu Mobile Services\ndu Fixed Services"
		},
		{
			fieldname: "fiscal_year",
			label: __("Fiscal Year"),
			fieldtype: "Link",
			options: "Fiscal Year",
			default: frappe.sys_defaults.fiscal_year
		},
		{
			fieldname: "target_on",
			label: __("Target On"),
			fieldtype: "Select",
			options: "Quantity\nAmount",
			default: "Amount"
		},
	]
}
