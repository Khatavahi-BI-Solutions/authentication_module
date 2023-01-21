from datetime import datetime
import base64

import frappe

from authentication_module import ApiEndpoint
from authentication_module.utils import verify_email_otp

@frappe.whitelist(allow_guest=True)
def endpoint():
	return VerifyEmailOTP().run()


class VerifyEmailOTP(ApiEndpoint):
	def __init__(self):
		super(VerifyEmailOTP, self).__init__("VerifyEmailOTP")

	def default(self, *args, **kwargs):
		body = self.json_body()
		self.body = body
		valid = self.validate_required_parameters(
			body, ["token", "otp"])

		if not valid:
			return

		self.otp = body.get('otp')
		self.token = body.get('token')
		self.phone = self.token

		self.get_details_catch()

		self.max_otp_retry = "3"

		if int(self.failed_otp_count) > int(self.max_otp_retry):
			self.code = 403
			self.message = "Incorrect OTP reached max limit. Please try resend OTP."
			return

		valid = self.verify_otp()

		if not valid:
			self.message = "Invalid OTP"
			self.code = 401
			self.set_details_catch()
			return
		else:
			self.create_user()
			self.create_client()
			self.start_session()
			self.delete_details_catch()
		return
	
	def set_user(self):
		user = frappe.get_value("User", {"email": self.email})
		if not user:
			self.create_user()
	
	def delete_details_catch(self):
		frappe.cache().hdel('request_otp', self.token)

	def get_details_catch(self):
		data = frappe.cache().hget('request_otp', self.token)
		
		self.message = data
		self.email = data['email']
		self.created_on = data['created_on']
		self.resend_otp_count = data['resend_otp_count']
		self.failed_otp_count = data['failed_otp_count']

		self.signup_cache_data = data
	
	def set_details_catch(self):
		data = {
			"email": self.email,
			"created_on": self.created_on,
			"resend_otp_count": self.resend_otp_count,
			"failed_otp_count": self.failed_otp_count,
		}
		frappe.cache().hset('request_otp', self.token, data)

	def set_api_key(self):
		user = self.user
		api_secret = frappe.generate_hash(length=15)
		# if api key is not set generate api key
		if not user.api_key:
			api_key = frappe.generate_hash(length=15)
			user.api_key = api_key
		user.api_secret = api_secret
		user.save(ignore_permissions=True)
		frappe.db.commit()
		token = base64.b64encode(
			(user.api_key+":"+api_secret).encode('ascii')).decode('ascii')
		frappe.local.response["token"] = token

	def start_session(self):
		self.set_api_key()

	def create_user(self):
		user = frappe.new_doc("User")
		user.email = self.email
		user.first_name = self.get_first_name()
		user.send_welcome_email = False
		user.flags.ignore_permissions = True
		user.insert()
		self.user = user
		print("User Created")

		portal_settings = frappe.get_single("Portal Settings")
		default_role = portal_settings.default_role
		if default_role:
			user.add_roles(default_role)
		frappe.set_user(self.user.name)

	def create_client(self):
		pass

	def get_first_name(self):
		return self.email

	def verify_otp(self):
		'''
			should return True / False
		'''
		status = verify_email_otp(self.token, self.otp)
		if status:
			self.message = "Email Verified"
			return True
		else:
			self.failed_otp_count += 1
			self.signup_cache_data['failed_otp_count'] = self.failed_otp_count
			self.signup_cache_data['failed_at'] = datetime.now()
			frappe.cache().hset('request_otp', self.token, self.signup_cache_data)
			return False
