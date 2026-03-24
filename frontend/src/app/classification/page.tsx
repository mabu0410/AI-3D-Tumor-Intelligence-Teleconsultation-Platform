"use client";
import { useState } from 'react';
import RiskScoreCard from '@/components/RiskScoreCard';

export default function ClassificationPage() {
  const [caseId, setCaseId] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleRun = async () => {
    if (!caseId) return;
    setLoading(true);
    setStatus("Running Ensemble Classification (3D CNN + XGBoost)...");
    
    try {
      // Trigger classification (sync demo)
      const res = await fetch(`/api/v1/classification/run-sync/${caseId}`, { method: 'POST' });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to run classification");
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
    <div className="animate-fade-in" style={{ maxWidth: 1000, margin: '0 auto' }}>
      <header style={{ marginBottom: 40 }}>
        <h1 style={{ fontSize: 32, fontWeight: 800, margin: '0 0 8px', color: '#f8fafc' }}>
          🔬 Module 4: Classification
        </h1>
        <p style={{ color: '#94a3b8', fontSize: 15, margin: 0 }}>
          Ensemble prediction (3D ResNet-18 + XGBoost) for Benign vs Malignant risk assessment.
        </p>
      </header>

      <div style={{ background: '#0f172a', borderRadius: 16, padding: 32, border: '1px solid #1e293b', marginBottom: 32 }}>
        <h3 style={{ fontSize: 16, fontWeight: 600, color: '#f8fafc', margin: '0 0 16px' }}>
          Analyze Tumor Malignancy
        </h3>
        <div style={{ display: 'flex', gap: 12 }}>
          <input 
            type="text" 
            placeholder="Enter Case ID (requires Features extracted)"
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
              padding: '0 24px', background: loading ? '#334155' : '#ef4444',
              color: '#fff', borderRadius: 8, border: 'none', fontWeight: 600,
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            {loading ? 'Analyzing...' : 'Run Classification'}
          </button>
        </div>
        
        {status && (
          <div style={{ marginTop: 20, color: status.includes("Fail") ? "#ef4444" : "#94a3b8", fontSize: 14 }}>
            {status}
          </div>
        )}
      </div>

      {result && (
        <div className="animate-fade-in">
          <RiskScoreCard 
            probabilityBenign={result.probabilities.benign}
            probabilityMalignant={result.probabilities.malignant}
            label={result.label}
            confidence={result.confidence}
            cnnWeight={0.6}
            xgbWeight={0.4}
            cnnPred={result.cnn_prediction}
            xgbPred={result.xgb_prediction}
          />
        </div>
      )}
    </div>
  );
}
