# -*- coding: utf-8 -*-
# Copyright (c) 2018, Finbyz Tech Pvt Ltd and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import now
from frappe.utils import nowdate, add_days, getdate, get_time, add_months
from datetime import timedelta, date, datetime, time

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
			
	def before_save(self):
		due_date = getdate(self.opening_date)
		due_days = 2
		default_holiday = frappe.db.get_value("Company",self.company,'default_holiday_list')
		holiday = frappe.get_doc("Holiday List",default_holiday)
		holiday_list =[row.holiday_date for row in holiday.holidays]

		i=0
		
		# if due_date.weekday() == 2:
			# due_date = add_days(due_date, 3)
		
		if due_date in holiday_list:
			due_days += 1
			
		elif due_date.weekday() == 5:
			due_days += 1
			
		opening_time = get_time(self.opening_time)
		
		hour = int(opening_time.strftime('%H'))
		minutes = int(opening_time.strftime('%M'))
		
		if due_date in holiday_list:
			hour = 8
			opening_time = get_time("08:00:00")
		if hour > 17:
			hour = 8 + hour - 17
			closing_time = (datetime.combine(date.today(), opening_time).replace(hour=hour)).time()
			due_days += 1
		else:
			closing_time = (datetime.combine(date.today(), opening_time) + timedelta(hours=5)).time()
		self.db_set('closing_time',str(closing_time))
	
		while i < due_days:
			i+=1
			due_date = add_days(due_date,1)
			if due_date.weekday() == 5:
				due_days += 1

			elif due_date in holiday_list:
				due_days += 1


		self.db_set('due_date', due_date)
