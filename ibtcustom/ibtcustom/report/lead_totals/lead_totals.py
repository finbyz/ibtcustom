# Copyright (c) 2013, FinByz Tech Pvt Ltd and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import getdate, nowdate


def execute(filters=None):
	filters.from_date = getdate(filters.from_date or nowdate())
	filters.to_date = getdate(filters.to_date or nowdate())
	columns, data = [], []
	columns = get_columns()
	data = get_lead_data(filters, "Sales Person")
	return columns, data

def get_columns():
	return [
		_("Sales Person") + ":Link/User:150",
		_("Lead Created") + ":Int:120",
		_("Lead Modified") + ":Int:120",
		_("Interested") + ":Int:100",
		_("Call Back/No Answer") + ":Int:150",
		_("Not Interested") + ":Int:120",
		_("Lead Existing Office") + ":Int:150",
		_("Lead New Office") + ":Int:150"
	]
	
def get_lead_data(filters, based_on):
	based_on_field = frappe.scrub(based_on)
	conditions = get_filter_conditions(filters)
	
	lead_details = frappe.db.sql("""
		select {based_on_field}, name
		from `tabLead` 
		where {based_on_field} is not null and {based_on_field} != '' {conditions} 
	""".format(based_on_field=based_on_field, conditions=conditions), filters, as_dict=1)
	
	lead_map = frappe._dict()
	
	for d in lead_details:
		lead_map.setdefault(d.get(based_on_field), []).append(d.name)
	
	data = []
	for based_on_value, leads in lead_map.items():
		row = {
			based_on: based_on_value,
		}
		row["Lead Created"] = get_creation_date(based_on_value, filters)
		row["Lead Modified"] = get_modified_date(based_on_value, filters)
		row["Interested"] = get_interested_count(based_on_value, filters)
		row["Call Back/No Answer"] = get_callback_count(based_on_value, filters)
		row["Not Interested"] = get_notinterested_count(based_on_value, filters)
		row["Lead Existing Office"] = get_existing_office(based_on_value, filters)
		row["Lead New Office"] = get_new_office(based_on_value, filters)
		data.append(row)
		
	return data	

def get_creation_date(based_on_value, filters):
	conditions = get_filter_conditions(filters)
	dt_s = filters.from_date
	dt_e = filters.to_date
	return frappe.db.sql(""" SELECT COUNT(creation) FROM `tabLead` WHERE sales_person='{b}' {conditions} AND (date(creation) BETWEEN '{st}' AND '{ed}')""".format(st=dt_s, ed=dt_e, b=based_on_value, conditions=conditions), filters)
		
def get_modified_date(based_on_value, filters):
	conditions = get_filter_conditions(filters)
	return frappe.db.sql(""" SELECT COUNT(modified) FROM `tabLead` WHERE sales_person='{b}' {conditions}""".format(b=based_on_value, conditions=conditions), filters)

def get_interested_count(based_on_value, filters):
	conditions = get_filter_conditions(filters)
	return frappe.db.sql("""select count(status) from `tabLead` WHERE status="Interested" AND sales_person='{b}' {conditions}""".format(b=based_on_value, conditions=conditions), filters)
	
def get_callback_count(based_on_value, filters):
	conditions = get_filter_conditions(filters)
	return frappe.db.sql("""select count(status) from `tabLead` WHERE (status="Call Back" OR status="No Answer") AND sales_person='{b}' {conditions}""".format(b=based_on_value, conditions=conditions), filters)
	
def get_notinterested_count(based_on_value, filters):
	conditions = get_filter_conditions(filters)
	return frappe.db.sql("""select count(status) from `tabLead` WHERE status="Not Interested" AND sales_person='{b}' {conditions}""".format(b=based_on_value, conditions=conditions), filters)
	
def get_existing_office(based_on_value, filters):
	conditions = get_filter_conditions(filters)
	return frappe.db.sql("""select count(status) from `tabLead` WHERE lead_type="Existing Office" AND sales_person='{b}' {conditions}""".format(b=based_on_value, conditions=conditions), filters)
	
def get_new_office(based_on_value, filters):
	conditions = get_filter_conditions(filters)
	return frappe.db.sql("""select count(status) from `tabLead` WHERE lead_type="New Office" AND sales_person='{b}' {conditions}""".format(b=based_on_value, conditions=conditions), filters)

def get_filter_conditions(filters):
	conditions=""
	if filters.from_date:
		conditions += " and date(modified) >= %(from_date)s"
	if filters.to_date:
		conditions += " and date(modified) <= %(to_date)s"
	
	return conditions
	