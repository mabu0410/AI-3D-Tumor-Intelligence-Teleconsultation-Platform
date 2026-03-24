"use client";
import { useState } from 'react';
import PatientDashboard from '@/components/PatientDashboard';

export default function SchedulingPage() {
  const [patientId, setPatientId] = useState("");
  const [active, setActive] = useState(false);

  return (
    <div className="animate-fade-in" style={{ maxWidth: 1200, margin: '0 auto', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <header style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: 32, fontWeight: 800, margin: '0 0 8px', color: '#f8fafc' }}>
          📅 Module 7: Patient Scheduling
        </h1>
        <p style={{ color: '#94a3b8', fontSize: 15, margin: 0 }}>
          AI-driven appointment intervals, risk-based follow-ups, and SMS/Push notifications.
        </p>
      </header>

      {!active ? (
        <div style={{ background: '#0f172a', borderRadius: 16, padding: 32, border: '1px solid #1e293b', maxWidth: 600 }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, color: '#f8fafc', margin: '0 0 16px' }}>
            Open Patient Dashboard
          </h3>
          <div style={{ display: 'flex', gap: 12 }}>
            <input 
              type="text" 
              placeholder="Enter Patient ID (UUID)"
              value={patientId}
              onChange={e => setPatientId(e.target.value)}
              style={{
                flex: 1, padding: '12px 16px', background: '#1e293b', 
                border: '1px solid #334155', borderRadius: 8,
                color: '#f8fafc', fontSize: 14, outline: 'none'
              }}
            />
            <button 
              onClick={() => setActive(true)}
              disabled={!patientId}
              style={{
                padding: '0 24px', background: '#ec4899',
                color: '#fff', borderRadius: 8, border: 'none', fontWeight: 600,
                cursor: !patientId ? 'not-allowed' : 'pointer',
                opacity: !patientId ? 0.5 : 1
              }}
            >
              View Profile
            </button>
          </div>
          
          <div style={{ marginTop: 24, padding: 16, background: '#1e293b', borderRadius: 8, fontSize: 13, color: '#94a3b8', borderLeft: '3px solid #6366f1' }}>
            <strong>Auto-Scheduling Rules:</strong><br/>
            🔴 High Risk = 1-month interval<br/>
            🟡 Medium Risk = 3-month interval<br/>
            🟢 Low Risk = 12-month interval
          </div>
        </div>
      ) : (
        <div className="animate-fade-in">
           <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16 }}>
             <button onClick={() => setActive(false)} style={{ background: 'transparent', border: '1px solid #334155', color: '#94a3b8', padding: '6px 16px', borderRadius: 8, cursor: 'pointer' }}>
               ← Back to Search
             </button>
          </div>
          <PatientDashboard patientId={patientId} />
        </div>
      )}
    </div>
  );
}
