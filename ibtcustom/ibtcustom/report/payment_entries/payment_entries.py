# Copyright (c) 2013, FinByz Tech Pvt Ltd and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import getdate, nowdate


def execute(filters=None):
	filters.date = getdate(filters.date or nowdate())
	columns, data = [], []
	columns = get_columns()
	data = get_payments(filters)	
	return columns, data

	
def get_columns():
	return [_("Payment") + ":Link/Payment Entry:100",_("Payment Type") + "::100",_("Date")+ ":Date:90",_("Party Type") + "::100",_("Party") + ":Party:200",_("Paid Amt")  + ":Currency:100",
		_("Recd Amount") + ":Currency:100"]

		
		
def get_payments(filters):
	cond = "1=1"
	if filters.get("date"):
		cond = "py.posting_date = %(date)s"

	rec_entries = frappe.db.sql(""" 
		select
			py.name, py.payment_type, py.posting_date, py.party_type, py.party, "0" , py.received_amount
		from 
			`tabPayment Entry` py
		where
			py.payment_type="Receive" and py.docstatus = 1 and {cond}
		order by
			py.name DESC
	""".format(cond=cond), filters, as_list=1)
	
	pay_entries = frappe.db.sql(""" 
		select
			py.name, py.payment_type, py.posting_date, py.party_type, py.party, py.paid_amount , "0"
		from 
			`tabPayment Entry` py
		where
			py.payment_type="Pay" and py.docstatus = 1 and {cond}
		order by
			py.name DESC			
	""".format(cond=cond), filters, as_list=1)
	
	return (rec_entries + pay_entries)