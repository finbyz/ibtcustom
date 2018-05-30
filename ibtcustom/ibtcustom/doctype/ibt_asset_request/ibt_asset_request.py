# -*- coding: utf-8 -*-
# Copyright (c) 2018, Finbyz Tech Pvt Ltd and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc


class IBTAssetRequest(Document):
	pass

@frappe.whitelist()
def make_asset_handover(source_name, target_doc=None):
	doclist = get_mapped_doc("IBT Asset Request", source_name, {
			"IBT Asset Request":{
				"doctype": "IBT Asset Handover",
				"field_map": {
					"name": "asset_request_ref"
				},
				"field_no_map": [
					"status",
					"naming_series"
				]
			}
		}, target_doc)

	return doclist