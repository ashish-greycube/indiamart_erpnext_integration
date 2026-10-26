import frappe


def get_territory(city, state, country):
	"""Return the most specific Territory available for the enquiry."""
	for territory in (city, state, country, "India"):
		if territory and frappe.db.exists("Territory", territory):
			return territory

	return "India"


def get_lead_owner(territory, default_user):
	"""Resolve lead owner from territory manager or round-robin, falling back to default_user."""
	user = default_user
	territory_manager = frappe.db.get_value("Territory", territory, "territory_manager")

	if not territory_manager:
		if frappe.get_meta("Territory").get_field("multiple_territory_manager_cf"):
			multiple_territory_manager_cf = frappe.db.get_value("Territory", territory, "multiple_territory_manager_cf")
			if multiple_territory_manager_cf == 1:
				user = get_user_round_robin(territory)
				if user:
					if frappe.get_meta("Territory").get_field("last_user_cf"):
						frappe.db.set_value("Territory", territory, "last_user_cf", user)
					return user
	else:
		is_user_cf = frappe.get_meta("Sales Person").get_field("user_cf")
		if is_user_cf:
			user = frappe.db.get_value("Sales Person", territory_manager, "user_cf")
		else:
			employee = frappe.db.get_value("Sales Person", territory_manager, "employee")
			if employee:
				user = frappe.db.get_value("Employee", employee, "user_id")
				if user:
					return user
		if user:
			return user

	return default_user


def get_user_round_robin(territory_name):
	"""Get next user based on round-robin. Returns None if users_cf is empty."""
	if not frappe.get_meta("Territory").get_field("users_cf"):
		return None

	territory = frappe.get_doc("Territory", territory_name)

	if not territory.get("users_cf"):
		return None

	# first time, or last in list, pick the first
	if not territory.get("last_user_cf") or territory.last_user_cf == territory.users_cf[-1].user:
		return territory.users_cf[0].user

	# find out the next user in the list
	for i, d in enumerate(territory.users_cf):
		if territory.last_user_cf == d.user:
			return territory.users_cf[i + 1].user

	# bad last user, assign to the first one
	return territory.users_cf[0].user
