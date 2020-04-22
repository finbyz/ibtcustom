
from erpnext.projects.doctype.project.project import Project
import frappe
from frappe import _, sendmail
from frappe.utils import today

def override_update_project(self):
	Project.update_percent_complete(self)
	upadte_customer(self)
	Project.update_costing(self)
	Project.db_update(self)

def upadte_customer(self):
	if self.customer and self.percent_complete == 100:
		frappe.db.set_value('Customer',self.customer,'customer_status','Close')
	else:
		frappe.db.set_value('Customer',self.customer,'customer_status','Open')

#Override class method of Copy from Temlate for assigned to field
def copy_from_template(self):
	'''
	Copy tasks from template
	'''
	if self.project_template and not frappe.db.get_all('Task', dict(project = self.name), limit=1):

		# has a template, and no loaded tasks, so lets create
		if not self.expected_start_date:
			# project starts today
			self.expected_start_date = today()

		template = frappe.get_doc('Project Template', self.project_template)

		if not self.project_type:
			self.project_type = template.project_type

		# create tasks from template
		for task in template.tasks:
			frappe.get_doc(dict(
				doctype = 'Task',
				subject = task.subject,
				project = self.name,
				status = 'Open',
				exp_start_date = add_days(self.expected_start_date, task.start),
				exp_end_date = add_days(self.expected_start_date, task.start + task.duration),
				description = task.description,
				task_weight = task.task_weight,
				assigned_to = task.assign_to
			)).insert()
		self.save()