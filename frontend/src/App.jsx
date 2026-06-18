import React, { useState, useEffect } from 'react';

const API_URL = 'http://localhost:8000/api';

function App() {
  const [activeTab, setActiveTab] = useState('submit');
  const [formData, setFormData] = useState({ name: '', amount: 150, reason: '' });
  const [agentResponse, setAgentResponse] = useState(null);
  const [queue, setQueue] = useState([]);
  const [auditLog, setAuditLog] = useState([]);

  useEffect(() => {
    if (activeTab === 'queue') fetchQueue();
    if (activeTab === 'audit') fetchAuditLog();
  }, [activeTab]);

  const fetchQueue = async () => {
    try {
      const res = await fetch(`${API_URL}/queue`);
      const data = await res.json();
      setQueue(data);
    } catch (e) { console.error(e); }
  };

  const fetchAuditLog = async () => {
    try {
      const res = await fetch(`${API_URL}/audit`);
      const data = await res.json();
      setAuditLog(data);
    } catch (e) { console.error(e); }
  };

  const submitExpense = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_URL}/expense`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          employee_name: formData.name,
          expense_amount: parseFloat(formData.amount),
          expense_reason: formData.reason
        })
      });
      const data = await res.json();
      setAgentResponse(data);
    } catch (e) {
      console.error(e);
      setAgentResponse({ state: 'error', reason: 'Failed to connect to backend' });
    }
  };

  const handleAction = async (id, action) => {
    await fetch(`${API_URL}/queue/${id}/${action}`, { method: 'POST' });
    fetchQueue();
  };

  return (
    <div className="container">
      <div className="header">
        <h1>🛡️ Secure Expense Approval Agent</h1>
        <p>Google ADK Powered Autonomous Agent with Human-in-the-Loop Controls</p>
      </div>

      <div className="tabs">
        <button className={`tab ${activeTab === 'submit' ? 'active' : ''}`} onClick={() => setActiveTab('submit')}>📤 Submit Expense</button>
        <button className={`tab ${activeTab === 'queue' ? 'active' : ''}`} onClick={() => setActiveTab('queue')}>📋 Review Queue</button>
        <button className={`tab ${activeTab === 'audit' ? 'active' : ''}`} onClick={() => setActiveTab('audit')}>🧾 Audit Log</button>
      </div>

      {activeTab === 'submit' && (
        <div className="glass-card">
          <form onSubmit={submitExpense}>
            <div className="form-group">
              <label>Employee Name</label>
              <input type="text" value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} required placeholder="e.g. Alice" />
            </div>
            <div className="form-group">
              <label>Expense Amount ($)</label>
              <input type="number" step="0.01" value={formData.amount} onChange={e => setFormData({...formData, amount: e.target.value})} required />
            </div>
            <div className="form-group">
              <label>Expense Reason</label>
              <textarea value={formData.reason} onChange={e => setFormData({...formData, reason: e.target.value})} required rows="3" placeholder="e.g. Office supplies..."></textarea>
            </div>
            <button type="submit" className="primary">Submit to AI Agent</button>
          </form>

          {agentResponse && (
            <div className="queue-item" style={{ marginTop: '2rem' }}>
              <div className="queue-header">
                <h3>Agent Response</h3>
                <span className={`badge ${agentResponse.state}`}>{agentResponse.state}</span>
              </div>
              <p>{agentResponse.reason}</p>
              {agentResponse.queue && <p><strong>Routed To:</strong> {agentResponse.queue.toUpperCase()} Queue</p>}
            </div>
          )}
        </div>
      )}

      {activeTab === 'queue' && (
        <div className="glass-card">
          <h2>Pending Approvals</h2>
          <br/>
          {queue.length === 0 ? <p>No expenses pending review! 🎉</p> : queue.map(item => (
            <div className="queue-item" key={item.id || item.expense_id}>
              <div className="queue-header">
                <h3>{item.employee_name} - ${item.expense_amount}</h3>
                <span className="badge pending">{item.queue} Queue</span>
              </div>
              <p><strong>Reason:</strong> {item.expense_reason}</p>
              <p><strong>Flag:</strong> {item.review_reason}</p>
              <div className="queue-actions">
                <button className="success" onClick={() => handleAction(item.id || item.expense_id, 'approve')}>✅ Approve</button>
                <button className="danger" onClick={() => handleAction(item.id || item.expense_id, 'reject')}>❌ Reject</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'audit' && (
        <div className="glass-card">
          <h2>Audit Log</h2>
          <br/>
          <table>
            <thead>
              <tr>
                <th>Action</th>
                <th>Employee</th>
                <th>Amount</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              {auditLog.map((log, i) => {
                const exp = log.details?.expense || log.details || {};
                return (
                  <tr key={i}>
                    <td><span className={`badge ${log.action.includes('REJECT') ? 'rejected' : log.action.includes('APPROVE') ? 'approved' : 'pending'}`}>{log.action}</span></td>
                    <td>{exp.employee_name || 'N/A'}</td>
                    <td>{exp.expense_amount ? `$${exp.expense_amount}` : 'N/A'}</td>
                    <td>{log.details?.reason || exp.expense_reason || 'N/A'}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default App;
