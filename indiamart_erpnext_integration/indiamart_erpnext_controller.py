from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.integrations.utils import create_request_log,make_post_request
from frappe.utils import get_datetime,now_datetime,format_datetime
from datetime import timedelta
import datetime
from frappe.utils.password import get_decrypted_password
from frappe.model.document import Document
import json
from six import string_types
import traceback,sys
from erpnext.crm.doctype.lead.lead import make_opportunity

@frappe.whitelist()
def manual_pull_indiamart_leads(start_time,end_time):
	try:
		indiamart_settings=get_indiamart_configuration()
		if indiamart_settings!='disabled':
			api_url,now_api_call_time=get_indiamart_api_url(indiamart_settings,start_time,end_time)
			if api_url:
				fetch_indiamart_data_and_make_integration_request(api_url,now_api_call_time)

	except Exception as e:
		title=_('Indiamart Error')
		seperator = "--" * 50
		error = "\n".join([format_datetime(now_datetime(),'d-MMM-y  HH:mm:ss'), "manual_pull_indiamart_leads",str(sys.exc_info()[1]), seperator,frappe.get_traceback()])
		frappe.log_error(message=error, title=title)

@frappe.whitelist()
def auto_pull_indiamart_leads():
	try:
		indiamart_settings=get_indiamart_configuration()
		if indiamart_settings!='disabled':
			api_url,now_api_call_time=get_indiamart_api_url(indiamart_settings)
			if api_url:
				fetch_indiamart_data_and_make_integration_request(api_url,now_api_call_time)

	except Exception as e:
		title=_('Indiamart Error')
		seperator = "--" * 50
		error = "\n".join([format_datetime(now_datetime(),'d-MMM-y  HH:mm:ss'), "auto_pull_indiamart_leads",str(sys.exc_info()[1]), seperator,frappe.get_traceback()])
		frappe.log_error(message=error, title=title)

def get_indiamart_configuration():
	if frappe.db.get_single_value("Indiamart Settings", "enabled"):
		indiamart_settings = frappe.get_doc("Indiamart Settings")
		return {
			"glusr_mobile": indiamart_settings.glusr_mobile,
			"glusr_mobile_key": indiamart_settings.glusr_mobile_key,
			"last_api_call_time": indiamart_settings.last_api_call_time
		}
	return "disabled"

def get_indiamart_api_url(indiamart_settings,start_time=None,end_time=None):
	if start_time==None:
		if indiamart_settings.get('last_api_call_time'):
			start_time=get_datetime(indiamart_settings.get('last_api_call_time')) - datetime.timedelta(minutes=5)
		else:
			start_time= now_datetime() - datetime.timedelta(minutes=5)
		start_time=format_datetime(start_time,'d-MMM-yHH:mm:ss')
		now_api_call_time=now_datetime()
		end_time=format_datetime(now_api_call_time,'d-MMM-yHH:mm:ss')
	if start_time!=None:
		start_time=format_datetime(start_time,'d-MMM-yHH:mm:ss')
		end_time=format_datetime(end_time,'d-MMM-yHH:mm:ss')
		# we don't change last call time as it is a manual attempt
		now_api_call_time=indiamart_settings.get('last_api_call_time')
	#  to do : put in config
	api_url = 'https://mapi.indiamart.com/wservce/enquiry/listing/'
	api_url = 'https://mapi.indiamart.com/wservce/enquiry/listing/GLUSR_MOBILE/{0}/GLUSR_MOBILE_KEY/{1}/Start_Time/{2}/End_Time/{3}/'.format(
				indiamart_settings.get('glusr_mobile'),
				get_decrypted_password('Indiamart Settings','Indiamart Settings','glusr_mobile_key'),
				start_time,
				end_time)
	return api_url,now_api_call_time



def fetch_indiamart_data_and_make_integration_request(api_url,now_api_call_time):
	valid_error_messages=['There are no leads in the given time duration.please try for a different duration.',
												'It is advised to hit this API once in every 5 minutes, but it seems that you have crossed this limit. Please try again after 5 minutes.']
	
	# response=[{'RN': '1', 'QUERY_ID': '4276830934', 'QTYPE': 'W', 'SENDERNAME': 'Rajesh Kumar', 'SENDEREMAIL': 'a@a.test', 'SUBJECT': 'Requirement for 60 W Solar Panel', 'DATE_RE': '13 Jul 2021', 'DATE_R': '13-Jul-21', 'DATE_TIME_RE': '13-Jul-2021 07:30:20 AM', 'GLUSR_USR_COMPANYNAME': None, 'READ_STATUS': None, 'SENDER_GLUSR_USR_ID': None, 'MOB': '+91-1983034993', 'COUNTRY_FLAG': '', 'QUERY_MODID': 'DIRECT', 'LOG_TIME': '20210713073020', 'QUERY_MODREFID': None, 'DIR_QUERY_MODREF_TYPE': None, 'ORG_SENDER_GLUSR_ID': None, 'ENQ_MESSAGE': 'I am interested in 60 W Solar Panel', 'ENQ_ADDRESS': 'Churu, Rajasthan', 'ENQ_CALL_DURATION': None, 'ENQ_RECEIVER_MOB': None, 'ENQ_CITY': 'Churu', 'ENQ_STATE': 'Rajasthan', 'PRODUCT_NAME': '60 W Solar Panel', 'COUNTRY_ISO': 'IN', 'EMAIL_ALT': None, 'MOBILE_ALT': None, 'PHONE': None, 'PHONE_ALT': None, 'IM_MEMBER_SINCE': None, 'TOTAL_COUNT': '1'},{'RN': '1', 'QUERY_ID': '1866810665', 'QTYPE': 'W', 'SENDERNAME': 'Hardeep', 'SENDEREMAIL': 'deepdhaliwal4683@gmail.com', 'SUBJECT': 'Requirement for Eastman Solar EPP PV Modules', 'DATE_RE': '13 Jul 2021', 'DATE_R': '13-Jul-21', 'DATE_TIME_RE': '13-Jul-2021 06:46:44 AM', 'GLUSR_USR_COMPANYNAME': 'Sgnt School', 'READ_STATUS': None, 'SENDER_GLUSR_USR_ID': None, 'MOB': '+91-9468464984', 'COUNTRY_FLAG': '', 'QUERY_MODID': 'DIRECT', 'LOG_TIME': '20210713064644', 'QUERY_MODREFID': None, 'DIR_QUERY_MODREF_TYPE': None, 'ORG_SENDER_GLUSR_ID': None, 'ENQ_MESSAGE': 'My Requirement is for Eastman Solar Epp 150w Pv Modules, Weight: 10.6 Kg. \n\nKindly send me price and other details.\n\n Quantity:   1   Piece\n Probable Order Value:   Rs. 2,800 - 5,000 \n', 'ENQ_ADDRESS': 'Mandi Dabwali, Haryana', 'ENQ_CALL_DURATION': None, 'ENQ_RECEIVER_MOB': None, 'ENQ_CITY': 'Mandi Dabwali', 'ENQ_STATE': 'Haryana', 'PRODUCT_NAME': 'Eastman Solar EPP PV Modules', 'COUNTRY_ISO': 'IN', 'EMAIL_ALT': None, 'MOBILE_ALT': None, 'PHONE': None, 'PHONE_ALT': None, 'IM_MEMBER_SINCE': None, 'TOTAL_COUNT': '2'}]
	# response=[{'RN': '1', 'QUERY_ID': '4276830934', 'QTYPE': 'W', 'SENDERNAME': 'Rajesh Kumar', 'SENDEREMAIL': 'a@a.test', 'SUBJECT': 'Requirement for 60 W Solar Panel', 'DATE_RE': '13 Jul 2021', 'DATE_R': '13-Jul-21', 'DATE_TIME_RE': '13-Jul-2021 07:30:20 AM', 'GLUSR_USR_COMPANYNAME': None, 'READ_STATUS': None, 'SENDER_GLUSR_USR_ID': None, 'MOB': '+91-1983034993', 'COUNTRY_FLAG': '', 'QUERY_MODID': 'DIRECT', 'LOG_TIME': '20210713073020', 'QUERY_MODREFID': None, 'DIR_QUERY_MODREF_TYPE': None, 'ORG_SENDER_GLUSR_ID': None, 'ENQ_MESSAGE': 'I am interested in 60 W Solar Panel', 'ENQ_ADDRESS': 'Churu, Rajasthan', 'ENQ_CALL_DURATION': None, 'ENQ_RECEIVER_MOB': None, 'ENQ_CITY': 'Churu', 'ENQ_STATE': 'Rajasthan', 'PRODUCT_NAME': '60 W Solar Panel', 'COUNTRY_ISO': 'IN', 'EMAIL_ALT': None, 'MOBILE_ALT': None, 'PHONE': None, 'PHONE_ALT': None, 'IM_MEMBER_SINCE': None, 'TOTAL_COUNT': '1'}]												
	# response=[{'RN': '1', 'QUERY_ID': '1866810665', 'QTYPE': 'W', 'SENDERNAME': 'Hardeep', 'SENDEREMAIL': 'deepdhaliwal4683@gmail.com', 'SUBJECT': 'Requirement for Eastman Solar EPP PV Modules', 'DATE_RE': '13 Jul 2021', 'DATE_R': '13-Jul-21', 'DATE_TIME_RE': '13-Jul-2021 06:46:44 AM', 'GLUSR_USR_COMPANYNAME': 'Sgnt School', 'READ_STATUS': None, 'SENDER_GLUSR_USR_ID': None, 'MOB': '+91-9468464984', 'COUNTRY_FLAG': '', 'QUERY_MODID': 'DIRECT', 'LOG_TIME': '20210713064644', 'QUERY_MODREFID': None, 'DIR_QUERY_MODREF_TYPE': None, 'ORG_SENDER_GLUSR_ID': None, 'ENQ_MESSAGE': 'My Requirement is for Eastman Solar Epp 150w Pv Modules, Weight: 10.6 Kg. \n\nKindly send me price and other details.\n\n Quantity:   1   Piece\n Probable Order Value:   Rs. 2,800 - 5,000 \n', 'ENQ_ADDRESS': 'Mandi Dabwali, Haryana', 'ENQ_CALL_DURATION': None, 'ENQ_RECEIVER_MOB': None, 'ENQ_CITY': 'Mandi Dabwali', 'ENQ_STATE': 'Haryana', 'PRODUCT_NAME': 'Eastman Solar EPP PV Modules', 'COUNTRY_ISO': 'IN', 'EMAIL_ALT': None, 'MOBILE_ALT': None, 'PHONE': None, 'PHONE_ALT': None, 'IM_MEMBER_SINCE': None, 'TOTAL_COUNT': '2'}]
	# response=[{'RN': '1', 'QUERY_ID': '449272972', 'QTYPE': 'B', 'SENDERNAME': 'Jaygeet', 'SENDEREMAIL': 'jkgajera1991@gmail.com', 'SUBJECT': 'Requirement for Solar Pump Controller', 'DATE_RE': '12 Jul 2021', 'DATE_R': '12-Jul-21', 'DATE_TIME_RE': '12-Jul-2021 11:14:58 AM', 'GLUSR_USR_COMPANYNAME': 'Greenedge Energy', 'READ_STATUS': None, 'SENDER_GLUSR_USR_ID': None, 'MOB': '+91-9737015250', 'COUNTRY_FLAG': '', 'QUERY_MODID': 'DIRECT', 'LOG_TIME': '20210712111458', 'QUERY_MODREFID': None, 'DIR_QUERY_MODREF_TYPE': None, 'ORG_SENDER_GLUSR_ID': None, 'ENQ_MESSAGE': 'I am interested in buying Solar Pump Controller. \n\nKindly send me price and other details.<br>Quantity : 10 piece<br>Probable Order Value : Rs. 1 to 2 Lakh<br>Probable Requirement Type : Business Use', 'ENQ_ADDRESS': '409, Time Trad Centre, Opposite Polaris Complex, Canal Road, Puna Gam, Surat, Surat, Gujarat,         395010', 'ENQ_CALL_DURATION': None, 'ENQ_RECEIVER_MOB': None, 'ENQ_CITY': 'Surat', 'ENQ_STATE': 'Gujarat', 'PRODUCT_NAME': 'Solar Pump Controller', 'COUNTRY_ISO': 'IN', 'EMAIL_ALT': None, 'MOBILE_ALT': None, 'PHONE': None, 'PHONE_ALT': None, 'IM_MEMBER_SINCE': None, 'TOTAL_COUNT': '2'}, {'RN': '2', 'QUERY_ID': '311972279', 'QTYPE': 'P', 'SENDERNAME': 'Buyer', 'SENDEREMAIL': None, 'SUBJECT': 'Buyer Call', 'DATE_RE': '12 Jul 2021', 'DATE_R': '12-Jul-21', 'DATE_TIME_RE': '12-Jul-2021 11:10:41 AM', 'GLUSR_USR_COMPANYNAME': None, 'READ_STATUS': None, 'SENDER_GLUSR_USR_ID': None, 'MOB': '7734055669', 'COUNTRY_FLAG': '', 'QUERY_MODID': 'DIRECT', 'LOG_TIME': '20210712000000', 'QUERY_MODREFID': None, 'DIR_QUERY_MODREF_TYPE': None, 'ORG_SENDER_GLUSR_ID': None, 'ENQ_MESSAGE': None, 'ENQ_ADDRESS': '', 'ENQ_CALL_DURATION': '85 Secs', 'ENQ_RECEIVER_MOB': '7948991308', 'ENQ_CITY': None, 'ENQ_STATE': None, 'PRODUCT_NAME': None, 'COUNTRY_ISO': 'IN', 'EMAIL_ALT': None, 'MOBILE_ALT': None, 'PHONE': None, 'PHONE_ALT': None, 'IM_MEMBER_SINCE': None, 'TOTAL_COUNT': '2'}]
	# response=[{'RN': '1', 'QUERY_ID': '1974413910', 'QTYPE': 'W', 'SENDERNAME': 'Nitesh Mendapara', 'SENDEREMAIL': None, 'SUBJECT': 'Requirement for 5HP AC CI Solar Submersible Pump With Controller', 'DATE_RE': '19 Jul 2021', 'DATE_R': '19-Jul-21', 'DATE_TIME_RE': '19-Jul-2021 09:00:56 AM', 'GLUSR_USR_COMPANYNAME': None, 'READ_STATUS': None, 'SENDER_GLUSR_USR_ID': None, 'MOB': '+91-9879019410', 'COUNTRY_FLAG': '', 'QUERY_MODID': 'DIRECT', 'LOG_TIME': '20210719090056', 'QUERY_MODREFID': None, 'DIR_QUERY_MODREF_TYPE': None, 'ORG_SENDER_GLUSR_ID': None, 'ENQ_MESSAGE': 'I want to buy 6" 7.5hp AC Ci Solar Submersible Pump with Controller. \n\nKindly send me price and other details.\n\n Quantity:   1   piece\n Probable Order Value:   Rs. 20,000 to 50,000 \n', 'ENQ_ADDRESS': 'Dhrol, Gujarat', 'ENQ_CALL_DURATION': None, 'ENQ_RECEIVER_MOB': None, 'ENQ_CITY': 'Dhrol', 'ENQ_STATE': 'Gujarat', 'PRODUCT_NAME': '5HP AC CI Solar Submersible Pump With Controller', 'COUNTRY_ISO': 'IN', 'EMAIL_ALT': None, 'MOBILE_ALT': None, 'PHONE': None, 'PHONE_ALT': None, 'IM_MEMBER_SINCE': None, 'TOTAL_COUNT': '2'}, {'RN': '2', 'QUERY_ID': '1874713865', 'QTYPE': 'W', 'SENDERNAME': 'Lalji Nandvana', 'SENDEREMAIL': 'nandvanalalji360@gmail.com', 'SUBJECT': 'Requirement for Solar Water Pumping System', 'DATE_RE': '19 Jul 2021', 'DATE_R': '19-Jul-21', 'DATE_TIME_RE': '19-Jul-2021 09:00:55 AM', 'GLUSR_USR_COMPANYNAME': 'Ashapura Kirana Store', 'READ_STATUS': None, 'SENDER_GLUSR_USR_ID': None, 'MOB': '+91-9725663841', 'COUNTRY_FLAG': '', 'QUERY_MODID': 'DIRECT', 'LOG_TIME': '20210719090055', 'QUERY_MODREFID': None, 'DIR_QUERY_MODREF_TYPE': None, 'ORG_SENDER_GLUSR_ID': None, 'ENQ_MESSAGE': 'I am interested in Solar Water Pumping System\n\n Probable Unit Price:   Rs. 1 to 2 Lakh \n', 'ENQ_ADDRESS': 'Tulsishyam Road, Junagadh, Gujarat, 362530', 'ENQ_CALL_DURATION': None, 'ENQ_RECEIVER_MOB': None, 'ENQ_CITY': 'Junagadh', 'ENQ_STATE': 'Gujarat', 'PRODUCT_NAME': 'Solar Water Pumping System', 'COUNTRY_ISO': 'IN', 'EMAIL_ALT': None, 'MOBILE_ALT': None, 'PHONE': None, 'PHONE_ALT': None, 'IM_MEMBER_SINCE': None, 'TOTAL_COUNT': '2'}]
	response=[{"RN": "19", "QUERY_ID": "493656332", "QTYPE": "B", "SENDERNAME": "Pervez Ahmad", "SENDEREMAIL": "arassociatesranchi@gmail.com", "SUBJECT": "Requirement for Oil Filled Submersible Pump", "DATE_RE": "29 Jun 2022", "DATE_R": "29-Jun-22", "DATE_TIME_RE": "29-Jun-2022 05:27:26 PM", "GLUSR_USR_COMPANYNAME": "AR Associate", "READ_STATUS": None, "SENDER_GLUSR_USR_ID": None, "MOB": "+91-9835372228", "COUNTRY_FLAG": "", "QUERY_MODID": "DIRECT", "LOG_TIME": "20220629172726", "QUERY_MODREFID": None, "DIR_QUERY_MODREF_TYPE": None, "ORG_SENDER_GLUSR_ID": None, "ENQ_MESSAGE": "I want to buy Oil Filled Submersible Pump. \n\nKindly send me price and other details.<br>Quantity : 40 piece<br>Probable Order Value : Rs. 1,60,000 - 3,12,000<br>Probable Requirement Type : Business Use", "ENQ_ADDRESS": "Hose No 1, 95 New Parasoli Doranda, Ranchi, Ranchi, Jharkhand,         834002", "ENQ_CALL_DURATION": None, "ENQ_RECEIVER_MOB": None, "ENQ_CITY": "Ranchi", "ENQ_STATE": "Jharkhand", "PRODUCT_NAME": "Oil Filled Submersible Pump", "COUNTRY_ISO": "IN", "EMAIL_ALT": None, "MOBILE_ALT": None, "PHONE": None, "PHONE_ALT": None, "IM_MEMBER_SINCE": None, "TOTAL_COUNT": "19"}]
	# response = make_post_request(api_url)
	print('response---'*10,type(response))
	if not response:
		return
	response =list(response)

	if isinstance(response, string_types):
		response = json.loads(response)	
	print('response',response)
	data={
		'api_url':api_url
	}
	request_log_data={
		'api_url':api_url,
		"reference_doctype":"Indiamart Lead"
	}
	error=None
	output={
		'output':response
	}


	if response[0].get('Error_Message'):
		error=response[0].get('Error_Message')
		
	if not error:
		integration_request=create_request_log(data=frappe._dict(request_log_data),integration_type="Remote",service_name="Indiamart")
		frappe.db.set_value('Integration Request', integration_request.name, 'output',json.dumps(output) )
	else:
		integration_request=create_request_log(data=frappe._dict(request_log_data),integration_type="Remote",service_name="Indiamart",error=frappe._dict({"error":error}))
		frappe.db.set_value('Integration Request', integration_request.name, 'output', json.dumps(output))

	error_message=response[0].get('Error_Message')
	status=None

	if (not error_message):
		status='Queued'
	elif error_message in valid_error_messages:
		frappe.db.set_value('Integration Request', integration_request.name, 'status', 'Cancelled')
		frappe.db.set_value('Indiamart Settings','Indiamart Settings', 'last_api_call_time', now_api_call_time)
		status='Failed'
	else: 
		frappe.db.set_value('Integration Request', integration_request.name, 'status', 'Failed')
		status='Failed'	
		# serious error. log it
		error_message=error_message+'\nIntegration Request ID :'+integration_request.name
		frappe.log_error(error_message, title=_('Indiamart Error'))	
	print('status',status)
	if 	status!='Failed':
		for index in range(len(response)):
				lead_values={}
				for key in response[index]:
						lead_values.update({key:response[index][key]})
				# make_lead_from_inidamart(lead_values)
				print('lead_values,integration_request.name',lead_values,integration_request.name)
				make_indiamart_lead_records(lead_values,integration_request.name)
		frappe.db.set_value('Integration Request', integration_request.name, 'status', 'Completed')
		frappe.db.set_value('Indiamart Settings','Indiamart Settings', 'last_api_call_time', now_api_call_time)

	return

def make_indiamart_lead_records(lead_values,integration_request,status='Queued',output='Not Processed'):
	existing_indiamart_lead = frappe.db.get_value("Indiamart Lead", {"query_id": lead_values.get('QUERY_ID')})
	if not existing_indiamart_lead:
		indiamart_lead=frappe.new_doc('Indiamart Lead')
		indiamart_lead.query_id=lead_values.get('QUERY_ID',None)
		indiamart_lead.indiamart_lead_json=json.dumps(lead_values)
		indiamart_lead.status=status
		indiamart_lead.output=output
		indiamart_lead.integration_request=integration_request
		indiamart_lead.save(ignore_permissions=True)
		return indiamart_lead.name
	return



def make_erpnext_lead_from_inidamart(lead_values,indiamart_lead_name=None):
	print('make_erpnext_lead_from_inidamart')
	try:
		output=None

		user=frappe.db.get_single_value('Indiamart Settings', 'default_lead_owner')
		country=frappe.get_value("Country", {"code": lead_values.get("COUNTRY_ISO", "IN").lower()}) or 'India'
		state=lead_values.get('ENQ_STATE',None)
		city=lead_values.get('ENQ_CITY',None)
		email_id=lead_values.get('SENDEREMAIL',None)
		mobile_no=lead_values.get('MOB',None)		

		lead_owner=user
		lead_name = None
		lead_name = frappe.db.get_value("Lead", {"query_id_cf": lead_values.get('QUERY_ID')})
		# It is a new lead from indiamart
		if not lead_name :
			check_duplicate_mobile_no=mobile_no
			lead_name = frappe.db.get_value("Lead", {"mobile_no": check_duplicate_mobile_no})
			#  It is a repeat user having same mobile_no
			if lead_name:
				existing_lead_output=update_existing_lead(lead_name,lead_values)
				output='Duplicate Mobile No: {0}'.format(existing_lead_output)
				frappe.db.set_value('Indiamart Lead', indiamart_lead_name, 'output', output)
				frappe.db.set_value('Indiamart Lead', indiamart_lead_name, 'status', 'Completed')			
				return output
			# It is may be a fresh lead 
			elif not lead_name:
					lead_name = frappe.db.get_value("Lead", {"email_id": email_id})
					# It is a repeat user having same email id
					if lead_name:
						existing_lead_output=update_existing_lead(lead_name,lead_values)
						output='Duplicate Email ID: {0}'.format(existing_lead_output)
						frappe.db.set_value('Indiamart Lead', indiamart_lead_name, 'output', output)
						frappe.db.set_value('Indiamart Lead', indiamart_lead_name, 'status', 'Completed')					
						return output
					elif not lead_name:
					# it is finally a fresh lead
						# source logic 
						if lead_values.get('QTYPE') == 'W' :
							source= frappe.db.get_single_value('Indiamart Settings', 'direct_lead_source')
						elif lead_values.get('QTYPE') == 'B' :
							source= frappe.db.get_single_value('Indiamart Settings', 'buy_lead_source')
						elif lead_values.get('QTYPE') == 'P' :
							source= frappe.db.get_single_value('Indiamart Settings', 'call_lead_source')
							
						if lead_values.get('GLUSR_USR_COMPANYNAME'):
							organization_lead=1
							company_name=lead_values.get('GLUSR_USR_COMPANYNAME')
							address_type='Office'
							address_title='Work'
						else:
							organization_lead=0
							company_name=None
							address_type='Personal'
							address_title='Work'
						
						notes_html="<div>Product Name :{0}</div><div>Subject :{1}</div><div>Message :{2}</div><div>Lead Date :{3}</div><div>Alternate EmailID :{4}</div><div>Alternate Mobile :{5}</div><div>India Mart Query ID :{6}</div>" \
						.format( \
										frappe.bold(lead_values.get('PRODUCT_NAME','Not specified')),
										frappe.bold(lead_values.get('SUBJECT','Not specified')),
										frappe.bold(lead_values.get('ENQ_MESSAGE','Not specified')),
										frappe.bold(lead_values.get('DATE_TIME_RE','Not specified')),
										frappe.bold(lead_values.get('EMAIL_ALT','Not specified')),
										frappe.bold(lead_values.get('MOBILE_ALT','Not specified')),
										frappe.bold(lead_values.get('QUERY_ID','Not specified'))
										)

						n  = 140
						address=lead_values.get('ENQ_ADDRESS')
						pincode=None
						address_line1,address_line2='',''

						if address:
							# extract pincode
							for word in address.rsplit():
								if word.isdigit() and len(word)==6:
										pincode=int(word)

							for index in range(0, len(address), n):
									if index==0:
										address_line1=address[index : index + n]
									elif index==1:
										address_line2=address[index : index + n]
						print('pincode',pincode)
						lead=frappe.new_doc('Lead')
						lead_value_dict={
							"lead_name": lead_values.get('SENDERNAME'),
							"email_id":email_id,
							"mobile_no": mobile_no,
							"source":source or '',
							"organization_lead":organization_lead,
							"company_name":company_name,
							"notes":notes_html,
							"state":state,
							"country":country ,
							"city": city,
							"query_id_cf":lead_values.get('QUERY_ID'),
							"address_title":address_title or 'Other',
							"address_type":address_type or 'Other',
							"address_line1":address_line1,
							"address_line2":address_line2,
							"pincode":pincode,
							'contact_by':'',
							'lead_owner':lead_owner
						}
						lead.update(lead_value_dict)
						lead.flags.ignore_mandatory = True
						lead.flags.ignore_permissions = True
						lead.save()
						
						# update details to indiamart lead doctype
						output='Lead {0} is created.'.format(lead.name)
						frappe.db.set_value('Indiamart Lead', indiamart_lead_name, 'output', output)
						frappe.db.set_value('Indiamart Lead', indiamart_lead_name, 'status', 'Completed')					
						return output
				
		else:
				# indiamart has send lead with same query id. Almost impossilble
				output='Duplicate Query_ID. It is in existing Lead {0}'.format(lead_name)
				frappe.db.set_value('Indiamart Lead', indiamart_lead_name, 'output', output)
				frappe.db.set_value('Indiamart Lead', indiamart_lead_name, 'status', 'Completed')			
				return output
	except Exception as e:
		title=_('Indiamart Error')
		seperator = "--" * 50
		error = "\n".join([format_datetime(now_datetime(),'d-MMM-y  HH:mm:ss'), "make_erpnext_lead_from_inidamart","indiamart_lead_name  "+indiamart_lead_name,str(sys.exc_info()[1]), seperator,frappe.get_traceback()])
		frappe.log_error(message=error, title=title)

def update_existing_lead(lead_name,lead_values):
		existing_lead_output=None
		lead_status = frappe.db.get_value('Lead', lead_name, 'status')

		if lead_status not in ['Converted','Quotation']:
			notes_html="<br><br><div><B>New Requirement</B></div><div>Product Name :{0}</div><div>Subject :{1}</div><div>Message :{2}</div><div>Lead Date :{3}</div><div>Alternate EmailID :{4}</div><div>Alternate Mobile :{5}</div><div>India Mart Query ID :{6}</div>" \
			.format( \
								frappe.bold(lead_values.get('PRODUCT_NAME','Not specified')),
								frappe.bold(lead_values.get('SUBJECT','Not specified')),
								frappe.bold(lead_values.get('ENQ_MESSAGE','Not specified')),
								frappe.bold(lead_values.get('DATE_TIME_RE','Not specified')),
								frappe.bold(lead_values.get('EMAIL_ALT','Not specified')),
								frappe.bold(lead_values.get('MOBILE_ALT','Not specified')),
								frappe.bold(lead_values.get('QUERY_ID','Not specified'))
								)

			lead=frappe.get_doc('Lead', lead_name)
			lead.reload()
			if lead.notes:
				lead.notes=lead.notes+notes_html
			else:
				lead.notes=notes_html
			lead.query_id_cf=lead_values.get('QUERY_ID')
			lead.status='Lead'
			lead.flags.ignore_mandatory = True
			lead.flags.ignore_permissions = True
			lead.contact_date=''
			lead.contact_by=''
			lead.save()	
			existing_lead_output='Lead notes updated for {0}'.format(lead_name)
			return existing_lead_output	
		else:
			to_discuss_html="New Requirement \n Product Name : {0} \n Subject :{1} \n Message :{2} \n Lead Date :{3} \n Alternate EmailID :{4} \n Alternate Mobile :{5} \n India Mart Query ID :{6}" \
			.format( \
								frappe.bold(lead_values.get('PRODUCT_NAME','Not specified')),
								frappe.bold(lead_values.get('SUBJECT','Not specified')),
								frappe.bold(lead_values.get('ENQ_MESSAGE','Not specified')),
								frappe.bold(lead_values.get('DATE_TIME_RE','Not specified')),
								frappe.bold(lead_values.get('EMAIL_ALT','Not specified')),
								frappe.bold(lead_values.get('MOBILE_ALT','Not specified')),
								frappe.bold(lead_values.get('QUERY_ID','Not specified'))
								)

			opportunity=make_opportunity(source_name=lead_name)
			opportunity.flags.ignore_mandatory = True
			opportunity.flags.ignore_permissions = True
			opportunity.to_discuss=to_discuss_html
			opportunity.sales_stage= frappe.db.get_single_value('Indiamart Settings', 'default_opportunity_sales_stage')
			opportunity.save()			

			opportunity_html='<br><br><div><B>New Oppurtunity {0} was created</B>'.format(opportunity.name)
			lead=frappe.get_doc('Lead', lead_name)
			lead.reload()
			lead.query_id_cf=lead_values.get('QUERY_ID')
			if lead.notes:
				lead.notes=lead.notes+opportunity_html
			else:
				lead.notes=opportunity_html
			lead.contact_date=''
			lead.contact_by=''
			lead.flags.ignore_mandatory = True
			lead.flags.ignore_permissions = True
			lead.save()		
			existing_lead_output='Opportunity is {0} created for Lead{1}'.format(opportunity.name,lead_name)
			return existing_lead_output			



def get_integration_request_dashboard_data(data):
	if len(data.get("transactions"))>0:
		for d in data.get("transactions",[]):
			print('d',d)
			d.update({"items":d.get("items") +["ToDo"]})
	else:
		data.get("transactions").append({"items":["ToDo"]})
	return data