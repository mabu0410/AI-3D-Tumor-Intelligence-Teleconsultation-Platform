"use client";
import { useState } from 'react';
import ReconstructionPanel from '@/components/ReconstructionPanel';

export default function ReconstructionPage() {
  const [caseId, setCaseId] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleRun = async () => {
    if (!caseId) return;
    setLoading(true);
    setStatus("Generating 3D Mesh... (Marching Cubes)");
    
    try {
      // Trigger mesh generation (sync for demo purposes, normally async)
      const res = await fetch(`/api/v1/reconstruction/run-sync/${caseId}`, { method: 'POST' });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to generate mesh");
      }
      
      const data = await res.json();
      setResult(data);
      setStatus(null);
    } catch (e: any) {
      setStatus(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="animate-fade-in" style={{ maxWidth: 1200, margin: '0 auto', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <header style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: 32, fontWeight: 800, margin: '0 0 8px', color: '#f8fafc' }}>
          🧊 Module 2: 3D Reconstruction
        </h1>
        <p style={{ color: '#94a3b8', fontSize: 15, margin: 0 }}>
          Marching Cubes mesh generation and geometric feature extraction.
        </p>
      </header>

      {!result ? (
        <div style={{ background: '#0f172a', borderRadius: 16, padding: 32, border: '1px solid #1e293b', maxWidth: 600 }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, color: '#f8fafc', margin: '0 0 16px' }}>
            Load Tumor Mesh
          </h3>
          <div style={{ display: 'flex', gap: 12 }}>
            <input 
              type="text" 
              placeholder="Enter Case ID (must be segmented first)"
              value={caseId}
              onChange={e => setCaseId(e.target.value)}
              style={{
                flex: 1, padding: '12px 16px', background: '#1e293b', 
                border: '1px solid #334155', borderRadius: 8,
                color: '#f8fafc', fontSize: 14, outline: 'none'
              }}
            />
            <button 
              onClick={handleRun}
              disabled={loading || !caseId}
              style={{
                padding: '0 24px', background: loading ? '#334155' : '#06b6d4',
                color: '#fff', borderRadius: 8, border: 'none', fontWeight: 600,
                cursor: loading ? 'not-allowed' : 'pointer'
              }}
            >
              {loading ? 'Processing...' : 'Generate 3D'}
            </button>
          </div>
          
          {status && (
            <div style={{ marginTop: 20, color: status.includes("Failed") ? "#ef4444" : "#06b6d4", fontSize: 14 }}>
              {status}
            </div>
          )}
        </div>
      ) : (
        <div className="animate-fade-in" style={{ flex: 1, minHeight: 0 }}>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16 }}>
             <button onClick={() => setResult(null)} style={{ background: 'transparent', border: '1px solid #334155', color: '#94a3b8', padding: '6px 16px', borderRadius: 8, cursor: 'pointer' }}>
               Close Viewer
             </button>
          </div>
          <ReconstructionPanel 
            caseId={caseId}
            features={result.features}
            meshUrl={`/api/v1/reconstruction/mesh/${caseId}/glb`}
          />
        </div>
      )}
    </div>
  );
}
