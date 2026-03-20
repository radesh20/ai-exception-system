"""
ACTION AGENT - Intelligent ServiceNow Ticket Creator

This agent:
1. Analyzes exception context
2. Decides what type of ticket to create
3. Creates the ticket in ServiceNow
4. Monitors status
5. Auto-closes when resolved
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ActionType(str, Enum):
    CREATE_INCIDENT = "create_incident"
    CREATE_CHANGE_REQUEST = "create_change_request"
    ESCALATE_TO_MANAGER = "escalate_to_manager"


class ActionAgent:
    """
    Intelligent action executor that creates ServiceNow tickets
    based on exception context.
    """
    
    def __init__(self, store, servicenow_connector):
        """
        Initialize action agent.
        
        Args:
            store: Data store (JSON/DB)
            servicenow_connector: ServiceNow API client
        """
        self.store = store
        self.servicenow = servicenow_connector
        logger.info("✅ ActionAgent initialized")
    
    def execute(self, exception: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point: Analyze exception and create ServiceNow ticket.
        
        Args:
            exception: Exception model/dict with full context
        
        Returns:
            {
                "status": "success" / "failed",
                "ticket_id": "...",
                "ticket_number": "INC0010052",
                "ticket_type": "incident" / "change_request",
                "url": "https://instance.service-now.com/...",
                "error": "..." (if failed)
            }
        """
        
        case_id = exception.get('context', {}).get('case_id', 'Unknown') if isinstance(exception, dict) else getattr(exception, 'context', {}).get('case_id', 'Unknown')
        logger.info(f"[ActionAgent] Processing: {case_id}")
        
        # ─────────────────────────────────────────────────────────────
        # STEP 1: DECIDE WHAT ACTION TO TAKE
        # ─────────────────────────────────────────────────────────────
        
        action_decision = self._decide_action(exception)
        action_type = action_decision.get("action_type")
        
        logger.info(f"[ActionAgent] Decided: {action_type}")
        
        # ─────────────────────────────────────────────────────────────
        # STEP 2: EXECUTE THE ACTION
        # ─────────────────────────────────────────────────────────────
        
        if action_type == ActionType.CREATE_INCIDENT.value:
            return self._create_incident(exception, action_decision)
        
        elif action_type == ActionType.CREATE_CHANGE_REQUEST.value:
            return self._create_change_request(exception, action_decision)
        
        elif action_type == ActionType.ESCALATE_TO_MANAGER.value:
            return self._escalate_to_manager(exception, action_decision)
        
        else:
            return {
                "status": "failed",
                "error": f"Unknown action: {action_type}"
            }
    
    def _decide_action(self, exception: Dict) -> Dict[str, Any]:
        """
        Decide what action to take based on exception context.
        
        Rules:
        - Amount > $100K → Change Request (needs approval)
        - Amount > $50K → Incident (high priority)
        - Compliance flag → Escalate to manager
        - Otherwise → Regular incident
        """
        
        try:
            # Handle both dict and object
            if isinstance(exception, dict):
                context = exception.get("context", {})
                classification = exception.get("classification", {})
            else:
                context = getattr(exception, "context", {})
                classification = getattr(exception, "classification", {})
            
            amount = context.get("financial_exposure", 0) if isinstance(context, dict) else getattr(context, "financial_exposure", 0)
            compliance_flag = context.get("compliance_flag", False) if isinstance(context, dict) else getattr(context, "compliance_flag", False)
            severity = classification.get("priority", 3) if isinstance(classification, dict) else getattr(classification, "priority", 3)
            exception_type = context.get("exception_type", "Unknown") if isinstance(context, dict) else getattr(context, "exception_type", "Unknown")
            
            # Rule 1: High financial exposure → Change Request
            if amount > 100000:
                logger.info(f"[ActionAgent] High amount (${amount:,.2f}) → Change Request")
                return {
                    "action_type": ActionType.CREATE_CHANGE_REQUEST.value,
                    "priority": 2,
                    "assignment_group": "Procurement",
                    "change_type": "standard",
                    "reason": f"High financial exposure: ${amount:,.2f}"
                }
            
            # Rule 2: Compliance flag → Escalate
            elif compliance_flag:
                logger.info("[ActionAgent] Compliance flag detected → Escalate")
                return {
                    "action_type": ActionType.ESCALATE_TO_MANAGER.value,
                    "priority": 1,
                    "reason": "Compliance risk detected"
                }
            
            # Rule 3: Medium amount → High priority incident
            elif amount > 50000:
                logger.info(f"[ActionAgent] Medium-high amount (${amount:,.2f}) → Incident")
                return {
                    "action_type": ActionType.CREATE_INCIDENT.value,
                    "priority": 2,
                    "urgency": 2,
                    "assignment_group": "Accounts Payable",
                    "reason": f"Financial exposure: ${amount:,.2f}"
                }
            
            # Rule 4: Default → Standard incident
            else:
                logger.info("[ActionAgent] Default → Incident")
                return {
                    "action_type": ActionType.CREATE_INCIDENT.value,
                    "priority": 3,
                    "urgency": 2,
                    "assignment_group": "Accounts Payable",
                    "reason": "Standard P2P exception"
                }
        
        except Exception as e:
            logger.error(f"[ActionAgent] Decision error: {e}")
            return {
                "action_type": ActionType.CREATE_INCIDENT.value,
                "priority": 3,
                "assignment_group": "Accounts Payable"
            }
    
    def _create_incident(self, 
                        exception: Dict,
                        decision: Dict) -> Dict[str, Any]:
        """
        Create ServiceNow incident with full context.
        """
        
        logger.info("[ActionAgent] Creating incident...")
        
        try:
            # Handle both dict and object
            if isinstance(exception, dict):
                context = exception.get("context", {})
                classification = exception.get("classification", {})
                root_cause = exception.get("root_cause", {})
                exc_id = exception.get("id", "")
            else:
                context = getattr(exception, "context", {})
                classification = getattr(exception, "classification", {})
                root_cause = getattr(exception, "root_cause", {})
                exc_id = getattr(exception, "id", "")
            
            case_id = context.get("case_id", "Unknown") if isinstance(context, dict) else getattr(context, "case_id", "Unknown")
            exception_type = context.get("exception_type", "Exception") if isinstance(context, dict) else getattr(context, "exception_type", "Exception")
            vendor = context.get("vendor", "Unknown") if isinstance(context, dict) else getattr(context, "vendor", "Unknown")
            amount = context.get("financial_exposure", 0) if isinstance(context, dict) else getattr(context, "financial_exposure", 0)
            
            # ─────────────────────────────────────────────────────────
            # BUILD DETAILED DESCRIPTION
            # ─────────────────────────────────────────────────────────
            
            description = f"""
CASE DETAILS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Case ID: {case_id}
Exception Type: {exception_type}
Vendor: {vendor}
Financial Exposure: ${amount:,.2f}

AI ANALYSIS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Status: Auto-created by AI Exception System

Next Steps:
1. Review the exception details
2. Verify vendor information
3. Approve or reject the recommended action
            """
            
            # ─────────────────────────────────────────────────────────
            # CREATE INCIDENT
            # ─────────────────────────────────────────────────────────
            
            result = self.servicenow.create_incident(
                short_description=f"{exception_type} - {case_id}",
                description=description,
                priority=decision.get("priority", 3),
                urgency=decision.get("urgency", 2),
                assignment_group=decision.get("assignment_group", "Accounts Payable"),
                category="Finance"
            )
            
            if result.get("success"):
                logger.info(f"✅ Incident created: {result.get('incident_number')}")
                
                # ─────────────────────────────────────────────────────
                # SAVE EXECUTION RECORD
                # ─────────────────────────────────────────────────────
                
                try:
                    self.store.save_action_execution({
                        "exception_id": exc_id,
                        "case_id": case_id,
                        "action_type": "create_incident",
                        "servicenow_ticket_id": result.get("incident_id"),
                        "servicenow_ticket_number": result.get("incident_number"),
                        "status": "created",
                        "created_at": datetime.now().isoformat(),
                        "ticket_url": result.get("url")
                    })
                except Exception as e:
                    logger.warning(f"[ActionAgent] Could not save execution record: {e}")
                
                return {
                    "status": "success",
                    "ticket_id": result.get("incident_id"),
                    "ticket_number": result.get("incident_number"),
                    "ticket_type": "incident",
                    "url": result.get("url"),
                    "message": f"Incident {result.get('incident_number')} created successfully"
                }
            
            else:
                logger.error(f"❌ Incident creation failed: {result.get('error')}")
                return {
                    "status": "failed",
                    "error": result.get("error"),
                    "message": "Failed to create incident in ServiceNow"
                }
        
        except Exception as e:
            logger.error(f"❌ Exception in _create_incident: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def _create_change_request(self,
                              exception: Dict,
                              decision: Dict) -> Dict[str, Any]:
        """
        Create ServiceNow change request (for high-value exceptions).
        """
        
        logger.info("[ActionAgent] Creating change request...")
        
        try:
            if isinstance(exception, dict):
                context = exception.get("context", {})
                exc_id = exception.get("id", "")
            else:
                context = getattr(exception, "context", {})
                exc_id = getattr(exception, "id", "")
            
            case_id = context.get("case_id", "Unknown") if isinstance(context, dict) else getattr(context, "case_id", "Unknown")
            exception_type = context.get("exception_type", "Exception") if isinstance(context, dict) else getattr(context, "exception_type", "Exception")
            amount = context.get("financial_exposure", 0) if isinstance(context, dict) else getattr(context, "financial_exposure", 0)
            
            description = f"""
CHANGE REQUEST FOR HIGH-VALUE EXCEPTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Case ID: {case_id}
Type: {exception_type}
Amount: ${amount:,.2f}

This change requires management approval before execution.

Implementation Steps:
1. Review all supporting documentation
2. Verify amounts match invoice and PO
3. Obtain manager approval
4. Execute in SAP (if approved)
5. Update this ticket with confirmation

Deadline: ASAP
            """
            
            result = self.servicenow.create_change_request(
                short_description=f"CHG: {exception_type} - {case_id} (${amount:,.0f})",
                description=description,
                change_type="standard",
                assignment_group="Procurement"
            )
            
            if result.get("success"):
                logger.info(f"✅ Change request created: {result.get('change_request_number')}")
                
                try:
                    self.store.save_action_execution({
                        "exception_id": exc_id,
                        "case_id": case_id,
                        "action_type": "create_change_request",
                        "servicenow_ticket_id": result.get("change_request_id"),
                        "servicenow_ticket_number": result.get("change_request_number"),
                        "status": "created",
                        "created_at": datetime.now().isoformat(),
                        "ticket_url": result.get("url")
                    })
                except Exception as e:
                    logger.warning(f"[ActionAgent] Could not save execution record: {e}")
                
                return {
                    "status": "success",
                    "ticket_id": result.get("change_request_id"),
                    "ticket_number": result.get("change_request_number"),
                    "ticket_type": "change_request",
                    "url": result.get("url"),
                    "message": "Change request created (awaiting approval)"
                }
            
            else:
                return {
                    "status": "failed",
                    "error": result.get("error")
                }
        
        except Exception as e:
            logger.error(f"❌ Exception in _create_change_request: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def _escalate_to_manager(self,
                            exception: Dict,
                            decision: Dict) -> Dict[str, Any]:
        """
        Escalate to manager for review (for compliance/high-risk cases).
        """
        
        logger.info("[ActionAgent] Escalating to manager...")
        
        try:
            if isinstance(exception, dict):
                context = exception.get("context", {})
            else:
                context = getattr(exception, "context", {})
            
            case_id = context.get("case_id", "Unknown") if isinstance(context, dict) else getattr(context, "case_id", "Unknown")
            
            description = f"""
🚨 ESCALATED FOR MANAGER REVIEW

Case: {case_id}
Exception: {context.get('exception_type') if isinstance(context, dict) else getattr(context, 'exception_type')}
Amount: ${(context.get('financial_exposure', 0) if isinstance(context, dict) else getattr(context, 'financial_exposure', 0)):,.2f}

Reason for Escalation: {decision.get('reason', 'Requires manager approval')}

This exception has been flagged for senior management review.
            """
            
            # Create high-priority incident for manager
            result = self.servicenow.create_incident(
                short_description=f"🚨 MANAGER ESCALATION: {case_id}",
                description=description,
                priority=1,  # Critical
                urgency=1,   # Immediate
                assignment_group="Finance Management",
                category="P2P Exception"
            )
            
            if result.get("success"):
                logger.info(f"✅ Escalation ticket created: {result.get('incident_number')}")
                
                return {
                    "status": "escalated",
                    "ticket_id": result.get("incident_id"),
                    "ticket_number": result.get("incident_number"),
                    "url": result.get("url"),
                    "message": "Exception escalated to management"
                }
            
            else:
                return {
                    "status": "failed",
                    "error": result.get("error")
                }
        
        except Exception as e:
            logger.error(f"❌ Exception in _escalate_to_manager: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def monitor_and_close(self,
                         exception_id: str,
                         ticket_id: str) -> Dict[str, Any]:
        """
        Monitor ticket status and auto-close when resolved.
        """
        
        logger.info(f"[ActionAgent] Monitoring ticket: {ticket_id}")
        
        try:
            # Get ticket status
            status_result = self.servicenow.get_incident_status(ticket_id)
            
            if not status_result.get("success"):
                logger.warning(f"Could not get status: {status_result.get('error')}")
                return status_result
            
            state = status_result.get("state")
            state_label = status_result.get("state_label")
            
            logger.info(f"Ticket {ticket_id} state: {state_label}")
            
            # Check if resolved
            if state in ["4", "7"]:  # Resolved or Closed
                logger.info(f"✅ Ticket {ticket_id} resolved, closing...")
                
                # Close ticket in ServiceNow
                close_result = self.servicenow.close_incident(
                    ticket_id,
                    close_notes="Auto-closed by AI Exception System - exception resolved",
                    state="7"
                )
                
                if close_result.get("success"):
                    # Update our record
                    try:
                        self.store.update_action_execution(exception_id, {
                            "status": "closed",
                            "closed_at": datetime.now().isoformat()
                        })
                    except Exception as e:
                        logger.warning(f"Could not update action execution: {e}")
                    
                    return {
                        "status": "closed",
                        "ticket_id": ticket_id,
                        "message": "Ticket closed successfully"
                    }
            
            else:
                # Still in progress
                return {
                    "status": "in_progress",
                    "ticket_id": ticket_id,
                    "state": state_label,
                    "message": f"Ticket still being worked on"
                }
        
        except Exception as e:
            logger.error(f"❌ Exception in monitor_and_close: {e}")
            return {
                "status": "error",
                "error": str(e)
            }