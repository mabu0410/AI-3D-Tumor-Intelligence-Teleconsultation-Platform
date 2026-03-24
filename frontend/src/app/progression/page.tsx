"use client";
import { useState } from 'react';
import ProgressionChart from '@/components/ProgressionChart';

export default function ProgressionPage() {
  const [patientId, setPatientId] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleRun = async () => {
    if (!patientId) return;
    setLoading(true);
    setStatus("Running Time-Series Forecast (BiLSTM + Transformer)...");
    
    try {
      // Trigger prediction sync
      const res = await fetch(`/api/v1/prediction/run-sync/${patientId}`, { method: 'POST' });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to forecast progression");
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
          📈 Module 5: Progression Prediction
        </h1>
        <p style={{ color: '#94a3b8', fontSize: 15, margin: 0 }}>
          Temporal forecasting of tumor volume and malignancy risk over 3-6 months.
        </p>
      </header>

      <div style={{ background: '#0f172a', borderRadius: 16, padding: 32, border: '1px solid #1e293b', marginBottom: 32 }}>
        <h3 style={{ fontSize: 16, fontWeight: 600, color: '#f8fafc', margin: '0 0 16px' }}>
          Select Patient
        </h3>
        <div style={{ display: 'flex', gap: 12 }}>
          <input 
            type="text" 
            placeholder="Enter Patient ID (requires ≥ 2 historical scans)"
            value={patientId}
            onChange={e => setPatientId(e.target.value)}
            style={{
              flex: 1, padding: '12px 16px', background: '#1e293b', 
              border: '1px solid #334155', borderRadius: 8,
              color: '#f8fafc', fontSize: 14, outline: 'none'
            }}
          />
          <button 
            onClick={handleRun}
            disabled={loading || !patientId}
            style={{
              padding: '0 24px', background: loading ? '#334155' : '#f59e0b',
              color: '#fff', borderRadius: 8, border: 'none', fontWeight: 600,
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            {loading ? 'Forecasting...' : 'Run Prediction'}
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
          <ProgressionChart 
            patientId={result.patient_id}
            current={result.current}
            prediction3m={result.prediction_3m}
            prediction6m={result.prediction_6m}
            invasionSpeed={result.invasion_speed}
            invasionProbs={result.invasion_probabilities}
          />
        </div>
      )}
    </div>
  );
}
