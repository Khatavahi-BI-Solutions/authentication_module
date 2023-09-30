from datetime import datetime
import base64
import frappe
from authentication_module.api import ApiEndpoint

@frappe.whitelist(allow_guest=True)
def endpoint():
    return Authenticate().run()


class Authenticate(ApiEndpoint):
    def __init__(self):
        super(Authenticate, self).__init__("VerifyEmailOTP")

    def default(self, *args, **kwargs):
        body = self.form_body()
        self.body = body
        valid = self.validate_required_parameters(
            body, ["email", "pwd"])

        if not valid:
            return

        self.email = body.get('email')
        self.pwd = body.get('pwd')

        frappe.local.login_manager.authenticate(user=self.email, pwd=self.pwd)
        
        self.set_api_key()
        
        return "Success"

    def set_api_key(self):
        user = frappe.get_doc("User", self.email)
        
        
        # if api key is not set generate api key
        if not user.api_key:
            api_key = frappe.generate_hash(length=15)
            user.api_key = api_key
        
        if not user.api_secret:
            api_secret = frappe.generate_hash(length=15)
            user.api_secret = api_secret
        user.save(ignore_permissions=True)
        frappe.db.commit()
        token = base64.b64encode(
            (user.api_key+":"+api_secret).encode('ascii')).decode('ascii')
        frappe.local.response["token"] = token