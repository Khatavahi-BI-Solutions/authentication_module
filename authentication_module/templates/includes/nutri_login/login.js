// login.js
// don't remove this line (used in test)

window.disable_signup = {{ disable_signup and "true" or "false" }};
// window.disable_signup = "false"
window.login = {};

window.verify = {};

login.bind_events = function () {
	$(window).on("hashchange", function () {
		login.route();
	});

	$(".form-login").on("submit", function (event) {
		event.preventDefault();
		var _login = {};
		_login.usr = frappe.utils.xss_sanitise(($("#login_email").val() || "").trim());
		frappe.call({
			method: "authentication_module.apis.request_email_otp.endpoint",
			type: "POST",
			args: {
				'email': _login.usr
			},
			success: function(r) {
				if (!r.exc) {
					_login.token = r.data.token
					$("#token-field").val(_login.token);
					$(".for-login").toggle(false);
					$(".for-signup").toggle(true);		
				}
			},
		});
		// login.set_status('{{ _("Otp Sended...") }}');
		// frappe.msgprint(_login.usr + "......." + _login.token);
		return false;
	});

	$(".form-otp").on("submit", function (event) {
		event.preventDefault();
		var _verify = {};
		_verify.token = frappe.utils.xss_sanitise(($("#token-field").val() || "").trim());
		_verify.otp = $("#otp-field").val()
		frappe.call({
			method: "authentication_module.apis.verify_email_otp.endpoint",
			type: "POST",
			args: {
				'token': _verify.token,
				'otp': _verify.otp
			},
			success: function(r) {
				if (r.message == "Invalid OTP"){
					frappe.msgprint(r.message)
				}
				else{
					location.reload();
				}
			},
		});
		login.set_status('{{ _("Verifing...") }}');
		// frappe.msgprint(_verify.token + "......." + _verify.otp);
		return false;
	});

	login.set_status = function (message) {
		$('section:visible .btn-primary').text(message)
	}
}

login.route = function () {
	var route = window.location.hash.slice(1);
	if (!route) route = "login";
	login[route]();
}

frappe.ready(function () {

	login.bind_events();

	if (!window.location.hash) {
		window.location.hash = "#login";
	} else {
		$(window).trigger("hashchange");
	}

	$(".form-signup, .form-forgot").removeClass("hide");
	$(document).trigger('login_rendered');
});