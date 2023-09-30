from datetime import datetime
import base64
import frappe
from authentication_module.api import ApiEndpoint

@frappe.whitelist()
def endpoint():
    return Logout().run()


class Logout(ApiEndpoint):
    def __init__(self):
        super(Logout, self).__init__("VerifyEmailOTP")

    def default(self, *args, **kwargs):        
        self.logout()
        
        return "Success"

    def logout(self):
        user = frappe.get_doc("User", frappe.session.user)
        user.api_key = ""
        user.api_secret = ""
        user.save(ignore_permissions=True)
        frappe.db.commit()