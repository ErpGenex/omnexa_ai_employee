app_name = "omnexa_ai_employee"
app_title = "ErpGenEx — AI Employee"
app_publisher = "ErpGenEx"
app_description = "Autonomous AI employee across all ERPGENEX business activities"
app_email = "dev@erpgenex.com"
app_license = "mit"

required_apps = ["omnexa_core"]

app_include_js = [
	"/assets/omnexa_ai_employee/js/ai_employee_dashboard.js",
]

after_install = "omnexa_ai_employee.install.after_install"
after_migrate = "omnexa_ai_employee.install.after_migrate"

fixtures = [
	{"dt": "Role", "filters": [["name", "in", ["AI Employee User"]]]},
]
