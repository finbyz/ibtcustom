# -*- coding: utf-8 -*-
# Copyright (c) 2018, Finbyz Tech Pvt Ltd and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import now


sender_field = "raised_by"

class HRIssue(Document):
	def validate(self):
		if not self.raised_by:
			self.raised_by = frappe.session.user
		self.update_status()
	
	def update_status(self):
		status = frappe.db.get_value("HR Issue", self.name, "status")
		if self.status=="Closed" and status !="Closed":
			self.resolution_date = now()
		if self.status=="Open" and status !="Open":
			# if no date, it should be set as None and not a blank string "", as per mysql strict config
			self.resolution_date = None