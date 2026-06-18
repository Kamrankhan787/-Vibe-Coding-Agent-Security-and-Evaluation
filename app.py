import streamlit as st
import json
import os
import pandas as pd
from agent import ExpenseAgent, ExpenseRequest
from approval_queue import ApprovalQueue, QUEUE_FILE, AUDIT_LOG_FILE

# Configuration
st.set_page_config(page_title="Secure Expense Agent", page_icon="🛡️", layout="wide")

# Initialize AI Backend
@st.cache_resource
def get_agent():
    return ExpenseAgent()

@st.cache_resource
def get_queue_manager():
    return ApprovalQueue()

agent = get_agent()
queue_manager = get_queue_manager()

st.title("🛡️ Secure Expense Approval Agent")
st.markdown("An AI-driven expense system utilizing Google ADK logic, strict prompt injection filtering, and a Human-in-the-Loop workflow.")

tab1, tab2, tab3 = st.tabs(["📤 Submit Expense", "📋 Review Queue", "🧾 Audit Log"])

# --- TAB 1: SUBMIT EXPENSE ---
with tab1:
    st.header("Submit New Expense")
    
    with st.form("expense_form"):
        col1, col2 = st.columns(2)
        with col1:
            emp_name = st.text_input("Employee Name", placeholder="e.g. Alice")
            emp_amount = st.number_input("Expense Amount ($)", min_value=0.0, step=10.0, value=150.0)
        with col2:
            emp_reason = st.text_area("Expense Reason / Description", placeholder="e.g. Office supplies...")
            
        submitted = st.form_submit_button("Submit to AI Agent")
        
        if submitted:
            if not emp_name or not emp_reason:
                st.error("Please fill out all fields.")
            else:
                request = ExpenseRequest(employee_name=emp_name, expense_amount=emp_amount, expense_reason=emp_reason)
                
                with st.spinner("Security Middleware and Agent are analyzing..."):
                    result_json = agent.process_expense(request)
                    result = json.loads(result_json)
                    
                st.subheader("Agent Response:")
                state = result.get("state")
                
                if state == "approved":
                    st.success(f"✅ **APPROVED:** {result.get('reason')}")
                elif state == "pending":
                    st.warning(f"⏳ **PENDING ({result.get('queue', '').upper()} QUEUE):** {result.get('reason')}")
                else:
                    st.error(f"🚨 **REJECTED:** {result.get('reason')}")
                    
                st.json(result)

# --- TAB 2: REVIEW QUEUE ---
with tab2:
    st.header("Human-in-the-Loop Queue")
    
    try:
        if os.path.exists(QUEUE_FILE):
            with open(QUEUE_FILE, 'r') as f:
                queue = json.load(f)
        else:
            queue = []
    except Exception:
        queue = []
        
    if not queue:
        st.info("No expenses pending review! 🎉")
    else:
        st.warning(f"You have {len(queue)} expenses awaiting manual review.")
        
        for idx, item in enumerate(queue):
            queue_type = item.get('queue', 'unknown').upper()
            
            with st.expander(f"Pending {queue_type} Review: {item.get('employee_name')} - ${item.get('expense_amount'):.2f}", expanded=True):
                st.write(f"**Reason:** {item.get('expense_reason')}")
                st.write(f"**Flagged by Agent:** {item.get('review_reason')}")
                st.caption(f"ID: `{item.get('id', 'unknown')}` | Submitted: `{item.get('submitted_at', 'unknown')}`")
                
                col1, col2, _ = st.columns([1, 1, 4])
                with col1:
                    if st.button("✅ Approve", key=f"app_{idx}"):
                        item['state'] = 'approved'
                        queue_manager.log_audit("MANUAL_APPROVED", {"expense_id": item.get("id"), "details": item})
                        queue.pop(idx)
                        with open(QUEUE_FILE, 'w') as f:
                            json.dump(queue, f, indent=4)
                        st.rerun()
                with col2:
                    if st.button("❌ Reject", key=f"rej_{idx}"):
                        item['state'] = 'rejected'
                        queue_manager.log_audit("MANUAL_REJECTED", {"expense_id": item.get("id"), "details": item})
                        queue.pop(idx)
                        with open(QUEUE_FILE, 'w') as f:
                            json.dump(queue, f, indent=4)
                        st.rerun()

# --- TAB 3: AUDIT LOG ---
with tab3:
    st.header("Immutable Audit Log")
    col_a, col_b = st.columns([1, 4])
    with col_a:
        if st.button("Refresh Logs"):
            st.rerun()
        
    try:
        if os.path.exists(AUDIT_LOG_FILE):
            with open(AUDIT_LOG_FILE, 'r') as f:
                logs = json.load(f)
            if logs:
                # Flatten the 'details' column for a nicer table
                flattened_logs = []
                for l in reversed(logs): # Show newest first
                    entry = {
                        "Timestamp": l.get("timestamp", ""),
                        "Action": l.get("action", "")
                    }
                    details = l.get("details", {})
                    # Add expense specific details
                    expense = details.get("expense", details) # sometimes it's nested
                    if isinstance(expense, dict):
                        entry["Employee"] = expense.get("employee_name", "N/A")
                        amount = expense.get("expense_amount", 0.0)
                        entry["Amount"] = f"${amount:.2f}" if amount else "N/A"
                        entry["Reason"] = details.get("reason", expense.get("expense_reason", "N/A"))
                    flattened_logs.append(entry)
                
                df = pd.DataFrame(flattened_logs)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("Log is empty.")
        else:
            st.info("No audit log found.")
    except Exception as e:
        st.error(f"Could not load logs: {e}")
