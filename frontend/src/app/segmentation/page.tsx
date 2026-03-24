"use client";
import { useState } from 'react';

export default function SegmentationPage() {
  const [caseId, setCaseId] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleRun = async () => {
    if (!caseId) return;
    setLoading(true);
    setStatus("Running AI Segmentation... (This may take a minute)");
    
    try {
      // 1. Trigger
      const res = await fetch(`/api/v1/segmentation/run/${caseId}`, { method: 'POST' });
      if (!res.ok) throw new Error("Failed to start");
      
      // 2. Poll status
      const interval = setInterval(async () => {
        const pollRes = await fetch(`/api/v1/segmentation/task-status/${caseId}`);
        const data = await pollRes.json();
        
        if (data.status === "completed") {
          clearInterval(interval);
          setStatus(null);
          setResult(data);
          setLoading(false);
        } else if (data.status === "error") {
          clearInterval(interval);
          setStatus("Error during segmentation");
          setLoading(false);
        }
      }, 3000);
    } catch (e: any) {
      setStatus(e.message);
      setLoading(false);
    }
  };

  return (
    <div className="animate-fade-in" style={{ maxWidth: 800, margin: '0 auto' }}>
      <header style={{ marginBottom: 40 }}>
        <h1 style={{ fontSize: 32, fontWeight: 800, margin: '0 0 8px', color: '#f8fafc' }}>
          🧠 Module 1: 3D Segmentation
        </h1>
        <p style={{ color: '#94a3b8', fontSize: 15, margin: 0 }}>
          Volumetric tumor extraction using MONAI U-Net / SegResNet.
        </p>
      </header>

      <div style={{ background: '#0f172a', borderRadius: 16, padding: 32, border: '1px solid #1e293b' }}>
        <h3 style={{ fontSize: 16, fontWeight: 600, color: '#f8fafc', margin: '0 0 16px' }}>
          Run Inference
        </h3>
        
        <div style={{ display: 'flex', gap: 12, marginBottom: 24 }}>
          <input 
            type="text" 
            placeholder="Enter Case ID (UUID)"
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
              padding: '0 24px', background: loading ? '#334155' : '#6366f1',
              color: '#fff', borderRadius: 8, border: 'none', fontWeight: 600,
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            {loading ? 'Processing...' : 'Run Segmentation'}
          </button>
        </div>

        {status && (
          <div style={{ padding: 16, background: '#1e293b', borderRadius: 8, color: '#94a3b8', fontSize: 13, marginBottom: 24, display: 'flex', alignItems: 'center', gap: 12 }}>
            {loading && <div style={{ width: 16, height: 16, border: '2px solid #6366f1', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />}
            {status}
          </div>
        )}

        {result && (
          <div className="animate-fade-in" style={{ borderTop: '1px solid #1e293b', paddingTop: 24 }}>
            <h4 style={{ color: '#22c55e', margin: '0 0 16px', display: 'flex', alignItems: 'center', gap: 8 }}>
              ✅ Segmentation Complete
            </h4>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16 }}>
              <div style={{ background: '#1e293b', padding: 16, borderRadius: 12 }}>
                <div style={{ fontSize: 11, color: '#64748b', textTransform: 'uppercase' }}>Dice Score</div>
                <div style={{ fontSize: 24, fontWeight: 700, color: '#f8fafc' }}>{result.dice_score?.toFixed(4) ?? 'N/A'}</div>
              </div>
              <div style={{ background: '#1e293b', padding: 16, borderRadius: 12 }}>
                <div style={{ fontSize: 11, color: '#64748b', textTransform: 'uppercase' }}>IoU Score</div>
                <div style={{ fontSize: 24, fontWeight: 700, color: '#f8fafc' }}>{result.iou_score?.toFixed(4) ?? 'N/A'}</div>
              </div>
              <div style={{ background: '#1e293b', padding: 16, borderRadius: 12 }}>
                <div style={{ fontSize: 11, color: '#64748b', textTransform: 'uppercase' }}>Hausdorff 95</div>
                <div style={{ fontSize: 24, fontWeight: 700, color: '#f8fafc' }}>{result.hausdorff_distance_95?.toFixed(2) ?? 'N/A'} mm</div>
              </div>
            </div>
          </div>
        )}
      </div>
      <style>{`@keyframes spin { 100% { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
