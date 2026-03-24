"use client";
import { useState } from 'react';
import ConsultationRoom from '@/components/ConsultationRoom';

export default function TelemedicinePage() {
  const [consultationId, setId] = useState("");
  const [userId, setUserId] = useState("dr_smith");
  const [role, setRole] = useState<"specialist" | "doctor" | "viewer">("specialist");
  const [active, setActive] = useState(false);

  return (
    <div className="animate-fade-in" style={{ maxWidth: 1200, margin: '0 auto', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <header style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: 32, fontWeight: 800, margin: '0 0 8px', color: '#f8fafc' }}>
          🤝 Module 6: Teleconsultation
        </h1>
        <p style={{ color: '#94a3b8', fontSize: 15, margin: 0 }}>
          Real-time collaborative 3D annotation and diagnostic review room.
        </p>
      </header>

      {!active ? (
        <div style={{ background: '#0f172a', borderRadius: 16, padding: 32, border: '1px solid #1e293b', maxWidth: 600 }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, color: '#f8fafc', margin: '0 0 16px' }}>
            Join Consultation Room
          </h3>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16, marginBottom: 24 }}>
            <div>
              <label style={{ display: 'block', fontSize: 12, color: '#94a3b8', marginBottom: 6 }}>Consultation ID</label>
              <input 
                type="text" 
                placeholder="UUID"
                value={consultationId}
                onChange={e => setId(e.target.value)}
                style={{
                  width: '100%', padding: '12px 16px', background: '#1e293b', 
                  border: '1px solid #334155', borderRadius: 8,
                  color: '#f8fafc', fontSize: 14, outline: 'none'
                }}
              />
            </div>
            
            <div style={{ display: 'flex', gap: 16 }}>
              <div style={{ flex: 1 }}>
                <label style={{ display: 'block', fontSize: 12, color: '#94a3b8', marginBottom: 6 }}>Username</label>
                <input 
                  type="text" 
                  value={userId}
                  onChange={e => setUserId(e.target.value)}
                  style={{
                    width: '100%', padding: '12px 16px', background: '#1e293b', 
                    border: '1px solid #334155', borderRadius: 8,
                    color: '#f8fafc', fontSize: 14, outline: 'none'
                  }}
                />
              </div>
              <div style={{ flex: 1 }}>
                <label style={{ display: 'block', fontSize: 12, color: '#94a3b8', marginBottom: 6 }}>Role</label>
                <select 
                  value={role}
                  onChange={e => setRole(e.target.value as any)}
                  style={{
                    width: '100%', padding: '12px 16px', background: '#1e293b', 
                    border: '1px solid #334155', borderRadius: 8,
                    color: '#f8fafc', fontSize: 14, outline: 'none', appearance: 'none'
                  }}
                >
                  <option value="specialist">Specialist ✍️</option>
                  <option value="doctor">Referring Doctor 🩺</option>
                  <option value="viewer">Viewer 👀</option>
                </select>
              </div>
            </div>
          </div>

          <button 
            onClick={() => setActive(true)}
            disabled={!consultationId || !userId}
            style={{
              width: '100%', padding: '14px 24px', background: '#10b981',
              color: '#fff', borderRadius: 8, border: 'none', fontWeight: 600,
              cursor: (!consultationId || !userId) ? 'not-allowed' : 'pointer',
              opacity: (!consultationId || !userId) ? 0.5 : 1
            }}
          >
            Join Live Room
          </button>
        </div>
      ) : (
        <div className="animate-fade-in" style={{ flex: 1, minHeight: 0 }}>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16 }}>
             <button onClick={() => setActive(false)} style={{ background: 'transparent', border: '1px solid #334155', color: '#94a3b8', padding: '6px 16px', borderRadius: 8, cursor: 'pointer' }}>
               Leave Room
             </button>
          </div>
          <ConsultationRoom 
            consultationId={consultationId}
            currentUserId={userId}
            currentUserRole={role}
          />
        </div>
      )}
    </div>
  );
}
