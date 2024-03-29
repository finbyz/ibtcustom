# -*- coding: utf-8 -*-
# Copyright (c) 2020, Finbyz Tech Pvt Ltd and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class RoleRestriction(Document):
	
	def before_save(self):
		for_value = ''
		user_list = frappe.get_list("User",{'enabled': 1, 'name': ['NOT IN', ['administrator','guest']]},ignore_permissions=True)
		for user in user_list:
			user_role_list = frappe.get_roles(user.name)
			if self.role in user_role_list:
				if self.allow == "Employee":
					for_value =  frappe.db.get_value("Employee",{'user_id': user.name}, 'name')
					if not for_value:
						frappe.throw("Create Employee for the user <b>{}</b>".format(user.name))
				if self.allow == "User":
					for_value = user.name
				if not frappe.db.exists("User Permission", {'user': user.name, 'allow': self.allow, 'for_value': for_value or self.for_value, 'is_default': self.is_default, 'applicable_for': self.applicable_for, 'apply_to_all_doctypes': self.apply_to_all_doctypes,"hide_descendants": self.hide_descendants}):
					
					user_perm = frappe.new_doc("User Permission")
					user_perm.user = user.name
					user_perm.allow = self.allow
					user_perm.for_value = for_value or self.for_value
					user_perm.is_default = self.is_default
					user_perm.apply_to_all_doctypes = self.apply_to_all_doctypes
					user_perm.applicable_for = self.applicable_for
					user_perm.hide_descendants = self.hide_descendants
					try:
						user_perm.save(ignore_permissions=True)
					except:
						pass
