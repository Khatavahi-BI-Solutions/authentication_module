
__version__ = '0.0.1'
import frappe
from typing import Dict
import json
from io import SEEK_END, SEEK_SET
import inspect
import datetime
import traceback
from werkzeug.exceptions import BadRequest, NotFound
class ApiEndpoint(object):
	"""Base class for all API endpoints."""

	def __init__(self, name):
		"""Initializes the API endpoint with the given name. The name will be used for analytics."""
		self.name = name
		self.message = {}
		self.data = {}
		self.error_code = {}
		self.code = "200"
		self.developer_message = {}
		self.exception = {}

	def run(self, *args, **kwargs):
		"""Entry-point for this endpoint. Parses API version from query string or body and calls
		the appropriate implementation, or the default implementation."""
		result = self.execute(lambda: self.default(*args, **kwargs))
		self.respond_with_code()
		return result

	def default(self):
		"""Default endpoint implementation if no API version is specified. Override this in derived
		classes."""
		return

	def query_string(self):
		"""Return a dictionary from the Query string."""
		return frappe.request.args

	def json_body(self):
		"""Returns a dictionary parsed from the body as JSON. If the body is not json, returns an
		empty dictionary."""
		body = frappe.request.data or '{}'
		try:
			result = json.loads(body)
		except ValueError:
			result = dict()

		return result

	def form_body(self):
		"""Returns a dictionary representing the form body parameters including files."""
		body = frappe.request.form.copy()

		# Add files directly as well. Iterating yields the file parameter names. Indexing with the
		# name yields a werkzeug.datastructures.FileStorage which we use as the value
		for f in frappe.request.files:
			body[f] = frappe.request.files[f]

		return body

	def respond_with_code(
			self) -> Dict[str, any]:
		"""Responds with the standard envelope and the given status code, data, error code,
		and message.
	   """
		
		has_request = frappe.request
		if has_request:
			frappe.local.response.http_status_code = self.code
		developer_message = developer_message or message

		if self.exception and not error_code:
			error_code = self.exception.__class__.__name__

		if error_code and not message:
			message = f"Server Error ({error_code})"

		if error_code:
			org_message = message
			message = frappe._(error_code)
			if message == error_code:
				message = org_message
		else:
			message = frappe._(message)

		
		frappe.local.response["message"] = self.message
		frappe.local.response["data"] = self.data
		frappe.local.response["error_code"] = self.error_code
		frappe.local.response["developer_message"] = self.developer_message
		return

	def execute(self, action):
		"""Executes an action and serializes frappe/web exceptions using the standard envelope."""
		try:
			return action()
		except frappe.ValidationError as e:
			traceback.print_exc()
			frappe.db.rollback()
			self.developer_message = frappe.get_traceback()
			self.code = 417
			self.exception = e
			return
		except NotFound as e:
			traceback.print_exc()
			frappe.db.rollback()
			self.developer_message = frappe.get_traceback()
			self.code = 404
			self.exception = e
			return
		except BadRequest as e:
			traceback.print_exc()
			frappe.db.rollback()
			self.code = 400
			self.developer_message = frappe.get_traceback()
			self.exception = e
			return
		except (frappe.PermissionError, PermissionError) as e:
			traceback.print_exc()
			frappe.db.rollback()
			self.code = 403
			self.developer_message = frappe.get_traceback()
			self.error_code="Forbidden"
			self.exception = e
			return
		except frappe.AuthenticationError as e:
			traceback.print_exc()
			frappe.db.rollback()
			self.code = 401
			self.developer_message = frappe.get_traceback()
			self.exception = e
			self.error_code="AuthenticationError"
			return
		except Exception as e:
			traceback.print_exc()
			frappe.db.rollback()
			self.code = 500
			self.developer_message = frappe.get_traceback()
			self.exception = e
			return

	def file_size_in_bytes(self, f):
		f.seek(0, SEEK_END)
		size = f.tell()
		f.seek(0, SEEK_SET)
		return size

	def validate_date_format(self, dates, date_format="%Y-%m-%d"):
		try:
			for date in dates:
				datetime.datetime.strptime(date, date_format)
			return True
		except ValueError:
			return False

	def validate_required_parameters(self, params, required_parameter_names, alternative_parameters=None):
		"""Checks that all keys defined in 'required_parameter_names' exist in 'params', and that
		one of the parameter names in each tuple in 'alternative_parameters' exists in 'params'.
		* params: The incoming parameters from body or query string as a dictionary
		* required_parameter_names: A list of required parameter names
		* alternative_parameters: A list of tuples, each defining the names of alternative parameter
		names (that is, if one of the names in the tuple is defined, the requirement is met)"""
		def check_tuple_parameters(param_tuple):
			for p in param_tuple:
				if p in params and params[p] is not None:
					return True
			return False

		alternative_parameters = alternative_parameters if alternative_parameters else []

		missing_parameters = [p for p in required_parameter_names if
							  p not in params or params[p] is None]

		missing_alt_parameters = [p for p in alternative_parameters if
								  not check_tuple_parameters(p)]

		if missing_alt_parameters or missing_parameters:
			message = ''
			if missing_parameters:
				message += 'Required parameters are missing: {}. '.format(
					', '.join(missing_parameters))

			if missing_alt_parameters:
				tuples = [' | '.join(x)
						  for x in [p for p in missing_alt_parameters]]
				message += 'Specify at least one of the following: {}'.format(
					', '.join(tuples))
			self.code = 400
			self.error_code = 'ArgumentNotFound'
			self.message = message
			return False

		return True

	def validate_required_parameters_has_values(self, params, required_parameters):
		missing_values = []
		for p in required_parameters:
			v = params.get(p)
			if v in ['0', '0.0', 0, 0.0]:
				continue

			if not v:
				missing_values.append(p)
		if missing_values:
			self.code = 400
			self.error_code = 'ValuesNotFound'
			self.message = f"These arguments {missing_values} values can't be empty"
			return False
		return True

	def validate_input_type(self, input_params: dict, input_type: tuple, check_digit=False):
		wrong_type_values = []
		for k, v in input_params.items():
			if v:
				if not isinstance(v, input_type):
					wrong_type_values.append(k)
				if str in input_type and check_digit and isinstance(v, str):
					try:
						float(v)
					except ValueError:
						wrong_type_values.append(k)
		if wrong_type_values:
			self.code = 400
			self.error_code = 'BadRequest'
			self.message = f"{wrong_type_values} have wrong input type"
			return False
		return True

	def validate_positive_value(self, input_params: dict):
		negative_value = []
		for k, v in input_params.items():
			if v:
				if float(v) < 0:
					negative_value.append(k)
		if negative_value:
			self.code = 400
			self.error_code = 'BadRequest'
			self.message = f"{negative_value} value shouldn't be negative"
			return False
		return True

	