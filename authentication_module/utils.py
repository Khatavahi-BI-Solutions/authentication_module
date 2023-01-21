import frappe
import pyotp

def send_otp_mail(email):
	'''
		if mail sending fail then return otp itself
		and if success then return Success
	'''
	secret = pyotp.random_base32()
	totp = pyotp.TOTP(secret)
	otp = totp.now()
	frappe.cache().set_value(email, otp, expires_in_sec = 180)
	try:
		frappe.sendmail(
			recipients=email,
			sender=None,
			subject="Verification Code",
			template="verification_code",
			args=dict(code=otp),
			delayed=False,
			retry=3
		)
	except:
		frappe.log_error(title="Send Email Failed " + str(frappe.session.user))
		frappe.clear_messages()
		return otp

	return "Success"

def verify_email_otp(email, otp_to_verify):
    '''
        return true false
    '''
    otp = frappe.cache().get_value(email)
    if str(otp) == str(otp_to_verify):
        frappe.cache().delete_value(email)
        return True
    else:
        return False