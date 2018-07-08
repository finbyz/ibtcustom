# -*- coding: utf-8 -*-
# Copyright (c) 2018, Finbyz Tech Pvt Ltd and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _, db
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc

class IBTAssetHandover(Document):
	
	# def validate(self):
	# 	self.update_doc_status()

	# def update_doc_status(self):
	# 	if not self.asset_request_ref:
	# 		frappe.throw(_("Please set Asset Request Ref"))
	# 		validated = False
	# 	else:
	# 		frappe.db.set_value("IBT Asset Request", self.asset_request_ref, 'status', self.status)
	# 		frappe.db.set_value("IBT Asset Request", self.asset_request_ref, 'workflow_state', self.status)

	def on_submit(self):
		if self.status == "Acknowledged":
			company_asset = frappe.get_doc("Company Asset",self.asset_number)
			company_asset.handover_date = self.date
			company_asset.in_possession_with = "Employee"
			company_asset.employee = self.employee
			company_asset.employee_name = self.employee_name
			company_asset.save(ignore_permissions=True)
			db.commit()

@frappe.whitelist()
def make_asset_return(source_name, target_doc=None):
	doclist = get_mapped_doc("IBT Asset Handover", source_name, {
			"IBT Asset Handover":{
				"doctype": "IBT Asset Return",
				"field_map": {
					"name": "asset_handover_ref"
				},
				"field_no_map": [
					"status",
					"naming_series"
				]
			}
		}, target_doc)

	return doclist