import frappe
from authentication_module import ApiEndpoint
from authentication_module.utils import send_otp_mail

@frappe.whitelist(allow_guest=True)
def endpoint():
	return RequestEmailOTP().run()

class RequestEmailOTP(ApiEndpoint):
	def __init__(self):
		super(RequestEmailOTP, self).__init__("RequestEmailOTP")

	def default(self, *args, **kwargs):
		body = self.form_body()
		self.body = body
		required_field = [
			"email"
		]

		valid = self.validate_required_parameters(
			body, required_field)
		if not valid:
			return
		self.email = body.get('email')
		self.set_token()

		self.store_details_catch()

		self.send_otp()

		self.set_resend_time()

		return

	def set_resend_time(self):
		self.data['resend_otp'] = "30"

	def set_token(self):
		self.token = self.email
		self.data['token'] = self.token

	def store_details_catch(self):
		catch_data = {
			"email": self.email,
			"created_on": frappe.utils.now(),
			"resend_otp_count": 0,
			"failed_otp_count": 0,
		}
		frappe.cache().hset('request_otp', self.token, catch_data)

	def send_otp(self):
		response = send_otp_mail(self.email)
		if response == "Success":
			self.message = "OTP Sent on {0}".format(self.email)
		else:
			self.data['otp'] = response