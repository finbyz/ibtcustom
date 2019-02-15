// Copyright (c) 2013, Finbyz Tech Pvt Ltd and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["HR SLA"] = {
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
			fieldname: "user",
			label: __("User"),
			fieldtype: "Link",
			options: "User"
		}
	]
}
