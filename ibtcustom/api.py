# -*- coding: utf-8 -*-
import frappe
from frappe import _, sendmail, db
from frappe.utils import nowdate, add_days, getdate, get_time, add_months
from frappe.core.doctype.communication.email import make
from frappe.utils.background_jobs import enqueue
from email.utils import formataddr
from datetime import timedelta, date, datetime, time
from frappe.email.doctype.auto_email_report.auto_email_report import AutoEmailReport
from frappe.model.mapper import get_mapped_doc
from frappe.utils import (flt, now, nowtime, get_time, today, get_datetime, add_days)
from frappe.core.doctype.communication.email import make


@frappe.whitelist()
def override_validate(self, method):
	AutoEmailReport.validate = validate

def validate(self):
	self.validate_emails()
	self.validate_report_format()
	
@frappe.whitelist()
def so_on_submit(self, method):
	update_did(self, method)
	update_op_status(self, method)

@frappe.whitelist()
def po_on_submit(self, method):
	update_order_date(self, method)

@frappe.whitelist()
def po_on_cancel(self, method):
	update_order_date(self, method)

@frappe.whitelist()
def so_on_cancel(self, method):
	cancel_did(self, method)
	cancel_op_status(self, method)
	
@frappe.whitelist()
def qt_on_submit(self, method):
	submit_op(self, method)
	
@frappe.whitelist()
def qt_on_cancel(self, method):
	cancel_op(self, method)
	
@frappe.whitelist()
def qt_on_update(self, method):
	if self.docstatus == 1 and self.opportunity:
		update_op_lead_status(self)

@frappe.whitelist()
def update_lead_owner(self,method):
	if self.contact_by and self.lead_owner != self.contact_by:
		self.lead_owner = self.contact_by
		self.save(ignore_permissions=True)
		frappe.db.commit()

def update_order_date(self, method):
	if self.get('items'):
		if self.items[0].get('material_request'):
			mr = frappe.get_doc("Material Request", self.items[0].material_request)
			
			if method == 'on_submit':
				mr.last_ordered_date = self.transaction_date
				if not mr.ordered_date:
					mr.ordered_date = self.transaction_date

			mr.save(ignore_permissions=True)
			frappe.db.commit()
			
@frappe.whitelist()
def po_cancel(docname):
	so = frappe.get_doc("Purchase Order",docname)
	if so.get('items'):
		if so.items[0].get('material_request'):
			mr = frappe.get_doc("Material Request", so.items[0].material_request)
			
	data = frappe.db.sql("""
					select 
						DATE(po.transaction_date)
					from 
						`tabPurchase Order` as po join `tabPurchase Order Item` as poi on( po.name = poi.parent)
					where 
						poi.material_request = '%s' and po.docstatus = 1
					order by
						po.modified desc
				"""% mr.name)
	
	if not data:
		mr.ordered_date = ''
		mr.last_ordered_date = ''
	else:
		mr.last_ordered_date = data[0][0]
	mr.save(ignore_permissions=True)
	frappe.db.commit()

def update_op_lead_status(self):
	opp = frappe.get_doc("Opportunity", self.opportunity)
	opp.db_set("status", "Lost")

	db.set_value("Opportunity", self.opportunity, 'status', "Lost")

	if self.quotation_to == "Lead":
		db.set_value("Lead", self.lead, 'status', "Lost Quotation")

def update_op_status(self, method):
	for row in self.items:
		if row.prevdoc_docname:
			quot = frappe.get_doc("Quotation", row.prevdoc_docname)
			if quot.opportunity and quot.docstatus < 2:
				opp = frappe.get_doc("Opportunity", quot.opportunity)
				opp.status = 'Converted'
				opp.save(ignore_permissions=True)
				frappe.db.commit()
				
def cancel_op_status(self, method):
	for row in self.items:
		if row.prevdoc_docname:
			quot = frappe.get_doc("Quotation", row.prevdoc_docname)
			if quot.opportunity and quot.docstatus < 2:
				opp = frappe.get_doc("Opportunity", quot.opportunity)
				opp.status = 'Quotation'
				opp.save(ignore_permissions=True)
				frappe.db.commit()
				
def update_did(self, method):
	for row in self.call_routing:
		target_doc = frappe.get_doc("IBT DID Numbers", row.did_no)
		target_doc.customer = self.customer
		target_doc.call_center_no = row.call_center_number
		target_doc.sales_order = self.name
		target_doc.in_use = 1
		target_doc.save(ignore_permissions=True)
		frappe.db.commit()
		
def cancel_did(self, method):	
	for row in self.call_routing:
		target_doc = frappe.get_doc("IBT DID Numbers", row.did_no)
		target_doc.customer = ""
		target_doc.call_center_no = ""
		target_doc.sales_order = ""
		target_doc.in_use = 0
		target_doc.save(ignore_permissions=True)
		frappe.db.commit()
		
def submit_op(self, method):
	if self.opportunity:
		op = frappe.get_doc("Opportunity", self.opportunity)
		grand_total = op.grand_total + self.grand_total
		op.db_set('grand_total', grand_total)
		
def cancel_op(self, method):
	if self.opportunity:
		op = frappe.get_doc("Opportunity", self.opportunity)
		grand_total = op.grand_total - self.grand_total
		op.db_set('grand_total', grand_total)
		if grand_total == 0.0:
			op.db_set('status', "Open")

def project_validate(self,method):
	sync_tasks(self)
	# self.project_tasks = []
	load_tasks(self)

def project_onload(self,method):
	pass
	# if not self.get('__unsaved') and not self.get("project_tasks"):
	# 	load_tasks(self)
	
def project_on_update(self,method):
	delete_task(self)
	# load_tasks(self)
	pass

@frappe.whitelist()
def project_before_save(self, method):
	set_progress(self)

def set_progress(self):
	if self.project_tasks:
		for row in self.project_tasks:
			if row.status == "Closed":
				frappe.db.set_value("Task", row.task_id, 'progress', 100.0)
			elif row.status == "Open":
				frappe.db.set_value("Task", row.task_id, 'progress', 0.0)

		self.run_method('update_percent_complete')

def delete_task(self):
	if not self.get('deleted_task_list'): return

	for d in self.get('deleted_task_list'):
		# unlink project
		frappe.db.set_value('Task', d, 'project', '')

	self.deleted_task_list = []

def load_tasks(self):
	"""Load `tasks` from the database"""
	project_task_custom_fields = frappe.get_all("Custom Field", {"dt": "Project Task"}, "fieldname")

	# self.project_tasks = []
	item_task = [project.task_id for project in self.project_tasks]
	for task in get_tasks(self):
		if task.name not in item_task:
			task_map = {
				"title": task.subject,
				"status": task.status,
				"start_date": task.exp_start_date,
				"end_date": task.exp_end_date,
				"description": task.description,
				"task_id": task.name,
			}
			map_custom_fields(self,task, task_map, project_task_custom_fields)

			self.append("project_tasks", task_map)

def is_row_updated(self, row, existing_task_data):
	if self.get("__islocal") or not existing_task_data: return True

	d = existing_task_data.get(row.task_id)

	if (d and (row.title != d.title or row.status != d.status
		or getdate(row.start_date) != getdate(d.start_date) or getdate(row.end_date) != getdate(d.end_date)
		or row.description != d.description )):
		return True

def sync_tasks(self):
	"""sync tasks and remove table"""
	if not hasattr(self, "deleted_task_list"):
		self.set("deleted_task_list", [])

	if self.flags.dont_sync_tasks: return
	task_names = []

	existing_task_data = {}

	fields = ["title", "status", "start_date", "end_date", "description", "assigned_to", "task_id"]
	# exclude_fieldtype = ["Button", "Column Break",
	# 	"Section Break", "Table", "Read Only", "Attach", "Attach Image", "Color", "Geolocation", "HTML", "Image"]

	custom_fields = frappe.get_all("Custom Field", {"dt": "Project Task"}, "fieldname")

	for d in custom_fields:
		fields.append(d.fieldname)

	for d in frappe.get_all('Project Task',
		fields = fields,
		filters = {'parent': self.name}):
		existing_task_data.setdefault(d.task_id, d)

	for t in self.project_tasks:
		if t.task_id:
			task = frappe.get_doc("Task", t.task_id)
			if not t.assigned_to:
				t.assigned_to = task.assigned_to
		else:
			task = frappe.new_doc("Task")
			task.project = self.name

		if not t.task_id or is_row_updated(self, t, existing_task_data):
			if not t.assigned_to:
				t.assigned_to = task.assigned_to
			task.update({
				"subject": t.title,
				"status": t.status,
				"exp_start_date": t.start_date,
				"exp_end_date": t.end_date,
				"description": t.description,
				"assigned_to": t.assigned_to
			})

			map_custom_fields(self, t, task, custom_fields)

			task.flags.ignore_links = True
			task.flags.from_project = True
			task.flags.ignore_feed = True

			if t.task_id:
				task.update({
					"modified_by": frappe.session.user,
					"modified": now()
				})

				task.run_method("validate")
				task.db_update()
				task.notify_update()
			else:
				task.save(ignore_permissions = True)
				t.task_id = task.name
				t.assigned_to = task.assigned_to
			task_names.append(task.name)
		else:
			task_names.append(task.name)
		

	# delete
	# for t in frappe.get_all("Task", ["name"], {"project": self.name, "name": ("not in", task_names)}):
	# 	self.deleted_task_list.append(t.name)

def map_custom_fields(self, source, target, custom_fields):
	for field in custom_fields:
		target.update({
			field.fieldname: source.get(field.fieldname)
		})

def get_tasks(self):
	if self.name is None:
		return {}
	else:
		return frappe.get_all("Task", "*", {"project": self.name}, order_by="exp_start_date asc, status asc")

@frappe.whitelist()
def remove_project_reference(task_name):
	frappe.db.set_value("Task", task_name, "project", '')

@frappe.whitelist()
def sales_invoice_mails():
	enqueue(send_sales_invoice_mails, queue='long', timeout=2000)
	return "Sales Invoice Mails Send"

@frappe.whitelist()
def send_sales_invoice_mails():
	def header(contact_list, customer):
		return """Hello """ + '/'.join(contact_list) + """ / Team """ + customer + """,<br><br>
		Thank you for choosing IBT as your Technology &amp; BPO Partner.<br>
		Below invoice/s for """ + customer + """ is/are showing pending as per our records, request you to process payment of outstanding amount
		at earliest.<br>
		<div align="center">
			<table border="1" cellspacing="0" cellpadding="0" width="100%">
				<thead>
					<tr>
						<th width="18%" valign="top">Invoice</th>
						<th width="12%" valign="top">Due Date</th>
						<th width="37%" valign="top">Customer</th>
						<th width="13%" valign="top">Invoice Amt</th>
						<th width="18%" valign="top">Outstanding Amt</th>
					</tr></thead><tbody>"""

	def table_content(name, posting_date, due_date, customer, rounded_total, outstanding_amount):
		'''bgcolor = ''
		today = getdate()
		d_date = getdate(due_date)

		if today > d_date:
			bgcolor = 'BC0006' # Dark Red
		elif add_days(posting_date, 21) <= today < d_date:
			bgcolor = 'FF5456' # Light Red
		elif add_days(posting_date, 14) <= today < add_days(posting_date, 21):
			bgcolor = 'FFBF00' # Amber (Orange)
		elif today < add_days(posting_date, 14):
			bgcolor = '0EA33B' # Dark Green

		 bgcolor='#""" + bgcolor + """' style='color:white in outstanding amount'''

		return """<tr>
				<td width="18%" valign="top"> {0} </td>
				<td width="12%" valign="top"> {1} </td>
				<td width="37%" valign="top"> {2} </td>
				<td width="13%" valign="top"> {3} </td>
				<td width="18%" valign="top"> {4} </td>
			</tr>""".format(name, due_date, customer, rounded_total, outstanding_amount)
	
	def footer(outstanding_amount, currency):
		return """<tr>
					<td width="68%" colspan="3" valign="top">
						<p align="center">
							<strong>Total Outstanding</strong>
						</p>
					</td>
					<td width="13%" valign="top">
						<p align="right">
							<strong></strong>
						</p>
					</td>
					<td width="18%" valign="top">
						<p align="right">
							<strong> """ + currency +""" {:,.2f} </strong>
						</p>
					</td>
				</tr>
				</tbody>
				</table>
				</div>
				<br>
				If you need any clarifications for any of above invoices, 
				please reach out to our Accounts Receivables Team by sending email to 
				accounts.receivables@ibtevolve.com or +97145548666""".format(sum(outstanding_amount))

	data = db.sql("""
		SELECT 
			name, customer
		FROM
			`tabSales Invoice`
		WHERE
			status in ('Unpaid', 'Overdue')
			and dont_send_email = 0 
		ORDER BY
			due_date """, as_dict=1)

	customers = list(set(map(lambda d: d.customer, data)))
	
	for customer in customers:
		attachments, outstanding, recipients, contact_list = [], [], [], []
		currency = ''
		table = ''

		for row in data:
			if row.customer == customer:
				si = frappe.get_doc("Sales Invoice", row.name)
				attachments.append(frappe.attach_print('Sales Invoice', si.name, print_format="Invoice Format - IBT", print_letterhead=True))
				table += table_content(
							si.name,
							si.posting_date,
							si.get_formatted("due_date"),
							si.customer,
							si.get_formatted("rounded_total"),
							si.get_formatted("outstanding_amount"))

				currency = si.currency
				outstanding.append(si.outstanding_amount)
	
				if si.notification_mail and si.notification_mail not in recipients:
					recipients.append(si.notification_mail)

				if not si.notification_mail:
					if si.contact_email not in recipients:
						recipients.append(si.contact_email)

				if si.contact_display not in contact_list:
					contact_list.append(si.contact_display)

		message = header(contact_list, customer) + '' + table + '' + footer(outstanding, currency)

		sendmail(recipients=recipients,
			cc = ['accounts.receivables@ibtevolve.com'],
			subject='Open Invoices: ' + customer,
			message= message,
			attachments = attachments)

@frappe.whitelist()
def employee_birthday_mails():
	enqueue(send_employee_birthday_mails, queue='long', timeout=2000)

def send_employee_birthday_mails():
	data = db.sql("""
		SELECT
			employee_name, company_email
		FROM
			`tabEmployee`
		WHERE
			status = 'Active' 
			and DATE_FORMAT(date_of_birth,'%m-%d') = DATE_FORMAT(CURDATE(),'%m-%d') """, as_dict=1)

	for row in data:
		recipients = [row.company_email]
		message = """<p>
				Dear {0},
			</p>
			<img src='/files/Birthday-Wishing-File-IBT.JPG'>""".format(row.employee_name)

		sendmail(recipients = recipients,
				cc = ['team@ibtevolve.com'],
				subject = 'Happy Birthday ' + row.employee_name,
				message = message)

# anniversary mails
@frappe.whitelist()
def employee_anniversary_mails():
	enqueue(send_employee_anniversary_mails, queue='long', timeout=2000)

@frappe.whitelist()
def send_employee_anniversary_mails():
	data = db.sql("""
		SELECT
			employee_name, company_email, DATE_FORMAT(CURDATE(),'%y') - DATE_FORMAT(date_of_joining,'%y') as diff 
		FROM
			`tabEmployee`
		WHERE
			status = 'Active' 
			and DATE_FORMAT(date_of_joining,'%m-%d') = DATE_FORMAT(CURDATE(),'%m-%d') """, as_dict=1)

	message = """<p>Dear {},</p>
				<p>Congratutions on completing {} years with IBT.</p>
				<img src='/files/Work-aniversary1000X1000_NEW.jpg' height='40%' width='70%'>
				"""
	for row in data:
		recipients = [row.company_email]
		sendmail(recipients = recipients,
				cc = ['team@ibtevolve.com'],
				subject = 'Happy Work Anniversary - ' + row.employee_name,
				message = message.format(row.employee_name, int(row.diff)))

@frappe.whitelist()
def daily_task_report():
	enqueue(send_task_report_mail, queue='long', timeout=2000)
	return "Daily Task report enqueued"

def send_task_report_mail():

	def get_task_table_heading():
		return """<h3 align='center'>Tasks</h3><br>
			<div align="center">
			<table border="1" cellspacing="0" cellpadding="0" width="100%">
			<thead>
			<tr>
			<th width="30%" valign="top">Subject</th>
			<th width="34%" valign="top"> Project </th>
			<th width="10%" valign="top"> Exp. Start Date </th>
			<th width="10%" valign="top"> Exp. End Date </th>
			<th width="13%" valign="top"> Status </th>
			</tr></thead><tbody>"""

	def get_task_table_data(subject, project, status, exp_start_date, exp_end_date):
		exp_start_date = exp_start_date.strftime("%d-%m-%Y") if exp_start_date is not None else '-'	
		exp_end_date = exp_end_date.strftime("%d-%m-%Y") if exp_end_date is not None else '-'

		return """<tr>
				<td width="30%" valign="top">""" + subject + """ </td>
				<td width="34%" valign="top">""" + project + """ </td>
				<td width="10%" valign="top">""" + exp_start_date + """ </td>
				<td width="10%" valign="top">""" + exp_end_date + """ </td>
				<td width="13%" valign="top">""" + status + """ </td>
				</tr>"""

	def get_todo_table_heading():
		return """<h3 align='center'>ToDo</h3><br>
				<div align="center">
				<table border="1" cellspacing="0" cellpadding="0" width="100%">
				<thead>
				<tr>
				<th width="25%" valign="top"> Task Name </th>
				<th width="25%" valign="top"> Due Date </th>
				<th width="25%" valign="top"> Status </th>
				<th width="25%" valign="top"> Owner </th>
				</tr></thead><tbody>"""
	
	def get_todo_table_data(task_name, due_date, status, assign_to):
		due_date = due_date.strftime("%d-%m-%Y") if due_date is not None else '-'
		task_name = task_name or '-'
		status = status or '-'
		assign_to = assign_to or '-'
		return """<tr>
				<td width="25%" valign="top"> """ + task_name + """ </td>
				<td width="25%" valign="top"> """ + due_date + """ </td>
				<td width="25%" valign="top"> """ + status + """ </td>
				<td width="25%" valign="top"> """ + assign_to + """ </td>
				</tr>"""

	def get_opp_lead_heading(heading, name):
		return """<h3 align='center'>""" + heading + """</h3><br>
				<div align="center">
				<table border="1" cellspacing="0" cellpadding="0" width="100%">
				<thead>
				<tr>
				<th width="22%" valign="top"> """ + name + """ </th>
				<th width="17%" valign="top"> Contact Person </th>
				<th width="18%" valign="top"> Next Contact By </th>
				<th width="16%" valign="top"> Next Contact Date </th>
				<th width="16%" valign="top"> Contact No </th>
				<th width="9%" valign="top"> Status </th>
				</tr></thead><tbody>"""

	def get_opp_lead_table_data(name, contact_person, contact_by, contact_date, contact_no, status):
		contact_date = contact_date.strftime("%d-%m-%Y") if contact_date is not None else '-'
		name = name or '-'
		contact_person = contact_person or '-'
		contact_by = contact_by or '-'
		contact_no = contact_no or '-'
		status = status or '-'
		return """<tr>
				<td width="22%" valign="top"> """ + name + """ </td>
				<td width="17%" valign="top"> """ + contact_person + """ </td>
				<td width="18%" valign="top"> """ + contact_by + """ </td>
				<td width="16%" valign="top"> """ + contact_date + """ </td>
				<td width="16%" valign="top"> """ + contact_no + """ </td>
				<td width="9%" valign="top"> """ + status + """ </td>
				</tr>"""

	def get_quotation_heading():
		return """<h3 align='center'> Quotation </h3><br>
				<div align="center"><table border="1" cellspacing="0" cellpadding="0" width="100%">
				<thead><tr>
				<th width="20%" valign="top"> Customer Name</th>
				<th width="20%" valign="top"> Creation Date</th>
				<th width="20%" valign="top"> Contact</th>
				<th width="20%" valign="top"> Mobile No</th>
				<th width="20%" valign="top"> Created By</th>
				</tr></thead><tbody>"""

	def get_quotation_data(customer_name, transaction_date, contact, mobile_no, created_by):
		transaction_date = transaction_date.strftime("%d-%m-%Y") if transaction_date is not None else '-'

		return """<tr>
				<td width="20%" valign="top"> """ + customer_name + """</td>
				<td width="20%" valign="top"> """ + transaction_date + """</td>
				<td width="20%" valign="top"> """ + contact + """</td>
				<td width="20%" valign="top"> """ + mobile_no + """</td>
				<td width="20%" valign="top"> """ + created_by + """</td>
				</tr>"""

	def get_issue_heading():
		return """<h3 align='center'> Issue </h3><br>
				<div align="center"><table border="1" cellspacing="0" cellpadding="0" width="100%">
				<thead><tr>
				<th width="23%" valign="top"> Subject</th>
				<th width="23%" valign="top"> Customer</th>
				<th width="19%" valign="top"> Engineer Name</th>
				<th width="17%" valign="top"> Opening Date</th>
				<th width="17%" valign="top"> Due Date</th>
				</tr></thead><tbody>"""

	def get_issue_data(subject, customer, engineer, opening_date, due_date):
		opening_date = opening_date.strftime("%d-%m-%Y") if opening_date is not None else '-'
		due_date = due_date.strftime("%d-%m-%Y") if due_date is not None else '-'

		return """<tr>
				<td width="23%" valign="top"> """ + subject + """</td>
				<td width="23%" valign="top"> """ + customer + """</td>
				<td width="19%" valign="top"> """ + engineer + """</td>
				<td width="17%" valign="top"> """ + opening_date + """</td>
				<td width="17%" valign="top"> """ + due_date + """</td>
				</tr>"""

	task_data = db.sql("""
		SELECT 
			subject, project, status, exp_start_date, exp_end_date, assigned_to
		FROM
			`tabTask`
		WHERE
			status in ('Open', 'Overdue')
			and exp_end_date <= CURDATE()
			and assigned_to != ''
		ORDER BY
			assigned_to, exp_end_date """, as_dict=1)

	todo_data = db.sql("""
		SELECT
			task_name, status, date, owner, assign_to
		FROM
			`tabToDo`
		WHERE
			date <= CURDATE()
			and status = 'Open'
			and task_name != ''
		ORDER BY
			owner, date """, as_dict=1)

	lead_data = db.sql("""
		SELECT
			company_name, lead_name, contact_by, contact_date, phone, mobile_no, status
		FROM
			`tabLead`
		WHERE
			DATE(contact_date) <= CURDATE()
			and contact_by != ''
			and status in ('Lead', 'Open', 'Get Details', 'Call Back', 'On Hold')
		ORDER BY
			lead_name, contact_date """, as_dict=1)

	opportunity_data = db.sql("""
		SELECT
			customer_name, contact_by, contact_date, contact_by_name, status, contact_mobile
		FROM
			`tabOpportunity`
		WHERE
			DATE(contact_date) <= CURDATE()
			and contact_by != ''
			and status in ('Open', 'Replied')
		ORDER BY
			customer_name, contact_date """, as_dict=1)

	quotation_data = db.sql("""
		SELECT
			customer_name, transaction_date, contact_display, contact_mobile, owner
		FROM
			`tabQuotation`
		WHERE
			docstatus < 2
			and status = 'Open' """, as_dict=1)

	issue_data = db.sql("""
		SELECT
			subject, customer, engineer_group, assigned_to, opening_date, due_date
		FROM
			`tabIssue`
		WHERE
			status = 'Open' """, as_dict=1)

	task_user = [d.assigned_to for d in task_data]
	todo_user = [d.owner for d in todo_data]
	lead_user = [d.contact_by for d in lead_data]
	opportunity_user = [d.contact_by for d in opportunity_data]
	quotation_user = [d.owner for d in quotation_data]
	issue_user = [d.assigned_to for d in issue_data]

	user_list = list(set(task_user + todo_user + lead_user + opportunity_user + quotation_user + issue_user))

	for user in user_list:
		if not db.exists({'doctype': 'Employee', 'company_email': user}):
			continue

		recipients_list = [user]
		employee_name, manager = db.get_value("Employee", {'company_email': user}, ['employee_name','reports_to'])

		if getdate().weekday() == 5:
			if db.exists('Employee', {'name': manager, 'status': ('!=', 'Left')}):
				recipients_list.append(db.get_value("Employee", manager, 'company_email'))
			else:
				recipients_list.append('operations.manager@ibtevolve.com')

		message = ''

		task_details = ''
		for row in task_data:
			if row.assigned_to == user:
				task_details += get_task_table_data(row.subject, row.project, row.status, row.exp_start_date, row.exp_end_date) or ''

		if task_details:
			message += get_task_table_heading() + task_details + "</tbody></table></div>"

		todo_details = ''
		for row in todo_data:
			if row.owner == user:
				todo_details += get_todo_table_data(row.task_name, row.date, row.status, row.assign_to) or ''

		if todo_details:
			message += get_todo_table_heading() + todo_details + "</tbody></table></div>"

		lead_details = ''
		for row in lead_data:
			if row.contact_by == user:
				contact = []
				if row.mobile_no is not None:
					contact.append(row.mobile_no)
				if row.phone is not None:
					contact.append(row.phone)

				lead_details += get_opp_lead_table_data(row.company_name, row.lead_name, row.contact_by, row.contact_date, '<br>'.join(contact), row.status) or ''

		if lead_details:
			message += get_opp_lead_heading('Lead','Organization Name') + lead_details + "</tbody></table></div>"

		opp_details = ''
		for row in opportunity_data:
			if row.contact_by == user:
				opp_details += get_opp_lead_table_data(row.customer_name, row.contact_by_name, row.contact_by, row.contact_date, row.contact_mobile, row.status) or ''

		if opp_details:
			message += get_opp_lead_heading('Opportunity', 'Customer / Lead Name') + opp_details + "</tbody></table></div>"

		qtn_details = ''
		for row in quotation_data:
			if row.owner == user:
				qtn_details += get_quotation_data(row.customer_name, row.transaction_date, row.contact_display, row.contact_mobile, row.owner) or ''

		if qtn_details:
			message += get_quotation_heading() + qtn_details + "</tbody></table></div>"

		issue_details = ''
		for row in issue_data:
			if row.assigned_to == user:
				issue_details += get_issue_data(row.subject, row.customer, row.engineer_group, row.opening_date, row.due_date) or ''
 
		if issue_details:
			message += get_issue_heading() + issue_details + "</tbody></table></div>"
		
		make(recipients = recipients_list,
				send_email=True,
				subject = 'Daily Report: ' + employee_name,
				content = message)
		# sendmail(recipients = recipients_list,
		# 		subject = 'Daily Report: ' + employee_name,
		# 		message = message)

@frappe.whitelist()
def weekly_reports():
	enqueue(weekly_task_reports, queue='long', timeout=2000, project_type='IT Infrastructure')
	enqueue(weekly_task_reports, queue='long', timeout=2000, project_type='BPO')
	enqueue(weekly_task_reports, queue='long', timeout=2000, project_type='IT Outsourcing')

def weekly_task_reports(project_type=None):
	from frappe.utils.user import get_user_fullname

	where_clause = {
		'BPO': "and project IN (SELECT name from `tabProject` where project_type = 'Call Center Outsourcing')",
		'IT Outsourcing': "and project IN (SELECT name from `tabProject` where project_type IN ('IT Outsourcing, Part-Time Enterprise Plus', 'IT Outsourcing, Part-Time Enterprise', 'IT Outsourcing, Part-Time Standard', 'IT Outsourcing, Full-Time', 'Cloud Computing'))",
		'IT Infrastructure': "and project IN (SELECT name from `tabProject` where project_type = 'IT Infrastructure')"
		}.get(project_type)

	data = db.sql("""
		SELECT 
			subject, project, status, progress, exp_start_date, exp_end_date, assigned_to
		FROM
			`tabTask`
		WHERE
			(status = 'Open' or status = 'Overdue')
			and exp_end_date <= CURDATE() 
			{0}
		ORDER BY
			assigned_to, exp_end_date """.format(where_clause), as_dict=1)

	message = """<div align="center">
				<table border="1" cellspacing="0" cellpadding="0" width="100%">
				<thead>
				<tr>
				<th width="13%" valign="top"> Subject</th>
				<th width="19%" valign="top"> Project</th>
				<th width="17%" valign="top"> Exp. Start Date</th>
				<th width="17%" valign="top"> Exp. End Date</th>
				<th width="8%" valign="top"> Status</th>
				<th width="11%" valign="top"> Progress (%)</th>
				<th width="12%" valign="top"> Assigned To</th>
				</tr></thead><tbody>"""

	for row in data:
		assigned_to = get_user_fullname(row.assigned_to)\
			if row.assigned_to is not None else '-'

		exp_start_date = row.exp_start_date.strftime("%d-%m-%Y")\
			if row.exp_start_date is not None else '-'	
		
		exp_end_date = row.exp_end_date.strftime("%d-%m-%Y")\
			if row.exp_end_date is not None else '-'

		message += """<tr>
					<td width="13%" valign="top"> """ + row.subject + """</td>
					<td width="19%" valign="top"> """ + row.project + """</td>
					<td width="17%" valign="top"> """ + exp_start_date + """</td>
					<td width="17%" valign="top"> """ + exp_end_date + """</td>
					<td width="8%" valign="top">  """ + row.status + """</td>
					<td width="11%" valign="top"> """ + str(row.progress) + """</td>
					<td width="12%" valign="top"> """ + assigned_to + """</td>
				</tr>"""

	message += "</tbody></table></div>"
	
	recipients = {
		'BPO': ['shubham.dhamija@ibtevolve.com'],
		'IT Outsourcing': ['mudassir.yousuff@ibtevolve.com', 'naushad.patel@ibtevolve.com'],
		'IT Infrastructure': ['operations.manager@ibtevolve.com']
		}.get(project_type)

	recipients.append('jai.mulani@ibtevolve.com')
	sendmail(recipients=recipients,
			subject = 'Weekly Task Report',
			message = message)

@frappe.whitelist()
def make_todo():
	data = db.sql(""" 
		SELECT 
			company_email,date_of_joining 
		FROM 
			`tabEmployee`
		WHERE 
			CURDATE() = DATE_ADD(date_of_joining , INTERVAL 181 DAY)
			and status = 'Active' and company_email != '' """, as_dict=1)

	for row in data:
		todo = frappe.new_doc("ToDo")
		todo.status = "Open"
		todo.date = add_days(nowdate(),7)
		todo.task_name = " HR One on One Meeting!!!"
		todo.owner = row.company_email
		todo.description = """ <div>Hi User,</div>
								<div>Please visit IBT Head Office for One on One meeting with HR Manager before the due date.</div><br>
								<div>Regards:</div>
								<div>TeamIBT</div>"""
		todo.assigned_by = "asha.vadakkepat@ibtevolve.com"
		
		todo.save()
		db.commit()


@frappe.whitelist()
def change_email_status():
	data = db.sql("""
		SELECT
			name
		FROM
			`tabEmail Queue`
		WHERE
			status = 'Error' 
		ORDER BY 
			modified DESC 
		LIMIT
			1000 """, as_dict=1)

	for row in data:
		queue = frappe.get_doc("Email Queue", row.name)
		queue.status = "Not Sent"
		queue.save()

@frappe.whitelist()
def opp_before_save(self, method):

	if self.enquiry_from == 'Lead':
		if self.contact_by and self.contact_date:
			frappe.db.set_value("Lead", self.lead, 'contact_by', self.contact_by)
			frappe.db.set_value("Lead", self.lead, 'contact_date', self.contact_date)

		if self.status == 'Lost':
			frappe.db.set_value("Lead", self.lead, 'status', "Lost")	

@frappe.whitelist()
def issue_before_save(self, method):
	if self.engineer_group:
		set_due_date(self)

def set_due_date(self):
	due_date = getdate(self.opening_date)
	due_days = 0
	default_holiday = frappe.db.get_value("Company",self.company,'default_holiday_list')
	holiday = frappe.get_doc("Holiday List",default_holiday)
	holiday_list =[row.holiday_date for row in holiday.holidays]

	i=0
	if due_date in holiday_list:
		due_days+=1
	elif due_date.weekday() == 5:
			due_days += 1
			
	opening_time = get_time(self.opening_time)	
	if self.issue_level == 'Remote Support Team':
		hour = int(opening_time.strftime('%H'))
		minutes = int(opening_time.strftime('%M'))
		if due_date in holiday_list:
			hour = 8
			opening_time = get_time("08:00:00")
		if hour > 16:
			hour = 8 + hour - 16
			closing_time = (datetime.combine(date.today(), opening_time).replace(hour=hour)).time()
			due_days += 1
		else:
			closing_time = (datetime.combine(date.today(), opening_time) + timedelta(hours=4)).time()
		self.db_set('closing_time',str(closing_time))

	
	elif self.issue_level == 'Level 1':
		due_days = 3
		self.db_set('closing_time',str(opening_time))
	else:
		due_days = 2
		self.db_set('closing_time',str(opening_time))

	while i<due_days:
		i+=1
		due_date= add_days(due_date,1)
		if due_date.weekday() in (5,6):
				due_days += 1
		elif due_date in holiday_list:
			due_days+=1
			
	self.due_date = due_date
	frappe.db.commit()

@frappe.whitelist()
def er_on_submit(self, method):
	change_employee(self)

def change_employee(self):
	
	lead = db.get_list("Lead", filters={'lead_owner': self.existing_user_id}, fields=('name'))
	opportunity = db.get_list("Opportunity", filters={'contact_by': self.existing_user_id}, fields=('name'))
	user_perm = db.get_list("User Permission", filters={'user': self.existing_user_id}, fields=('name'))

	if self.existing_sales_person and self.new_sales_person:
		lead_sp = db.get_list("Lead", filters={'sales_account_manager': self.existing_sales_person}, fields=('name'))
		
		for row in lead_sp:
			ld = frappe.get_doc("Lead", row.name)
			ld.db_set('sales_account_manager', self.new_sales_person)
	
	for row in lead:
		ld = frappe.get_doc("Lead", row.name)
		ld.db_set('lead_owner', self.new_user_id)
		ld.db_set('lead_owner_full_name', self.new_employee_name)
		
	for row in opportunity:
		opp = frappe.get_doc("Opportunity", row.name)
		opp.db_set('contact_by', self.new_user_id)
		opp.db_set('contact_by_name', self.new_employee_name)
		
	for row in user_perm:
		usr_per = frappe.get_doc("User Permission", row.name)
		usr_per.user = self.new_user_id
		usr_per.apply_for_all_roles = 0

		if usr_per.allow == 'Sales Person' and self.existing_sales_person and self.new_sales_person:
			usr_per.for_value = self.new_sales_person

		usr_per.save()

	if self.existing_role_profile:
		user = frappe.get_doc("User", self.new_user_id)
		user.role_profile_name = self.existing_role_profile
		user.save()

	db.commit()
	frappe.msgprint(_("Successfully updated all %s's records with %s!" % (self.existing_user_id, self.new_user_id)))

@frappe.whitelist()
def er_on_cancel(self, method):	
	lead = db.get_list("Lead", filters={'lead_owner': self.new_user_id}, fields=('name'))
	opportunity = db.get_list("Opportunity", filters={'contact_by': self.new_user_id}, fields=('name'))
	user_perm = db.get_list("User Permission", filters={'user': self.new_user_id}, fields=('name'))

	if self.existing_sales_person and self.new_sales_person:
		lead_sp = db.get_list("Lead", filters={'lead_owner': self.new_sales_person}, fields=('name'))
		for row in lead_sp:
			ld = frappe.get_doc("Lead", row.name)
			ld.db_set('sales_account_manager', self.existing_sales_person)

	for row in lead:
		ld = frappe.get_doc("Lead", row.name)
		ld.db_set('lead_owner', self.existing_user_id)
		ld.db_set('lead_owner_full_name', self.existing_employee_name)

	for row in opportunity:
		opp = frappe.get_doc("Opportunity", row.name)
		opp.db_set('contact_by', self.existing_user_id)
		opp.db_set('contact_by_name', self.existing_employee_name)
		
	for row in user_perm:
		usr_per = frappe.get_doc("User Permission", row.name)
		usr_per.user = self.existing_user_id
		usr_per.apply_for_all_roles = 0

		if usr_per.allow == 'Sales Person' and self.existing_sales_person and self.new_sales_person:
			usr_per.for_value = self.existing_sales_person

		usr_per.save()

	db.commit()

@frappe.whitelist()
def sl_before_save(self,method):
	user_id = frappe.db.get_value("Employee", self.employee, "user_id")
	self.db_set("employee_email", user_id)
	
@frappe.whitelist()
def update_issue_status():
	doctype = ["HR Issue", "Admin Issue"]

	for d in doctype:
		data = db.sql("""
			SELECT
				name
			FROM
				`tab%s`
			WHERE
				status = "Open"
				and due_date < CURDATE() """ % d , as_dict=1)

		for row in data:
			issue = frappe.get_doc(d, row.name)
			issue.status = "Overdue"
			issue.save()

@frappe.whitelist()
def ela_validate(self, method):
	validate_loan_amount(self)

def validate_loan_amount(self):
        base = frappe.db.get_value("Salary Structure Employee", {'employee': self.employee}, 'base')

        if self.loan_amount > (base/2):
                validated = False
                frappe.throw(_("Loan amount can not be more than 50% of salary"))

@frappe.whitelist()
def make_exit_form(source_name, target_doc=None):

	def postprocess(source,target):
		department,designation = frappe.db.get_value("Employee", source.employee, ["department","designation"])
		target.department = department
		target.designation = designation

	doclist = get_mapped_doc("Employee Resignation", source_name, {
			"Employee Resignation":{
				"doctype": "Exit Form",
				"field_no_map":[
					"status"
				]
			}
		}, target_doc,postprocess)
	
	return doclist

@frappe.whitelist()
def make_visa_process(source_name,target_doc=None):
	doclist = get_mapped_doc("Employee", source_name,{
			"Employee":{
				"doctype": "Visa Process",
				"field_map": {
					"name": "employee"
				}
			}
	},  target_doc)

	return doclist

@frappe.whitelist()
def make_activity(source_name,target_doc=None):
	doclist = get_mapped_doc("Customer",source_name,{
			"Customer":{
				"doctype": "Activity",
				"field_map":{
					"name" : "customer"
			}
		}
	}, target_doc)

	return doclist

@frappe.whitelist()
def disable_customer():
	enqueue(set_customer_disable, queue='long', timeout=2000)

def set_customer_disable():
	data = db.sql("""
		SELECT Distinct
			customer
		FROM
			`tabSales Order`
		WHERE
			transaction_date BETWEEN DATE_SUB(NOW(), INTERVAL 90 DAY) AND NOW()""", as_dict=1)

	customers = tuple(d.customer for d in data)

	customer = db.sql("""
		SELECT 
			name
		FROM
			`tabCustomer`
		WHERE
			disabled = 0
			and creation BETWEEN DATE_SUB(NOW(), DATEADD(day,-90,NOW())) and name not in (%s) """ % ', '.join(['%s'] * len(customers)), customers, as_dict=1)

	for row in customer:
		cust = frappe.get_doc("Customer", row.name)
		cust.db_set('disabled', 1)

@frappe.whitelist()
def daily_leave_allocation():
	emp =  db.get_list("Employee", 
			filters= {
				"probation_end_date": nowdate(), 
				'status': 'Active'
			}, 
			fields = ("name","date_of_joining","probation_end_date"))

	for e in emp:
		leave = frappe.new_doc("Leave Allocation")
		leave.employee = e.name
		leave.leave_type = "Flexible Leave"
		leave.from_date = nowdate()
		leave.to_date = str(getdate().year) + '-12-31'
		if e.date_of_joining.year < getdate().year:
			leave.new_leaves_allocated = 12
		else:
			leave.new_leaves_allocated = 12 - e.date_of_joining.month
		leave.carry_forward = 0
		leave.insert()
		leave.save()
		leave.submit()
		db.commit()

	emp = db.sql("""
		SELECT
			name
		FROM
			tabEmployee
		WHERE
			CURDATE() = DATE_ADD(date_of_joining, INTERVAL 1 YEAR)
			and status = 'Active' """, as_dict=1)

	for e in emp:
		leave = frappe.new_doc("Leave Allocation")
		leave.employee = e.name
		leave.leave_type = "Annual Leave"
		leave.from_date = nowdate()
		leave.to_date = add_date(add_months(nowdate(), 2), -1)
		leave.carry_forward = 0
		leave.new_leaves_allocated = 30
		leave.insert()
		leave.save()
		leave.submit()
		db.commit()

@frappe.whitelist()
def monthly_leave_allocation():
	emp = db.get_list("Employee", 
			filters= {
				"probation_end_date": ["<=", nowdate()], 
				'status': 'Active'
			}, 
			fields = "name")
	
	for e in emp:
		leave = frappe.new_doc("Leave Allocation")
		leave.employee = e.name
		leave.leave_type = "Flexible Leave"
		leave.from_date = nowdate()
		leave.to_date = add_date(add_months(nowdate(), 1), -1)
		leave.carry_forward = 0
		leave.new_leaves_allocated = 1
		leave.insert()
		leave.save()
		leave.submit()
		db.commit()

@frappe.whitelist()
def yearly_leave_allocation():
	emp = db.get_list("Employee", 
			filters= {
				"probation_end_date": ["<=", nowdate()], 
				'status': 'Active',
				'branch' : 'Headquarters, Dubai, United Arab Emirates'
			}, 
			fields = "name")
	
	for e in emp:
		leave = frappe.new_doc("Leave Allocation")
		leave.employee = e.name
		leave.leave_type = "Annual Leave"
		leave.from_date = nowdate()
		leave.to_date = add_days(add_months(nowdate(), 11), 30)
		leave.carry_forward = 0
		leave.new_leaves_allocated = 30
		leave.insert()
		leave.save()
		leave.submit()
		db.commit()

	emp = db.get_list("Employee", 
			filters= {
				"probation_end_date": ["<=", nowdate()], 
				'status': 'Active',
			}, 
			fields = "name")
	
	for e in emp:
		leave = frappe.new_doc("Leave Allocation")
		leave.employee = e.name
		leave.leave_type = "Flexible Leave"
		leave.from_date = nowdate()
		leave.to_date = add_days(add_months(nowdate(), 11), 30)
		leave.carry_forward = 0
		leave.new_leaves_allocated = 12
		leave.insert()
		leave.save()
		leave.submit()
		db.commit()

@frappe.whitelist()
def get_sales_owner(sales_manager):
        emp = frappe.db.get_value("Sales Person", sales_manager, "employee")
        emp_details = frappe.db.get_value("Employee", emp, ["user_id", "employee_name"])

        return emp_details

@frappe.whitelist()
def send_event_digest():
        from frappe.utils import format_datetime, nowdate
        from frappe.utils.user import get_enabled_system_users
        from frappe.desk.doctype.event.event import get_events

        today = nowdate()
        for user in get_enabled_system_users():
                events = get_events(today, today, user.name, for_reminder=True)
                if events:
                        frappe.set_user_lang(user.name, user.language)

                        for e in events:
                                e.starts_on = format_datetime(e.starts_on, 'hh:mm a')
                                if e.all_day:
                                        e.starts_on = "All Day"

                        frappe.sendmail(
                                recipients=user.email,
                                subject=frappe._("Upcoming Events for Today"),
                                template="upcoming_events",
                                args={
                                        'events': events,
                                },
                                header=[frappe._("Events in Today's Calendar"), 'blue']
                        )
