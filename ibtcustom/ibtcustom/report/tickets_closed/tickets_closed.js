// Copyright (c) 2016, Finbyz Tech Pvt Ltd and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Tickets Closed"] = {
	"filters": [
		{
			fieldname: "from_date",
			label:__("From Date"),
			fieldtype: "Date",
			default : frappe.datetime.add_days(frappe.datetime.nowdate(), -30)
		},
		{
			fieldname: "to_date",
			label:__("To Date"),
			fieldtype: "Date",
			default : frappe.datetime.nowdate()
		},
		{
			fieldname: "engineer_name",
			label: __("Engineer Name"),
			fieldtype: "Link",
			options: "Engineer Group"
		}
	]
}
