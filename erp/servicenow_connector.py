"""
ServiceNow REST API Connector

This module handles all communication with ServiceNow:
- Creating incidents
- Monitoring ticket status
- Closing tickets
- Updating tickets with context
"""

import requests
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import config.settings as settings

logger = logging.getLogger(__name__)


class ServiceNowConnector:
    """
    Connects to ServiceNow API and performs operations.
    Uses Basic Auth (username/password) for simplicity.
    """
    
    def __init__(self, instance_url: Optional[str] = None, 
                 username: Optional[str] = None, 
                 password: Optional[str] = None):
        """
        Initialize ServiceNow connector.
        
        Args:
            instance_url: ServiceNow instance URL (defaults to env var)
            username: ServiceNow API user (defaults to env var)
            password: ServiceNow API password (defaults to env var)
        """
        
        self.instance_url = (instance_url or settings.SERVICENOW_URL).rstrip('/')
        self.username = username or settings.SERVICENOW_USER
        self.password = password or settings.SERVICENOW_PASS
        self.auth = (self.username, self.password)
        
        # Base headers for all requests
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        logger.info(f"✅ ServiceNow Connector initialized: {self.instance_url}")
        self._test_connection()
    
    def _test_connection(self):
        """Test connection to ServiceNow"""
        try:
            url = f"{self.instance_url}/api/now/table/incident?sysparm_limit=1"
            response = requests.get(url, auth=self.auth, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                logger.info("✅ ServiceNow connection successful")
            else:
                logger.warning(f"⚠️ ServiceNow connection test failed: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ ServiceNow connection error: {e}")
    
    # ═════════════════════════════════════════════════════════════
    # INCIDENT OPERATIONS
    # ═════════════════════════════════════════════════════════════
    
    def create_incident(self, 
                       short_description: str,
                       description: str,
                       priority: int = 3,
                       urgency: int = 2,
                       impact: int = 2,
                       assignment_group: str = "Accounts Payable",
                       category: str = "Finance",
                       **custom_fields) -> Dict[str, Any]:
        """
        Create a ServiceNow incident.
        
        Args:
            short_description: One-line title
            description: Full description with context
            priority: 1 (Critical) to 5 (Low)
            urgency: 1 (High) to 3 (Low)
            impact: 1 (High) to 3 (Low)
            assignment_group: Which team handles it
            category: Incident category
            **custom_fields: Additional custom fields
        
        Returns:
            {
                "success": True/False,
                "incident_id": "sys_id",
                "incident_number": "INC0010052",
                "url": "https://instance.service-now.com/incident.do?sys_id=...",
                "error": "error message if failed"
            }
        """
        
        try:
            logger.info(f"[ServiceNow] Creating incident: {short_description}")
            
            # Build payload
            payload = {
                "short_description": short_description,
                "description": description,
                "priority": str(priority),
                "urgency": str(urgency),
                "impact": str(impact),
                "assignment_group": assignment_group,
                "category": category,
                "state": "1",  # New
                "contact_type": "self_service"
            }
            
            # Add any custom fields (prefixed with u_)
            payload.update(custom_fields)
            
            logger.debug(f"Payload: {payload}")
            
            # Make API call
            url = f"{self.instance_url}/api/now/table/incident"
            response = requests.post(
                url,
                auth=self.auth,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            # Handle response
            if response.status_code in [200, 201]:
                result = response.json().get("result", {})
                incident_id = result.get("sys_id")
                incident_number = result.get("number")
                
                logger.info(f"✅ Incident created: {incident_number} (ID: {incident_id})")
                
                return {
                    "success": True,
                    "incident_id": incident_id,
                    "incident_number": incident_number,
                    "url": f"{self.instance_url}/incident.do?sys_id={incident_id}",
                    "data": result
                }
            else:
                error_msg = response.text
                logger.error(f"❌ Incident creation failed: {error_msg}")
                
                return {
                    "success": False,
                    "error": error_msg,
                    "status_code": response.status_code
                }
        
        except Exception as e:
            logger.error(f"❌ Exception in create_incident: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_incident_status(self, incident_id: str) -> Dict[str, Any]:
        """
        Get incident status from ServiceNow.
        
        Args:
            incident_id: sys_id of incident
        
        Returns:
            {
                "success": True/False,
                "number": "INC0010052",
                "state": "1",  # 1=New, 2=In Progress, 7=Closed
                "state_label": "New",
                "error": "error message if failed"
            }
        """
        
        try:
            logger.info(f"[ServiceNow] Checking status: {incident_id}")
            
            url = f"{self.instance_url}/api/now/table/incident/{incident_id}"
            response = requests.get(
                url,
                auth=self.auth,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json().get("result", {})
                
                state_labels = {
                    "1": "New",
                    "2": "In Progress",
                    "3": "On Hold",
                    "4": "Resolved",
                    "5": "Closed",
                    "6": "Cancelled",
                    "7": "Closed"
                }
                
                state = result.get("state", "1")
                
                return {
                    "success": True,
                    "number": result.get("number"),
                    "state": state,
                    "state_label": state_labels.get(state, "Unknown"),
                    "assignment_group": result.get("assignment_group"),
                    "assigned_to": result.get("assigned_to"),
                    "updated_at": result.get("sys_updated_on")
                }
            else:
                return {
                    "success": False,
                    "error": response.text
                }
        
        except Exception as e:
            logger.error(f"❌ Exception in get_incident_status: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def update_incident(self, 
                       incident_id: str,
                       updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing incident.
        
        Args:
            incident_id: sys_id of incident
            updates: Dict of fields to update
        
        Returns:
            {"success": True/False, "error": "..."}
        """
        
        try:
            logger.info(f"[ServiceNow] Updating incident: {incident_id}")
            
            url = f"{self.instance_url}/api/now/table/incident/{incident_id}"
            response = requests.patch(
                url,
                auth=self.auth,
                headers=self.headers,
                json=updates,
                timeout=30
            )
            
            if response.status_code in [200, 204]:
                logger.info(f"✅ Incident updated: {incident_id}")
                return {"success": True}
            else:
                logger.error(f"❌ Update failed: {response.text}")
                return {
                    "success": False,
                    "error": response.text
                }
        
        except Exception as e:
            logger.error(f"❌ Exception in update_incident: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def close_incident(self,
                      incident_id: str,
                      close_notes: str = "Resolved by AI Exception System",
                      state: str = "7") -> Dict[str, Any]:
        """
        Close a ServiceNow incident.
        
        Args:
            incident_id: sys_id of incident
            close_notes: Why is it being closed?
            state: "7" for Closed, "4" for Resolved
        
        Returns:
            {"success": True/False}
        """
        
        try:
            logger.info(f"[ServiceNow] Closing incident: {incident_id}")
            
            payload = {
                "state": state,
                "close_notes": close_notes,
                "closed_at": datetime.now().isoformat()
            }
            
            result = self.update_incident(incident_id, payload)
            return result
        
        except Exception as e:
            logger.error(f"❌ Exception in close_incident: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # ═════════════════════════════════════════════════════════════
    # CHANGE REQUEST OPERATIONS
    # ═════════════════════════════════════════════════════════════
    
    def create_change_request(self,
                            short_description: str,
                            description: str,
                            change_type: str = "normal",
                            assignment_group: str = "Procurement",
                            **custom_fields) -> Dict[str, Any]:
        """
        Create a ServiceNow change request (for high-value exceptions).
        
        Args:
            short_description: Title
            description: Full details
            change_type: "normal", "standard", or "emergency"
            assignment_group: Which team
            **custom_fields: Custom fields
        
        Returns:
            {
                "success": True/False,
                "change_request_id": "sys_id",
                "change_request_number": "CHG0010052",
                "error": "..."
            }
        """
        
        try:
            logger.info(f"[ServiceNow] Creating change request: {short_description}")
            
            payload = {
                "short_description": short_description,
                "description": description,
                "type": change_type,
                "assignment_group": assignment_group,
                "urgency": "2",
                "impact": "2",
                "priority": "3"
            }
            
            payload.update(custom_fields)
            
            url = f"{self.instance_url}/api/now/table/change_request"
            response = requests.post(
                url,
                auth=self.auth,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                result = response.json().get("result", {})
                change_id = result.get("sys_id")
                change_number = result.get("number")
                
                logger.info(f"✅ Change request created: {change_number}")
                
                return {
                    "success": True,
                    "change_request_id": change_id,
                    "change_request_number": change_number,
                    "url": f"{self.instance_url}/change_request.do?sys_id={change_id}",
                    "data": result
                }
            else:
                return {
                    "success": False,
                    "error": response.text
                }
        
        except Exception as e:
            logger.error(f"❌ Exception in create_change_request: {e}")
            return {
                "success": False,
                "error": str(e)
            }