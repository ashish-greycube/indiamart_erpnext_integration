import json

import frappe

from indiamart_erpnext_integration.indiamart_erpnext_controller import make_erpnext_lead_from_inidamart


def execute():
	# every processed row looks up Lead by query_id_cf; on a full scan this takes about 2 seconds per row
	frappe.db.add_index("Lead", ["query_id_cf"])
	mismatched = mark_rows_with_existing_lead_completed()
	process_stuck_rows(mismatched)


def mark_rows_with_existing_lead_completed():
	"""Lead was created but its Address insert failed, so the Indiamart Lead row stayed Queued.
	Returns rows whose Lead is a different customer; those are left Queued."""
	rows = frappe.db.sql(
		"""
		select il.name, il.indiamart_lead_json, l.name as lead, l.mobile_no, l.email_id
		from `tabIndiamart Lead` il
		join `tabLead` l on l.query_id_cf = il.query_id
		where il.status = 'Queued'
		""",
		as_dict=True,
	)

	mismatched = []
	for row in rows:
		if is_same_customer(row, json.loads(row.indiamart_lead_json)):
			frappe.db.set_value(
				"Indiamart Lead",
				row.name,
				{"status": "Completed", "output": f"Lead {row.lead} already exists (marked by patch)"},
			)
		else:
			mismatched.append(row.name)

	return mismatched


def is_same_customer(lead, lead_values):
	mobile_no = (lead_values.get("SENDER_MOBILE") or "").removeprefix("+91-")
	email_id = lead_values.get("SENDER_EMAIL")

	return bool(
		(mobile_no and mobile_no == (lead.mobile_no or "").removeprefix("+91-"))
		or (email_id and email_id == lead.email_id)
	)


def process_stuck_rows(skip):
	"""Oldest first, so a repeat customer's first enquiry creates the Lead and later ones update it."""
	filters = {"status": "Queued"}
	if skip:
		filters["name"] = ["not in", skip]

	rows = frappe.get_all(
		"Indiamart Lead",
		filters=filters,
		fields=["name", "indiamart_lead_json"],
		order_by="creation asc",
	)

	for row in rows:
		make_erpnext_lead_from_inidamart(json.loads(row.indiamart_lead_json), row.name)
		# commit per row: a crash midway keeps finished rows, and a re-run continues from the remaining Queued ones
		frappe.db.commit()
