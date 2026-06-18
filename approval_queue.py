import json
import os
from datetime import datetime
from typing import Dict, Any

AUDIT_LOG_FILE = "audit_log.json"
QUEUE_FILE = "pending_queue.json"

class ApprovalQueue:
    """
    Manages the human-in-the-loop workflow and maintains immutable audit logs.
    Handles 'pending', 'approved', and 'rejected' states.
    """
    def __init__(self):
        self._ensure_file(AUDIT_LOG_FILE, [])
        self._ensure_file(QUEUE_FILE, [])

    def _ensure_file(self, filename: str, default_content: Any):
        if not os.path.exists(filename):
            with open(filename, 'w') as f:
                json.dump(default_content, f, indent=4)

    def log_audit(self, action: str, details: Dict[str, Any]):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details
        }
        with open(AUDIT_LOG_FILE, 'r+') as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []
            
            logs.append(log_entry)
            f.seek(0)
            f.truncate()
            json.dump(logs, f, indent=4)

    def add_to_queue(self, expense: Dict[str, Any], reason: str, queue_type: str):
        """
        Adds an expense to the manual review queue for human-in-the-loop processing.
        queue_type should be 'manager' or 'executive'
        """
        expense['state'] = 'pending'
        expense['queue'] = queue_type
        expense['review_reason'] = reason
        expense['submitted_at'] = datetime.now().isoformat()
        
        with open(QUEUE_FILE, 'r+') as f:
            try:
                queue = json.load(f)
            except json.JSONDecodeError:
                queue = []
                
            queue.append(expense)
            f.seek(0)
            f.truncate()
            json.dump(queue, f, indent=4)
        
        self.log_audit(f"ADDED_TO_QUEUE_{queue_type.upper()}", {"expense": expense, "reason": reason})

    def process_queue_interactive(self):
        """Interactive interface for reviewing pending queue items."""
        with open(QUEUE_FILE, 'r') as f:
            try:
                queue = json.load(f)
            except json.JSONDecodeError:
                queue = []
            
        if not queue:
            print("No expenses pending review.")
            return

        remaining_queue = []
        print(f"Found {len(queue)} expenses pending review.")
        
        for expense in queue:
            print("\n" + "="*50)
            print(f"PENDING {expense.get('queue', 'unknown').upper()} REVIEW:")
            print(f"Employee: {expense.get('employee_name')}")
            print(f"Amount:   ${expense.get('expense_amount'):.2f}")
            print(f"Reason:   {expense.get('expense_reason')}")
            print(f"Flag:     {expense.get('review_reason')}")
            print(f"State:    {expense.get('state')}")
            print("="*50)
            
            decision = input("Approve this expense? (y/n/skip): ").strip().lower()
            if decision == 'y':
                expense['state'] = 'approved'
                self.log_audit("MANUAL_APPROVED", {"expense_id": expense.get("id"), "details": expense})
                print(f"-> Expense marked as {expense['state']}.")
            elif decision == 'n':
                expense['state'] = 'rejected'
                self.log_audit("MANUAL_REJECTED", {"expense_id": expense.get("id"), "details": expense})
                print(f"-> Expense marked as {expense['state']}.")
            else:
                remaining_queue.append(expense)
                print("-> Skipped. Kept in pending state.")

        # Save remaining pending items back to queue
        with open(QUEUE_FILE, 'w') as f:
            json.dump(remaining_queue, f, indent=4)
        
        print("\nQueue processing complete.")
