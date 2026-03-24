"use client";

import Link from 'next/link';

const MODULE_CARDS = [
  { id: 1, title: 'Segmentation 3D', icon: '🧠', desc: 'Upload DICOM, run AI inference, extract tumor mask.', path: '/segmentation', color: '#6366f1' },
  { id: 2, title: 'Reconstruction', icon: '🧊', desc: 'Marching Cubes 3D mesh generator and viewer.', path: '/reconstruction', color: '#06b6d4' },
  { id: 3, title: 'Feature Extraction', icon: '📐', desc: 'Radiomics, gradient entropy, fractal dimension.', path: '/features', color: '#8b5cf6' },
  { id: 4, title: 'Classification', icon: '🔬', desc: 'Ensemble 3D ResNet + XGBoost Benign/Malignant.', path: '/classification', color: '#ef4444' },
  { id: 5, title: 'Progression', icon: '📈', desc: 'Time-series volume forecast & growth speed.', path: '/progression', color: '#f59e0b' },
  { id: 6, title: 'Teleconsultation', icon: '🤝', desc: 'Real-time 3D web-socket annotation room.', path: '/telemedicine', color: '#10b981' },
  { id: 7, title: 'Scheduling', icon: '📅', desc: 'Auto-appointment generation and SMS triggers.', path: '/scheduling', color: '#ec4899' },
];

export default function Home() {
  return (
    <div className="animate-fade-in" style={{ maxWidth: 1200, margin: '0 auto' }}>
      <header style={{ marginBottom: 40 }}>
        <h1 style={{ fontSize: 36, fontWeight: 800, margin: '0 0 8px', letterSpacing: '-0.03em', color: '#f8fafc' }}>
          Platform Overview
        </h1>
        <p style={{ color: '#94a3b8', fontSize: 16, margin: 0 }}>
          Central command center for the 7-module AI Tumor Intelligence lifecycle.
        </p>
      </header>

      {/* Quick Stats Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 20, marginBottom: 40 }}>
        {[
          { label: 'Total Cases Processed', val: '1,284', grow: '+12%' },
          { label: 'High Risk Detections', val: '315', grow: '+4%' },
          { label: 'Active Consultations', val: '12', grow: 'Live' },
          { label: 'System Accuracy (AUC)', val: '0.942', grow: 'Optimal' },
        ].map((stat, i) => (
          <div key={i} style={{
            background: '#0f172a', borderRadius: 16, padding: 24,
            border: '1px solid #1e293b', boxShadow: '0 10px 30px -10px rgba(0,0,0,0.5)'
          }}>
            <div style={{ fontSize: 13, color: '#94a3b8', fontWeight: 600, marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              {stat.label}
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 12 }}>
              <span style={{ fontSize: 32, fontWeight: 800, color: '#f8fafc', letterSpacing: '-0.03em' }}>{stat.val}</span>
              <span style={{ fontSize: 12, fontWeight: 700, color: '#10b981', background: '#064e3b', padding: '2px 8px', borderRadius: 10 }}>
                {stat.grow}
              </span>
            </div>
          </div>
        ))}
      </div>

      <h2 style={{ fontSize: 20, fontWeight: 700, color: '#f8fafc', marginBottom: 20, borderBottom: '1px solid #1e293b', paddingBottom: 12 }}>
        Module Quick Access
      </h2>

      {/* Modules Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 20 }}>
        {MODULE_CARDS.map((m) => (
          <Link key={m.id} href={m.path} style={{ textDecoration: 'none' }}>
            <div style={{
              background: '#0f172a', borderRadius: 16, padding: '24px',
              border: '1px solid #1e293b',
              transition: 'all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)',
              cursor: 'pointer', height: '100%',
              display: 'flex', flexDirection: 'column',
              position: 'relative', overflow: 'hidden',
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.transform = 'translateY(-4px)';
              e.currentTarget.style.borderColor = m.color;
              e.currentTarget.style.boxShadow = `0 12px 24px -10px ${m.color}40`;
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.borderColor = '#1e293b';
              e.currentTarget.style.boxShadow = 'none';
            }}>
              {/* Highlight bar top */}
              <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 4, background: m.color, opacity: 0.8 }} />
              
              <div style={{ fontSize: 36, marginBottom: 16 }}>{m.icon}</div>
              <h3 style={{ fontSize: 16, fontWeight: 700, color: '#f8fafc', margin: '0 0 8px' }}>
                Module {m.id}: {m.title}
              </h3>
              <p style={{ fontSize: 13, color: '#94a3b8', margin: 0, lineHeight: 1.6, flex: 1 }}>
                {m.desc}
              </p>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
