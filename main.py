from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import uuid
import os
from adk_agent import adk_workflow
from approval_queue import QUEUE_FILE, AUDIT_LOG_FILE, ApprovalQueue

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

queue_manager = ApprovalQueue()

class ExpenseRequest(BaseModel):
    employee_name: str
    expense_amount: float
    expense_reason: str

@app.post("/api/expense")
async def process_expense(req: ExpenseRequest):
    expense_id = f"EX-{str(uuid.uuid4())[:8]}"
    result_text = adk_workflow.execute(req.employee_name, req.expense_amount, req.expense_reason, expense_id)
    try:
        return json.loads(result_text)
    except Exception:
        return {"state": "error", "reason": "Failed to parse agent response"}

@app.get("/api/queue")
async def get_queue():
    if os.path.exists(QUEUE_FILE):
        with open(QUEUE_FILE, 'r') as f:
            return json.load(f)
    return []

@app.post("/api/queue/{expense_id}/approve")
async def approve_expense(expense_id: str):
    if not os.path.exists(QUEUE_FILE):
        return {"success": False}
        
    with open(QUEUE_FILE, 'r') as f:
        queue = json.load(f)
        
    for i, item in enumerate(queue):
        item_id = item.get("id") or item.get("expense_id")
        if item_id == expense_id:
            item["state"] = "approved"
            queue_manager.log_audit("MANUAL_APPROVED", {"expense_id": expense_id, "details": item})
            queue.pop(i)
            with open(QUEUE_FILE, 'w') as f:
                json.dump(queue, f, indent=4)
            return {"success": True}
    return {"success": False}

@app.post("/api/queue/{expense_id}/reject")
async def reject_expense(expense_id: str):
    if not os.path.exists(QUEUE_FILE):
        return {"success": False}
        
    with open(QUEUE_FILE, 'r') as f:
        queue = json.load(f)
        
    for i, item in enumerate(queue):
        item_id = item.get("id") or item.get("expense_id")
        if item_id == expense_id:
            item["state"] = "rejected"
            queue_manager.log_audit("MANUAL_REJECTED", {"expense_id": expense_id, "details": item})
            queue.pop(i)
            with open(QUEUE_FILE, 'w') as f:
                json.dump(queue, f, indent=4)
            return {"success": True}
    return {"success": False}

@app.get("/api/audit")
async def get_audit():
    if os.path.exists(AUDIT_LOG_FILE):
        with open(AUDIT_LOG_FILE, 'r') as f:
            logs = json.load(f)
            return list(reversed(logs)) # newest first
    return []
