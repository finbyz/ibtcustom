# Copyright (c) 2013, Finbyz Tech Pvt Ltd and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _, db

def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	columns = [
		_("Customer") + ":Link/Customer:180",
		_("SO Number") + ":Link/Sales Order:100",
		_("Start Date") + ":Date:80",
		_("End Date") + ":Date:80",
		_("Total Invoices to be made") + ":Int:150",
		_("Actual Invoices made") + ":Int:120",
		_("Invoice Nos") + "::100",
		_("Pending Invoices to be made") + ":Int:150",
		_("Subscription No") + "::110",
		_("Next Invoice Date") + ":Date:110"
	]

	return columns

def get_data(filters):
	
	condition = filters.customer and " and so.customer = '%s' " % filters.customer or ""

	data = db.sql("""
		SELECT
			so.customer as "Customer", so.name as "SO Number", so.contract_start_date as "Start Date", so.contract_end_date as "End Date", 
			(SELECT
				count(*)
			FROM
				`tabPayment Schedule`
			WHERE
				parent = so.name
			) as "Total Invoices to be made",
			
			(SELECT
				count(*)
			FROM
				`tabSales Invoice`
			WHERE
				docstatus < 2
				and status not in ('Return', 'Credit Note Issued')
				and sales_order = so.name
			) as "Actual Invoices made"
		FROM
			`tabSales Order` so
		WHERE
			so.docstatus < 2
			and so.status not in ('Completed', 'Closed')
			{condition}
		ORDER BY
			so.customer """.format(condition= condition), as_dict=1)

	for row in data:
		set_invoice_details(row)
		row["Pending Invoices to be made"] = int(row["Total Invoices to be made"]) - int(row["Actual Invoices made"])

	return data

def set_invoice_details(row):
	
	data = db.sql("""
		SELECT
			si.name as "Invoice", sub.name as "Subscription", sub.next_schedule_date as "Next Date"
		FROM
			`tabSales Invoice` si left join tabSubscription sub on sub.reference_document = si.name
		WHERE
			si.docstatus < 2
			and si.status not in ('Return', 'Credit Note Issued')
			and si.sales_order = %s """, row["SO Number"], as_dict=1)

	row.update({
		"Invoice Nos": ','.join([row["Invoice"] for row in data]),
		"Subscription No": ','.join([row["Subscription"] for row in data if row["Subscription"] != None]),
		"Next Invoice Date": ','.join([str(row["Next Date"]) for row in data if row["Subscription"] != None])
	})