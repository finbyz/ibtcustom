// Copyright (c) 2016, Finbyz Tech Pvt Ltd and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Invoice Audit Report"] = {
	"filters": [
		{
			fieldname: 'customer',
			label: __("Customer"),
			fieldtype: "Link",
			options: "Customer"
		}
	]
}
