# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
import datetime
from frappe import _, msgprint
from frappe.utils import flt
from erpnext.accounts.utils import get_fiscal_year
from frappe.utils import getdate


def get_period_date_ranges(period, fiscal_year=None, year_start_date=None):
	from dateutil.relativedelta import relativedelta
	today = datetime.datetime.today()
	year_start_date= datetime.date(today.year,today.month,1)
	if today.month == 12:	
		year_end_date = datetime.date(today.year,1,1)- datetime.timedelta (days = 1)
	else:
		year_end_date = datetime.date(today.year,(today.month+1),1)- datetime.timedelta (days = 1)
	#if not year_start_date:
	#	year_start_date, year_end_date = frappe.db.get_value("Fiscal Year",
	#		fiscal_year, ["year_start_date", "year_end_date"])

	increment = {
		"Monthly": 1,
		"Quarterly": 3,
		"Half-Yearly": 6,
		"Yearly": 12
	}.get(period)

	period_date_ranges = []
	for i in xrange(1, 12, increment):
		period_end_date = getdate(year_start_date) + relativedelta(months=increment, days=-1)
		if period_end_date > getdate(year_end_date):
			period_end_date = year_end_date
		period_date_ranges.append([year_start_date, period_end_date])
		year_start_date = period_end_date + relativedelta(days=1)
		if period_end_date == year_end_date:
			break

	return period_date_ranges

def get_period_month_ranges(period, fiscal_year):
	from dateutil.relativedelta import relativedelta
	period_month_ranges = []

	for start_date, end_date in get_period_date_ranges(period, fiscal_year):
		months_in_this_period = []
		while start_date <= end_date:
			months_in_this_period.append(start_date.strftime("%B"))
			start_date += relativedelta(months=1)
		period_month_ranges.append(months_in_this_period)

	return period_month_ranges

def execute(filters=None):
	if not filters: filters = {}

	columns = get_columns(filters)
	period_month_ranges = get_period_month_ranges(filters["period"], filters["fiscal_year"])
	sim_map = get_salesperson_item_month_map(filters)

	data = []
	for salesperson, salesperson_items in sim_map.items():
		for item_group, monthwise_data in salesperson_items.items():
			row = [salesperson, item_group]
			totals = [0, 0, 0]
			for relevant_months in period_month_ranges:
				period_data = [0, 0, 0]
				for month in relevant_months:
					month_data = monthwise_data.get(month, {})
					for i, fieldname in enumerate(["target", "achieved", "variance"]):
						value = flt(month_data.get(fieldname))
						period_data[i] += value
						totals[i] += value
				period_data[2] = period_data[0] - period_data[1]
				row += period_data
			totals[2] = totals[0] - totals[1]
			row 
			data.append(row)

	return columns, sorted(data, key=lambda x: (x[1], x[0]))

def get_columns(filters):
	for fieldname in ["fiscal_year", "period", "target_on"]:
		if not filters.get(fieldname):
			label = (" ".join(fieldname.split("_"))).title()
			msgprint(_("Please specify") + ": " + label,
				raise_exception=True)

	columns = [_("Sales Person") + ":Link/Sales Person:120", _("Item Group") + ":Link/Item Group:120"]

	group_months = False if filters["period"] == "Monthly" else True

	for from_date, to_date in get_period_date_ranges(filters["period"], filters["fiscal_year"]):
		for label in [_("Target") + " (%s)", _("Achieved") + " (%s)", _("Variance") + " (%s)"]:
			if group_months:
				label = label % (_(from_date.strftime("%b")) + " - " + _(to_date.strftime("%b")))
			else:
				label = label % _(from_date.strftime("%b"))

			columns.append(label+":Float:120")

	return columns

#Get sales person & item group details
def get_salesperson_details(filters):
	if 'person' in filters:
		return frappe.db.sql("""
			select
				sp.name, td.item_group, td.target_qty, td.target_amount, sp.distribution_id
			from
				`tabSales Person` sp, `tabTarget Detail` td
			where
				td.parent=sp.name and td.fiscal_year=%s and sp.name=%s order by td.item_group, sp.name
			""", (filters["fiscal_year"], filters["person"]), as_dict=1)
	else:
		return frappe.db.sql("""
			select
				sp.name, td.item_group, td.target_qty, td.target_amount, sp.distribution_id
			from
				`tabSales Person` sp, `tabTarget Detail` td
			where
				td.parent=sp.name and td.fiscal_year=%s order by td.item_group, sp.name
			""", (filters["fiscal_year"]), as_dict=1)	
#Get target distribution details of item group
def get_target_distribution_details(filters):
	target_details = {}

	for d in frappe.db.sql("""
		select
			md.name, mdp.month, mdp.percentage_allocation
		from
			`tabMonthly Distribution Percentage` mdp, `tabMonthly Distribution` md
		where
			mdp.parent=md.name and md.fiscal_year=%s
		""", (filters["fiscal_year"]), as_dict=1):
			target_details.setdefault(d.name, {}).setdefault(d.month, flt(d.percentage_allocation))

	return target_details

#Get achieved details from sales order
def get_achieved_details(filters, sales_person, all_sales_persons, target_item_group, item_groups):
	start_date, end_date = get_fiscal_year(fiscal_year = filters["fiscal_year"])[1:]

	item_details = frappe.db.sql("""
		select
			sum(soi.stock_qty * (st.allocated_percentage/100)) as qty,
			sum(soi.base_net_amount * (st.allocated_percentage/100)) as amount,
			st.sales_person, MONTHNAME(so.transaction_date) as month_name
		from
			`tabSales Order Item` soi, `tabSales Order` so, `tabSales Team` st
		where
			soi.parent=so.name and so.docstatus=1 and st.parent=so.name
			and so.transaction_date>=%s and so.transaction_date<=%s
			and exists(select name from `tabSales Person` where lft >= %s and rgt <= %s and name=st.sales_person)
			and exists(select name from `tabItem Group` where lft >= %s and rgt <= %s and name=soi.item_group)
		group by
			sales_person, month_name
			""",
		(start_date, end_date, all_sales_persons[sales_person].lft, all_sales_persons[sales_person].rgt, 
			item_groups[target_item_group].lft, item_groups[target_item_group].rgt), as_dict=1)

	actual_details = {}
	for d in item_details:
		actual_details.setdefault(d.month_name, frappe._dict({
			"quantity" : 0,
			"amount" : 0
		}))

		value_dict = actual_details[d.month_name]
		value_dict.quantity += flt(d.qty)
		value_dict.amount += flt(d.amount)

	return actual_details

def get_salesperson_item_month_map(filters):
	import datetime
	salesperson_details = get_salesperson_details(filters)
	tdd = get_target_distribution_details(filters)
	item_groups = get_item_groups()
	sales_persons = get_sales_persons(filters)

	sales_person_achievement_dict = {}
	for sd in salesperson_details:
		achieved_details = get_achieved_details(filters, sd.name, sales_persons, sd.item_group, item_groups)

		for month_id in range(1, 13):
			month = datetime.date(2013, month_id, 1).strftime('%B')
			sales_person_achievement_dict.setdefault(sd.name, {}).setdefault(sd.item_group, {})\
					.setdefault(month, frappe._dict({
							"target": 0.0, "achieved": 0.0
						}))

			sales_target_achieved = sales_person_achievement_dict[sd.name][sd.item_group][month]
			month_percentage = tdd.get(sd.distribution_id, {}).get(month, 0) \
				if sd.distribution_id else 100.0/12

			if (filters["target_on"] == "Quantity"):
				sales_target_achieved.target = flt(sd.target_qty) * month_percentage / 100
			else:
				sales_target_achieved.target = flt(sd.target_amount) * month_percentage / 100

			sales_target_achieved.achieved = achieved_details.get(month, frappe._dict())\
				.get(filters["target_on"].lower())

	return sales_person_achievement_dict

def get_item_groups():
	item_groups = frappe._dict()
	for d in frappe.get_all("Item Group", fields=["name", "lft", "rgt"]):
		item_groups.setdefault(d.name, frappe._dict({
			"lft": d.lft,
			"rgt": d.rgt
		}))
	return item_groups

def get_sales_persons(filters):
	sales_persons = frappe._dict()
	for d in frappe.get_all("Sales Person", fields=["name", "lft", "rgt"]):
		if 'person' in filters:
			if (d.name == filters["person"]):
				sales_persons.setdefault(d.name, frappe._dict({
					"lft": d.lft,
					"rgt": d.rgt
				}))
		else:
			sales_persons.setdefault(d.name, frappe._dict({
				"lft": d.lft,
				"rgt": d.rgt
			}))		
	return sales_persons
	