# Copyright (c) 2013, Finbyz Tech Pvt Ltd and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
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
		_("MR") + ":Link/Material Request:120",
		_("Customer") + ":Link/Sales Order:180",
		_("SO") + ":Link/Sales Order:120",
		_("Posting Date") + ":Date:120",
		_("First PO Date") + ":Date:100",
		_("Last PO Date") + ":Date:100",
		_("MR SLA") + ":INT:80",
		_("MR Closed") + ":INT:80"
	]
	return columns

def get_data(filters):
	data = frappe.db.sql("""
		SELECT
			mr.name as "MR", mr.customer as "Customer", mr.sales_order as "SO", mr.posting_date as "Posting Date",
			mr.ordered_date as "First PO Date", mr.last_ordered_date as "Last PO Date",
			DATEDIFF(mr.ordered_date, mr.posting_date) as "MR SLA",
			DATEDIFF(mr.last_ordered_date, mr.posting_date) as "MR Closed"
		FROM
			`tabMaterial Request` as mr
		WHERE DATE(mr.posting_date) between '{from_date}' AND '{to_date}'
		""".format(from_date=filters.from_date, to_date=filters.to_date),as_dict=1)
	return data