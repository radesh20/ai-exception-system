# Create this file to test connection

from erp.servicenow_connector import ServiceNowConnector
import config.settings as settings

# Initialize connector
sn = ServiceNowConnector(
    instance_url=settings.SERVICENOW_URL,
    username=settings.SERVICENOW_USER,
    password=settings.SERVICENOW_PASS
)

# Test: Create an incident
result = sn.create_incident(
    short_description="Test Incident from AI System",
    description="This is a test ticket created by the ActionAgent.",
    priority=3,
    urgency=2,
    assignment_group="Accounts Payable"
)

print("Result:", result)

if result.get("success"):
    print(f"✅ Success! Incident created: {result.get('incident_number')}")
    print(f"   URL: {result.get('url')}")
else:
    print(f"❌ Failed: {result.get('error')}")