# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Other"),
			"items": [
				{
					"type": "doctype",
					"name": "Meeting",
				},
                {
					"type": "doctype",
					"name": "Allow Module",
				},
				{
					"type": "doctype",
					"name": "Role Restriction",
				}
			]
		},
		{
			"label": _("IBT"),
			"items": [
				{
					"type": "doctype",
					"name": "IBT Asset Request",
				},
				{
					"type": "doctype",
					"name": "IBT Asset Return",
				},
				{
					"type": "doctype",
					"name": "IBT Asset Handover",
				},
                {
					"type": "doctype",
					"name": "Business Segment",
				},
                {
					"type": "doctype",
					"name": "Device Registration Form",
				},
                {
					"type": "doctype",
					"name": "Company Asset",
				},
                {
					"type": "doctype",
					"name": "HR Issue",
				},
                {
					"type": "doctype",
					"name": "Admin Issue",
				},
			]
		}
	]