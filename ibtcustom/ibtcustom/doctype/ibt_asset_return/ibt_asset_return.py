# -*- coding: utf-8 -*-
# Copyright (c) 2018, Finbyz Tech Pvt Ltd and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _, db
from frappe.model.document import Document

class IBTAssetReturn(Document):
	# def validate(self):
	# 	self.update_doc_status()

	# def update_doc_status(self):
	# 	if not self.asset_handover_ref:
	# 		frappe.throw(_("Please set Asset Handover Ref"))
	# 		validated = False
	# 	else:
	# 		ho = frappe.get_doc("IBT Asset Handover", self.asset_handover_ref)
	# 		ho.db_set('status', self.status)
	# 		ho.db_set('workflow_state', self.status)
	# 		frappe.db.set_value("IBT Asset Request", ho.asset_request_ref, 'status', self.status)
	# 		frappe.db.set_value("IBT Asset Request", ho.asset_request_ref, 'workflow_state', self.status)

	def on_submit(self):
		if self.status == "Received":
			company_asset = frappe.get_doc("Company Asset",self.asset_number)
			company_asset.handover_date = ''
			company_asset.in_possession_with = "Company"
			company_asset.employee = ''
			company_asset.employee_name = ''
			company_asset.save(ignore_permissions=True)
			db.commit()