# Copyright (c) 2013, Finbyz Tech Pvt Ltd and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils.user import get_user_fullname
from frappe.utils import getdate, nowdate, add_days

def execute(filters=None):
	filters.from_date = getdate(filters.from_date or add_days(nowdate(), -30))
	filters.to_date = getdate(filters.to_date or nowdate())
	columns, data = [], []
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	columns = [
		_("User ID") + ":Link/User:140",
		_("User Name") + ":Data:160",
		_("Total Tickets Worked") + ":Int:150",
		_("Tickets Closed within SLA") + ":Int:180",
		_("Tickets Violated SLA") + ":Int:150",
		_("Total % within SLA") + ":Float:140",
		_("Total % Violated SLA") + ":Float:150",
	]
	return columns

def get_data(filters):
	
	where_clause = filters.user and " and assigned_to = '%s' " % filters.user or ""

	data = frappe.db.sql("""
		SELECT
			iss.assigned_to as "User ID", count(*) as "Total Tickets Worked",
			(SELECT
				count(*)
			FROM
				`tabHR Issue`
			WHERE
				status = 'Closed'
				and assigned_to = iss.assigned_to
				and DATE(resolution_date) between '{from_date}' AND '{to_date}'
				and DATE(due_date) > DATE(resolution_date)) as "Tickets Closed within SLA",
			(SELECT
				count(*)
			FROM
				`tabHR Issue`
			WHERE
				status = 'Closed'
				and assigned_to = iss.assigned_to
				and DATE(resolution_date) between '{from_date}' AND '{to_date}'
				and DATE(due_date) <= DATE(resolution_date)) as "Tickets Violated SLA"
		FROM 
			`tabHR Issue` iss
		WHERE 
			iss.status = 'Closed' 
			and iss.assigned_to != ''
			and DATE(resolution_date) between '{from_date}' AND '{to_date}'
			{where_clause}
		GROUP BY assigned_to """.format(from_date=filters.from_date, to_date=filters.to_date, where_clause=where_clause), as_dict=1)

	for row in data:
		row["User Name"] = get_user_fullname(row["User ID"])
		row["Total % within SLA"] = get_percentage(row)
		row["Total % Violated SLA"] = get_percentage(row, 1)

	data.append({
		"User ID": "Total",
		"Total Tickets Worked": sum(row["Total Tickets Worked"] for row in data),
		"Tickets Closed within SLA": sum(row["Tickets Closed within SLA"] for row in data),
		"Tickets Violated SLA": sum(row["Tickets Violated SLA"] for row in data)})
		
	data[-1].update({
		"Total % within SLA": get_percentage(data[-1]),
		"Total % Violated SLA": get_percentage(data[-1], 1)})

	return data

def get_percentage(row, nt=0):
	
	if nt:
		return round(float(row["Tickets Violated SLA"]) / float(row["Total Tickets Worked"]) * 100.0, 2)
	else:
		return round(float(row["Tickets Closed within SLA"]) / float(row["Total Tickets Worked"]) * 100.0, 2)

