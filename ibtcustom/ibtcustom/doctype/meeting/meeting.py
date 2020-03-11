# -*- coding: utf-8 -*-
# Copyright (c) 2017, FinByz Tech Pvt Ltd and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import now, global_date_format, format_time, get_datetime
import datetime



class Meeting(Document):
	def before_save(self):
		self.set_invitation()

	def set_invitation(self):
		message = """<p>
					Dear full_name
				</p>
				<p>
					We request you to confirm the invitation of the meeting as described below:
				</p>
				<p>
					<strong>Planned Date: {0}</strong>
				</p>
				<p>
					<strong>Meeting Date: {1}</strong>
				</p>
				<p>
					<strong>From: {2}</strong>
				</p>
				<p>
					<strong>To: {3}</strong>
				</p>
				<p>
					<strong></strong>
				</p>
				<p>
					<strong>Agenda as below:</strong>
				</p>""".format(self.get_formatted('planned_date'), self.get_formatted('date'), frappe.utils.get_datetime(self.from_time).strftime("%H:%M"), frappe.utils.get_datetime(self.to_time).strftime("%H:%M"))

		message += "<ol>"

		for agenda in self.meeting_agenda:
			message += "<li>"+agenda.description+"</li>"

		message += "</ol>"
		
		self.invitation_message = message
		
	def send_minutes(self):
	
		date = frappe.utils.get_datetime(self.date).strftime("%A %d-%b-%Y")
		subject = "{0} - Minutes: {1}".format(self.title, self.get_formatted('date'))
		
		minutes = """<p>
						Dear {0},
					</p>
					<p>
						<strong>Greeting from IBT!</strong>
					</p>
					<p>
						Thank you for sparing time for {1} on {2}.
					</p>
					<p>
						Please have minutes of meeting as below:
					</p>
					<p>
						{3}
					</p>"""
					
		if self.meeting_actionable:
			actionable_heading = """<br><p>
						<strong>Actionable</strong>
						</p>
					
					<table border="1" cellspacing="0" cellpadding="0">
						<tbody>
							<tr>
								<td width="208" valign="top">
									<p>
										<strong>Actionable</strong>
									</p>
								</td>
								<td width="208" valign="top">
									<p>
										<strong>Responsibility</strong>
									</p>
								</td>
								<td width="208" valign="top">
									<p>
										<strong>Expected Completion Date</strong>
									</p>
								</td>
							</tr>"""
			actionable_row = """	<tr>
						<td width="208" valign="top"> {0}
						</td>
						<td width="208" valign="top"> {1}
						</td>
						<td width="208" valign="top"> {2}
						</td>
					</tr>"""
				
			actionable_rows = ""	
			for row in self.meeting_actionable:
				actionable_rows += actionable_row.format(row.actionables, row.responsible, row.get_formatted('expected_completion_date'))
				
			actionable_heading += actionable_rows
			actionable_heading += "</tbody></table>"
			minutes += actionable_heading
		
		for row in self.meeting_company:
			minutes_message = minutes.format(row.full_name, self.title, date, self.minutes)
			
			if row.user_id:
				frappe.sendmail(recipients=[row.user_id],
							sender=frappe.session.user,
							subject=subject, 
							message=minutes_message,
							reference_doctype=self.doctype,
							reference_name=self.name)
							
		for row in self.meeting_customer:
			minutes_message = minutes.format(row.person_name, self.title, date, self.minutes)
			
			if row.email_id:
				frappe.sendmail(recipients=[row.email_id],
							sender=frappe.session.user,
							subject=subject, 
							message=minutes_message,
							reference_doctype=self.doctype,
							reference_name=self.name)
		
		frappe.msgprint("Minutes Sent to All Participants")
		
		self.status = "Completed"
		self.save()
		frappe.db.commit()
		
	def send_invitation(self):
		self.send_internal_invitation()
		self.send_external_invitation()
	
	def send_internal_invitation(self):

		subject = "Invitation: '" + self.title + "' on date: " + self.get_formatted('date')

		for row in self.meeting_company:
			frappe.sendmail(recipients=[row.user_id],
							sender=frappe.session.user,
							subject=subject, 
							message=self.invitation_message,
							reference_doctype=self.doctype,
							reference_name=self.name)
			
		self.status = "Invitation Sent"
		self.save()
		frappe.db.commit()
		frappe.msgprint("Invitation Sent to Company Representatives")
		
	def send_external_invitation(self):

		subject = "Invitation: '" + self.title + "' on date: " + self.get_formatted('date')

		for row in self.meeting_customer:
			frappe.sendmail(recipients=[row.email_id],
						sender=frappe.session.user,
						subject=subject, 
						message=self.invitation_message,
						reference_doctype=self.doctype,
						reference_name=self.name)
		
		self.status = "Invitation Sent"
		self.save()
		frappe.db.commit()
		frappe.msgprint("Invitation Sent to Customer Representatives")