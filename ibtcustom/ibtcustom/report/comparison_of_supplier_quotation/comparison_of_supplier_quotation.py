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
	return [
		_("ID") + ":Link/Supplier Quotation:100",
		_("Material Request") + ":Link/Material Request:100",
		_("Supplier") + ":Link/Supplier:150",
		_("Item Code") + ":Link/Item:120",
		_("Item Name") + ":Data:160",
		_("Quantity") + ":Float:80",
		_("Rate") + ":Currency:100",
		_("Grand Total") + ":Currency:100",
	]

def get_data(filters):

	where_clause = get_conditions(filters)
	
	data = db.sql("""
		SELECT DISTINCT
			sq.name as 'ID', sq.supplier as 'Supplier', sq.grand_total as 'Grand Total'
		FROM
			`tabSupplier Quotation` sq, `tabSupplier Quotation Item` sqi
		WHERE
			sq.docstatus < 2
			and sqi.parent = sq.name
			%s
		ORDER BY
			sq.modified DESC """ % where_clause, as_dict=1)

	d = data[:]
	id = 0

	for row in d:
		id = insert_items(data, row, id+1)

	return data

def insert_items(data, row, id):

	items = db.sql("""
		SELECT
			item_code as "Item Code", material_request as 'Material Request', qty as 'Quantity', item_name as 'Item Name', rate as 'Rate'
		FROM
			`tabSupplier Quotation Item`
		WHERE
			parent = '%s' """ % row['ID'], as_dict=1)

	if items:
		row["Material Request"] = items[0]["Material Request"]
		row["Quantity"] = items[0]["Quantity"]
		row["Item Code"] = items[0]["Item Code"]
		row["Item Name"] = items[0]["Item Name"]
		row["Rate"] = items[0]["Rate"]

	for i in items[1:]:
		data.insert(id, {
			'Material Request': i['Material Request'],
			'Quantity': i["Quantity"],
			'Item Code': i["Item Code"],
			'Item Name': i["Item Name"],
			'Rate': i["Rate"]
		})
		id +=1

	return id

def get_conditions(filters):
	conditions = ''

	if filters.name: conditions += " and sq.name = '%s'" % filters.name.replace("'","/'")
	if filters.supplier: conditions += " and sq.supplier = '%s'" % filters.supplier.replace("'","/'")
	if filters.material_request: conditions += " and sqi.material_request = '%s'" % filters.material_request.replace("'","/'")
	if filters.item_code: conditions += " and sqi.item_code = '%s' " % filters.item_code.replace("'","/'")

	return conditions